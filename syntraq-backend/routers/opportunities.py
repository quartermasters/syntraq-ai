from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from database.connection import get_db
from models.opportunity import Opportunity
from services.sam_gov import SamGovService
from services.opportunity_processor import OpportunityProcessor
from pydantic import BaseModel

router = APIRouter()

class OpportunityResponse(BaseModel):
    id: int
    notice_id: str
    title: str
    description: str
    agency: str
    posted_date: datetime
    response_deadline: datetime
    relevance_score: Optional[float]
    ai_summary: Optional[str]
    user_decision: Optional[str]
    status: str
    
    class Config:
        from_attributes = True

class OpportunityFilter(BaseModel):
    status: Optional[str] = None
    agency: Optional[str] = None
    naics_code: Optional[str] = None
    min_relevance: Optional[float] = None
    decision: Optional[str] = None

@router.get("/", response_model=List[OpportunityResponse])
async def get_opportunities(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=100),
    status: Optional[str] = Query(None),
    min_relevance: Optional[float] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Opportunity).filter(Opportunity.is_active == True)
    
    if status:
        query = query.filter(Opportunity.status == status)
    if min_relevance:
        query = query.filter(Opportunity.relevance_score >= min_relevance)
    
    opportunities = query.order_by(Opportunity.posted_date.desc()).offset(skip).limit(limit).all()
    return opportunities

@router.get("/{opportunity_id}", response_model=OpportunityResponse)
async def get_opportunity(opportunity_id: int, db: Session = Depends(get_db)):
    opportunity = db.query(Opportunity).filter(Opportunity.id == opportunity_id).first()
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    return opportunity

@router.post("/sync-sam-gov")
async def sync_sam_gov_opportunities(
    days_back: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db)
):
    """Fetch new opportunities from SAM.gov API"""
    sam_service = SamGovService()
    processor = OpportunityProcessor(db)
    
    try:
        # Fetch opportunities from last N days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        opportunities = await sam_service.fetch_opportunities(start_date, end_date)
        
        new_count = 0
        updated_count = 0
        
        for opp_data in opportunities:
            result = await processor.process_opportunity(opp_data)
            if result["created"]:
                new_count += 1
            else:
                updated_count += 1
        
        return {
            "status": "success",
            "new_opportunities": new_count,
            "updated_opportunities": updated_count,
            "total_processed": len(opportunities)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")

@router.post("/{opportunity_id}/process-ai")
async def process_with_ai(opportunity_id: int, db: Session = Depends(get_db)):
    """Process opportunity with AI summarizer and relevance scoring"""
    opportunity = db.query(Opportunity).filter(Opportunity.id == opportunity_id).first()
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    processor = OpportunityProcessor(db)
    result = await processor.ai_process_opportunity(opportunity)
    
    return {
        "status": "success",
        "ai_summary": result["summary"],
        "relevance_score": result["relevance_score"],
        "confidence_score": result["confidence_score"]
    }

@router.get("/dashboard/stats")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get dashboard statistics for MVP"""
    total_opportunities = db.query(Opportunity).filter(Opportunity.is_active == True).count()
    new_opportunities = db.query(Opportunity).filter(
        Opportunity.status == "new",
        Opportunity.is_active == True
    ).count()
    high_relevance = db.query(Opportunity).filter(
        Opportunity.relevance_score >= 70,
        Opportunity.is_active == True
    ).count()
    decided_opportunities = db.query(Opportunity).filter(
        Opportunity.user_decision.isnot(None),
        Opportunity.is_active == True
    ).count()
    
    return {
        "total_opportunities": total_opportunities,
        "new_opportunities": new_opportunities,
        "high_relevance_opportunities": high_relevance,
        "decided_opportunities": decided_opportunities,
        "decision_rate": (decided_opportunities / total_opportunities * 100) if total_opportunities > 0 else 0
    }