from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, List, Optional

from database.connection import get_db
from models.opportunity import Opportunity
from services.ai_service import AIService

router = APIRouter()

class SummaryRequest(BaseModel):
    opportunity_id: int
    user_profile: Optional[Dict] = None

class SummaryResponse(BaseModel):
    opportunity_id: int
    executive_summary: str
    relevance_score: float
    confidence_score: float
    key_requirements: List[str]
    decision_factors: Dict[str, str]
    recommendations: Dict[str, str]
    processing_time: float

class BatchSummaryRequest(BaseModel):
    opportunity_ids: List[int]
    user_profile: Optional[Dict] = None

@router.post("/summarize", response_model=SummaryResponse)
async def generate_summary(
    request: SummaryRequest,
    db: Session = Depends(get_db)
):
    """Generate AI summary for a single opportunity"""
    opportunity = db.query(Opportunity).filter(Opportunity.id == request.opportunity_id).first()
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    ai_service = AIService()
    
    try:
        result = await ai_service.generate_executive_summary(
            opportunity=opportunity,
            user_profile=request.user_profile
        )
        
        # Update opportunity with AI results
        opportunity.ai_summary = result["executive_summary"]
        opportunity.relevance_score = result["relevance_score"]
        opportunity.confidence_score = result["confidence_score"]
        opportunity.key_requirements = result["key_requirements"]
        opportunity.decision_factors = result["decision_factors"]
        opportunity.status = "reviewed"
        
        db.commit()
        
        return SummaryResponse(**result, opportunity_id=request.opportunity_id)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI processing failed: {str(e)}")

@router.post("/batch-summarize")
async def batch_generate_summaries(
    request: BatchSummaryRequest,
    db: Session = Depends(get_db)
):
    """Generate AI summaries for multiple opportunities"""
    opportunities = db.query(Opportunity).filter(
        Opportunity.id.in_(request.opportunity_ids)
    ).all()
    
    if len(opportunities) != len(request.opportunity_ids):
        raise HTTPException(status_code=404, detail="Some opportunities not found")
    
    ai_service = AIService()
    results = []
    failed = []
    
    for opportunity in opportunities:
        try:
            result = await ai_service.generate_executive_summary(
                opportunity=opportunity,
                user_profile=request.user_profile
            )
            
            # Update opportunity
            opportunity.ai_summary = result["executive_summary"]
            opportunity.relevance_score = result["relevance_score"]
            opportunity.confidence_score = result["confidence_score"]
            opportunity.key_requirements = result["key_requirements"]
            opportunity.decision_factors = result["decision_factors"]
            opportunity.status = "reviewed"
            
            results.append({
                "opportunity_id": opportunity.id,
                "status": "success",
                "relevance_score": result["relevance_score"]
            })
            
        except Exception as e:
            failed.append({
                "opportunity_id": opportunity.id,
                "status": "failed",
                "error": str(e)
            })
    
    db.commit()
    
    return {
        "processed": len(results),
        "failed": len(failed),
        "results": results,
        "failures": failed
    }

@router.get("/relevance-trends")
async def get_relevance_trends(
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Get relevance score trends for analytics"""
    from datetime import datetime, timedelta
    
    start_date = datetime.now() - timedelta(days=days)
    
    opportunities = db.query(Opportunity).filter(
        Opportunity.created_at >= start_date,
        Opportunity.relevance_score.isnot(None)
    ).all()
    
    # Group by day and calculate average relevance
    daily_stats = {}
    for opp in opportunities:
        day_key = opp.created_at.date().isoformat()
        if day_key not in daily_stats:
            daily_stats[day_key] = {"scores": [], "count": 0}
        daily_stats[day_key]["scores"].append(opp.relevance_score)
        daily_stats[day_key]["count"] += 1
    
    # Calculate averages
    trends = []
    for day, stats in daily_stats.items():
        avg_score = sum(stats["scores"]) / len(stats["scores"])
        trends.append({
            "date": day,
            "average_relevance": round(avg_score, 2),
            "opportunity_count": stats["count"]
        })
    
    return {
        "period_days": days,
        "trends": sorted(trends, key=lambda x: x["date"])
    }

@router.post("/feedback")
async def submit_ai_feedback(
    opportunity_id: int,
    accuracy_score: float,
    feedback_notes: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Submit feedback on AI summary accuracy for learning"""
    opportunity = db.query(Opportunity).filter(Opportunity.id == opportunity_id).first()
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    # Store feedback for AI model improvement
    feedback_data = {
        "accuracy_score": accuracy_score,
        "feedback_notes": feedback_notes,
        "timestamp": datetime.now().isoformat(),
        "original_relevance": opportunity.relevance_score,
        "original_confidence": opportunity.confidence_score
    }
    
    # Add to opportunity's feedback history
    if not opportunity.decision_factors:
        opportunity.decision_factors = {}
    
    if "ai_feedback" not in opportunity.decision_factors:
        opportunity.decision_factors["ai_feedback"] = []
    
    opportunity.decision_factors["ai_feedback"].append(feedback_data)
    db.commit()
    
    return {"status": "success", "message": "Feedback recorded for AI improvement"}