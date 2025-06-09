from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from database.connection import get_db
from models.market_research import MarketAnalysis, CompetitorProfile, ContractAward
from services.market_intelligence import MarketIntelligenceService
from routers.users import get_current_user
from models.user import User
from pydantic import BaseModel

router = APIRouter()

class MarketAnalysisResponse(BaseModel):
    opportunity_id: int
    competition_level: str
    total_competitors: int
    barrier_to_entry: str
    pricing_pressure: str
    key_competitors: List[Dict]
    pricing_benchmarks: List[Dict]
    ai_insights: Dict
    confidence_score: float
    analysis_date: datetime
    
    class Config:
        from_attributes = True

class CompetitorResponse(BaseModel):
    id: int
    company_name: str
    size_standard: Optional[str]
    certifications: List[str]
    capabilities: List[str]
    past_performance_rating: Optional[float]
    annual_revenue: Optional[float]
    contract_vehicles: List[str]
    
    class Config:
        from_attributes = True

class ContractAwardResponse(BaseModel):
    id: int
    contract_number: str
    title: str
    agency: str
    base_value: float
    total_value: float
    contractor_name: str
    award_date: datetime
    naics_code: str
    
    class Config:
        from_attributes = True

@router.get("/opportunity/{opportunity_id}/analysis", response_model=MarketAnalysisResponse)
async def get_market_analysis(
    opportunity_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive market analysis for an opportunity"""
    
    service = MarketIntelligenceService(db)
    
    try:
        analysis = await service.analyze_opportunity_market(opportunity_id)
        
        # Convert to response format
        return MarketAnalysisResponse(
            opportunity_id=opportunity_id,
            competition_level=analysis.get('competition_level', 'medium'),
            total_competitors=analysis.get('total_competitors', 0),
            barrier_to_entry=analysis.get('barrier_to_entry', 'medium'),
            pricing_pressure=analysis.get('pricing_pressure', 'medium'),
            key_competitors=analysis.get('key_competitors', []),
            pricing_benchmarks=analysis.get('pricing_benchmarks', []),
            ai_insights=analysis.get('ai_analysis', {}),
            confidence_score=analysis.get('confidence_score', 75.0),
            analysis_date=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Market analysis failed: {str(e)}")
    finally:
        await service.close()

@router.get("/competitors", response_model=List[CompetitorResponse])
async def get_competitors(
    naics_code: Optional[str] = Query(None),
    size_standard: Optional[str] = Query(None),
    certification: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get competitor profiles with filtering"""
    
    query = db.query(CompetitorProfile).filter(CompetitorProfile.is_active == True)
    
    if naics_code:
        query = query.filter(CompetitorProfile.naics_codes.contains([naics_code]))
    
    if size_standard:
        query = query.filter(CompetitorProfile.size_standard == size_standard)
    
    if certification:
        query = query.filter(CompetitorProfile.certifications.contains([certification]))
    
    competitors = query.offset(skip).limit(limit).all()
    
    return [
        CompetitorResponse(
            id=comp.id,
            company_name=comp.company_name,
            size_standard=comp.size_standard,
            certifications=comp.certifications or [],
            capabilities=comp.capabilities or [],
            past_performance_rating=comp.past_performance_rating,
            annual_revenue=comp.annual_revenue,
            contract_vehicles=comp.contract_vehicles or []
        )
        for comp in competitors
    ]

@router.get("/competitor/{competitor_id}", response_model=CompetitorResponse)
async def get_competitor_detail(
    competitor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed competitor profile"""
    
    competitor = db.query(CompetitorProfile).filter(
        CompetitorProfile.id == competitor_id,
        CompetitorProfile.is_active == True
    ).first()
    
    if not competitor:
        raise HTTPException(status_code=404, detail="Competitor not found")
    
    return CompetitorResponse(
        id=competitor.id,
        company_name=competitor.company_name,
        size_standard=competitor.size_standard,
        certifications=competitor.certifications or [],
        capabilities=competitor.capabilities or [],
        past_performance_rating=competitor.past_performance_rating,
        annual_revenue=competitor.annual_revenue,
        contract_vehicles=competitor.contract_vehicles or []
    )

@router.get("/competitor/{competitor_id}/awards", response_model=List[ContractAwardResponse])
async def get_competitor_awards(
    competitor_id: int,
    years_back: int = Query(5, ge=1, le=10),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get contract awards for a competitor"""
    
    start_date = datetime.now() - timedelta(days=365 * years_back)
    
    awards = db.query(ContractAward).filter(
        ContractAward.contractor_id == competitor_id,
        ContractAward.award_date >= start_date
    ).order_by(ContractAward.award_date.desc()).all()
    
    return [
        ContractAwardResponse(
            id=award.id,
            contract_number=award.contract_number,
            title=award.title,
            agency=award.agency,
            base_value=award.base_value,
            total_value=award.total_value,
            contractor_name=award.contractor.company_name,
            award_date=award.award_date,
            naics_code=award.naics_code
        )
        for award in awards
    ]

@router.get("/historical-awards")
async def get_historical_awards(
    naics_code: Optional[str] = Query(None),
    agency: Optional[str] = Query(None),
    min_value: Optional[float] = Query(None),
    max_value: Optional[float] = Query(None),
    years_back: int = Query(3, ge=1, le=10),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get historical contract awards with filtering"""
    
    start_date = datetime.now() - timedelta(days=365 * years_back)
    
    query = db.query(ContractAward).filter(ContractAward.award_date >= start_date)
    
    if naics_code:
        query = query.filter(ContractAward.naics_code == naics_code)
    
    if agency:
        query = query.filter(ContractAward.agency.ilike(f"%{agency}%"))
    
    if min_value:
        query = query.filter(ContractAward.total_value >= min_value)
    
    if max_value:
        query = query.filter(ContractAward.total_value <= max_value)
    
    awards = query.order_by(ContractAward.award_date.desc()).offset(skip).limit(limit).all()
    
    return [
        {
            "id": award.id,
            "contract_number": award.contract_number,
            "title": award.title,
            "agency": award.agency,
            "contractor": award.contractor.company_name if award.contractor else "Unknown",
            "base_value": award.base_value,
            "total_value": award.total_value,
            "award_date": award.award_date.isoformat(),
            "naics_code": award.naics_code,
            "psc_code": award.psc_code,
            "set_aside": award.set_aside
        }
        for award in awards
    ]

@router.get("/pricing-intelligence")
async def get_pricing_intelligence(
    naics_code: Optional[str] = Query(None),
    psc_code: Optional[str] = Query(None),
    service_category: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get pricing intelligence and benchmarks"""
    
    # Get contract award pricing data
    query = db.query(ContractAward)
    
    if naics_code:
        query = query.filter(ContractAward.naics_code == naics_code)
    
    if psc_code:
        query = query.filter(ContractAward.psc_code == psc_code)
    
    awards = query.filter(
        ContractAward.total_value > 0,
        ContractAward.award_date >= datetime.now() - timedelta(days=365*3)
    ).limit(100).all()
    
    # Calculate pricing statistics
    values = [award.total_value for award in awards if award.total_value]
    
    if not values:
        return {
            "data_points": 0,
            "pricing_statistics": {},
            "market_benchmarks": []
        }
    
    values.sort()
    n = len(values)
    
    pricing_stats = {
        "average": sum(values) / n,
        "median": values[n//2] if n % 2 == 1 else (values[n//2-1] + values[n//2]) / 2,
        "min": min(values),
        "max": max(values),
        "percentile_25": values[int(n * 0.25)],
        "percentile_75": values[int(n * 0.75)],
        "std_deviation": (sum([(x - sum(values)/n)**2 for x in values]) / n) ** 0.5
    }
    
    # Market benchmarks by contract size
    benchmarks = []
    size_ranges = [
        (0, 100000, "Micro Purchase"),
        (100000, 500000, "Small Business"),
        (500000, 5000000, "Medium Contract"),
        (5000000, float('inf'), "Large Contract")
    ]
    
    for min_val, max_val, category in size_ranges:
        range_values = [v for v in values if min_val <= v < max_val]
        if range_values:
            benchmarks.append({
                "category": category,
                "count": len(range_values),
                "average_value": sum(range_values) / len(range_values),
                "value_range": f"${min_val:,.0f} - ${max_val:,.0f}" if max_val != float('inf') else f"${min_val:,.0f}+"
            })
    
    return {
        "data_points": len(values),
        "pricing_statistics": pricing_stats,
        "market_benchmarks": benchmarks,
        "recent_awards": [
            {
                "contractor": award.contractor.company_name if award.contractor else "Unknown",
                "value": award.total_value,
                "award_date": award.award_date.isoformat(),
                "agency": award.agency
            }
            for award in awards[:10]
        ]
    }

@router.get("/market-trends")
async def get_market_trends(
    naics_code: Optional[str] = Query(None),
    agency: Optional[str] = Query(None),
    months_back: int = Query(24, ge=6, le=60),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get market trends and analytics"""
    
    start_date = datetime.now() - timedelta(days=30 * months_back)
    
    query = db.query(ContractAward).filter(ContractAward.award_date >= start_date)
    
    if naics_code:
        query = query.filter(ContractAward.naics_code == naics_code)
    
    if agency:
        query = query.filter(ContractAward.agency.ilike(f"%{agency}%"))
    
    awards = query.all()
    
    # Group by month
    monthly_data = {}
    for award in awards:
        month_key = award.award_date.strftime("%Y-%m")
        if month_key not in monthly_data:
            monthly_data[month_key] = {
                "award_count": 0,
                "total_value": 0,
                "small_business_awards": 0,
                "average_value": 0
            }
        
        monthly_data[month_key]["award_count"] += 1
        monthly_data[month_key]["total_value"] += award.total_value or 0
        
        # Check if small business (simplified check)
        if award.set_aside and any(sb in award.set_aside.lower() for sb in ['small', '8(a)', 'wosb', 'hubzone']):
            monthly_data[month_key]["small_business_awards"] += 1
    
    # Calculate averages
    for month_data in monthly_data.values():
        if month_data["award_count"] > 0:
            month_data["average_value"] = month_data["total_value"] / month_data["award_count"]
    
    # Sort by month
    trends = []
    for month in sorted(monthly_data.keys()):
        data = monthly_data[month]
        trends.append({
            "month": month,
            "award_count": data["award_count"],
            "total_value": data["total_value"],
            "average_value": data["average_value"],
            "small_business_percentage": (data["small_business_awards"] / data["award_count"] * 100) if data["award_count"] > 0 else 0
        })
    
    return {
        "period_months": months_back,
        "trends": trends,
        "summary": {
            "total_awards": len(awards),
            "total_value": sum(award.total_value or 0 for award in awards),
            "average_monthly_awards": len(awards) / months_back if months_back > 0 else 0,
            "small_business_share": len([a for a in awards if a.set_aside and 'small' in a.set_aside.lower()]) / len(awards) * 100 if awards else 0
        }
    }

@router.post("/competitor/add")
async def add_competitor(
    company_name: str,
    duns_number: Optional[str] = None,
    size_standard: Optional[str] = None,
    certifications: List[str] = [],
    naics_codes: List[str] = [],
    capabilities: List[str] = [],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a new competitor profile"""
    
    # Check if competitor already exists
    existing = db.query(CompetitorProfile).filter(
        CompetitorProfile.company_name == company_name
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Competitor already exists")
    
    competitor = CompetitorProfile(
        company_name=company_name,
        duns_number=duns_number,
        size_standard=size_standard,
        certifications=certifications,
        naics_codes=naics_codes,
        capabilities=capabilities
    )
    
    db.add(competitor)
    db.commit()
    db.refresh(competitor)
    
    return {"status": "success", "competitor_id": competitor.id, "message": "Competitor added successfully"}