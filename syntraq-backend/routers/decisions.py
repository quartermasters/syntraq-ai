from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime

from database.connection import get_db
from models.opportunity import Opportunity

router = APIRouter()

class DecisionRequest(BaseModel):
    opportunity_id: int
    decision: str  # "go", "no-go", "bookmark", "validate"
    reason: Optional[str] = None
    priority: Optional[str] = "medium"  # "high", "medium", "low"
    assigned_to: Optional[str] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None

class DecisionResponse(BaseModel):
    opportunity_id: int
    decision: str
    reason: Optional[str]
    decision_date: datetime
    status: str
    
    class Config:
        from_attributes = True

class DecisionStats(BaseModel):
    total_decisions: int
    go_decisions: int
    no_go_decisions: int
    bookmark_decisions: int
    validate_decisions: int
    go_rate: float
    average_time_to_decision: Optional[float] = None

@router.post("/make-decision", response_model=DecisionResponse)
async def make_decision(
    request: DecisionRequest,
    db: Session = Depends(get_db)
):
    """Make a Go/No-Go decision on an opportunity"""
    opportunity = db.query(Opportunity).filter(Opportunity.id == request.opportunity_id).first()
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    # Validate decision type
    valid_decisions = ["go", "no-go", "bookmark", "validate"]
    if request.decision not in valid_decisions:
        raise HTTPException(status_code=400, detail=f"Invalid decision. Must be one of: {valid_decisions}")
    
    # Update opportunity with decision
    opportunity.user_decision = request.decision
    opportunity.decision_reason = request.reason
    opportunity.decision_date = datetime.utcnow()
    opportunity.priority = request.priority or "medium"
    opportunity.assigned_to = request.assigned_to
    opportunity.notes = request.notes
    
    # Handle tags
    if request.tags:
        opportunity.tags = request.tags
    
    # Update status based on decision
    if request.decision == "go":
        opportunity.status = "approved"
    elif request.decision == "no-go":
        opportunity.status = "rejected"
    elif request.decision == "bookmark":
        opportunity.status = "bookmarked"
    elif request.decision == "validate":
        opportunity.status = "needs_validation"
    
    db.commit()
    
    return DecisionResponse(
        opportunity_id=opportunity.id,
        decision=opportunity.user_decision,
        reason=opportunity.decision_reason,
        decision_date=opportunity.decision_date,
        status=opportunity.status
    )

@router.get("/bulk-decision")
async def bulk_decision(
    opportunity_ids: List[int],
    decision: str,
    reason: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Make the same decision on multiple opportunities"""
    valid_decisions = ["go", "no-go", "bookmark", "validate"]
    if decision not in valid_decisions:
        raise HTTPException(status_code=400, detail=f"Invalid decision. Must be one of: {valid_decisions}")
    
    opportunities = db.query(Opportunity).filter(
        Opportunity.id.in_(opportunity_ids),
        Opportunity.is_active == True
    ).all()
    
    if len(opportunities) != len(opportunity_ids):
        raise HTTPException(status_code=404, detail="Some opportunities not found")
    
    updated_count = 0
    for opportunity in opportunities:
        opportunity.user_decision = decision
        opportunity.decision_reason = reason
        opportunity.decision_date = datetime.utcnow()
        
        # Update status
        if decision == "go":
            opportunity.status = "approved"
        elif decision == "no-go":
            opportunity.status = "rejected"
        elif decision == "bookmark":
            opportunity.status = "bookmarked"
        elif decision == "validate":
            opportunity.status = "needs_validation"
        
        updated_count += 1
    
    db.commit()
    
    return {
        "status": "success",
        "updated_opportunities": updated_count,
        "decision": decision
    }

@router.get("/stats", response_model=DecisionStats)
async def get_decision_stats(
    days: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get decision statistics for analytics"""
    query = db.query(Opportunity).filter(
        Opportunity.user_decision.isnot(None),
        Opportunity.is_active == True
    )
    
    if days:
        from datetime import timedelta
        start_date = datetime.now() - timedelta(days=days)
        query = query.filter(Opportunity.decision_date >= start_date)
    
    opportunities = query.all()
    
    if not opportunities:
        return DecisionStats(
            total_decisions=0,
            go_decisions=0,
            no_go_decisions=0,
            bookmark_decisions=0,
            validate_decisions=0,
            go_rate=0.0
        )
    
    # Count decisions
    decisions = [opp.user_decision for opp in opportunities]
    go_count = decisions.count("go")
    no_go_count = decisions.count("no-go")
    bookmark_count = decisions.count("bookmark")
    validate_count = decisions.count("validate")
    total = len(decisions)
    
    # Calculate average time to decision (from posting to decision)
    decision_times = []
    for opp in opportunities:
        if opp.posted_date and opp.decision_date:
            time_diff = (opp.decision_date - opp.posted_date).total_seconds() / 3600  # hours
            decision_times.append(time_diff)
    
    avg_decision_time = sum(decision_times) / len(decision_times) if decision_times else None
    
    return DecisionStats(
        total_decisions=total,
        go_decisions=go_count,
        no_go_decisions=no_go_count,
        bookmark_decisions=bookmark_count,
        validate_decisions=validate_count,
        go_rate=round((go_count / total * 100), 2) if total > 0 else 0.0,
        average_time_to_decision=round(avg_decision_time, 2) if avg_decision_time else None
    )

@router.get("/recent")
async def get_recent_decisions(
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get recent decisions for dashboard"""
    opportunities = db.query(Opportunity).filter(
        Opportunity.user_decision.isnot(None),
        Opportunity.is_active == True
    ).order_by(Opportunity.decision_date.desc()).limit(limit).all()
    
    return [
        {
            "id": opp.id,
            "title": opp.title,
            "agency": opp.agency,
            "decision": opp.user_decision,
            "decision_date": opp.decision_date,
            "relevance_score": opp.relevance_score,
            "reason": opp.decision_reason
        }
        for opp in opportunities
    ]

@router.put("/{opportunity_id}/update-decision")
async def update_decision(
    opportunity_id: int,
    request: DecisionRequest,
    db: Session = Depends(get_db)
):
    """Update an existing decision"""
    opportunity = db.query(Opportunity).filter(Opportunity.id == opportunity_id).first()
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    if not opportunity.user_decision:
        raise HTTPException(status_code=400, detail="No existing decision to update")
    
    # Update decision fields
    opportunity.user_decision = request.decision
    opportunity.decision_reason = request.reason
    opportunity.priority = request.priority or opportunity.priority
    opportunity.assigned_to = request.assigned_to
    opportunity.notes = request.notes
    
    if request.tags:
        opportunity.tags = request.tags
    
    # Update status
    if request.decision == "go":
        opportunity.status = "approved"
    elif request.decision == "no-go":
        opportunity.status = "rejected"
    elif request.decision == "bookmark":
        opportunity.status = "bookmarked"
    elif request.decision == "validate":
        opportunity.status = "needs_validation"
    
    db.commit()
    
    return {"status": "success", "message": "Decision updated successfully"}