from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel

from database.connection import get_db
from models.proposals import (
    Proposal, ProposalVolume, ProposalSection, ProposalReview,
    ProposalSubmission, ProposalTemplate, ProposalLibrary,
    ProposalStatus, VolumeType, ComplianceStatus
)
from services.proposal_engine import ProposalManagementEngine
from routers.users import get_current_user
from models.user import User

router = APIRouter()

class ProposalCreateRequest(BaseModel):
    opportunity_id: int
    project_id: Optional[int] = None
    delivery_plan_id: Optional[int] = None

class SectionContentRequest(BaseModel):
    section_id: int
    context: Optional[Dict[str, Any]] = None

class ReviewRequest(BaseModel):
    proposal_id: int
    review_type: str
    sections_to_review: Optional[List[int]] = None

class ProposalResponse(BaseModel):
    id: int
    proposal_number: str
    proposal_title: str
    status: str
    submission_deadline: datetime
    overall_progress_percentage: float
    compliance_score: Optional[float]
    win_probability: Optional[float]
    
    class Config:
        from_attributes = True

class SectionResponse(BaseModel):
    id: int
    section_number: str
    section_title: str
    completion_percentage: float
    compliance_status: str
    word_count: int
    assigned_writer: Optional[int]
    
    class Config:
        from_attributes = True

@router.post("/proposals")
async def create_proposal(
    request: ProposalCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create new proposal from opportunity"""
    
    engine = ProposalManagementEngine(db)
    
    try:
        result = await engine.create_proposal_from_opportunity(
            current_user.id,
            request.opportunity_id,
            request.project_id,
            request.delivery_plan_id
        )
        
        return {
            "status": "success",
            **result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Proposal creation failed: {str(e)}")

@router.get("/proposals", response_model=List[ProposalResponse])
async def get_proposals(
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's proposals"""
    
    query = db.query(Proposal).filter(Proposal.created_by == current_user.id)
    
    if status:
        query = query.filter(Proposal.status == status)
    
    proposals = query.order_by(Proposal.created_at.desc()).offset(skip).limit(limit).all()
    
    return [
        ProposalResponse(
            id=proposal.id,
            proposal_number=proposal.proposal_number,
            proposal_title=proposal.proposal_title,
            status=proposal.status.value,
            submission_deadline=proposal.submission_deadline,
            overall_progress_percentage=proposal.overall_progress_percentage,
            compliance_score=proposal.compliance_score,
            win_probability=proposal.win_probability
        )
        for proposal in proposals
    ]

@router.get("/proposals/{proposal_id}")
async def get_proposal_detail(
    proposal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed proposal information"""
    
    proposal = db.query(Proposal).filter(
        Proposal.id == proposal_id,
        Proposal.created_by == current_user.id
    ).first()
    
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    
    # Get volumes
    volumes = db.query(ProposalVolume).filter(
        ProposalVolume.proposal_id == proposal_id
    ).all()
    
    # Get sections
    sections = db.query(ProposalSection).filter(
        ProposalSection.proposal_id == proposal_id
    ).order_by(ProposalSection.section_number).all()
    
    # Get latest reviews
    recent_reviews = db.query(ProposalReview).filter(
        ProposalReview.proposal_id == proposal_id
    ).order_by(ProposalReview.review_date.desc()).limit(5).all()
    
    return {
        "proposal": {
            "id": proposal.id,
            "proposal_number": proposal.proposal_number,
            "proposal_title": proposal.proposal_title,
            "status": proposal.status.value,
            "submission_deadline": proposal.submission_deadline.isoformat(),
            "progress": proposal.overall_progress_percentage,
            "compliance_score": proposal.compliance_score,
            "quality_score": proposal.quality_score,
            "win_probability": proposal.win_probability,
            "win_strategy": proposal.win_strategy,
            "value_proposition": proposal.value_proposition,
            "discriminators": proposal.discriminators or []
        },
        "volumes": [
            {
                "id": vol.id,
                "name": vol.volume_name,
                "type": vol.volume_type.value,
                "completion": vol.completion_percentage,
                "page_limit": vol.page_limit,
                "current_pages": vol.current_page_count,
                "assigned_lead": vol.assigned_lead
            }
            for vol in volumes
        ],
        "sections": [
            {
                "id": sect.id,
                "number": sect.section_number,
                "title": sect.section_title,
                "type": sect.section_type,
                "completion": sect.completion_percentage,
                "compliance": sect.compliance_status.value,
                "word_count": sect.word_count,
                "assigned_writer": sect.assigned_writer,
                "ai_generated": sect.ai_generated_content
            }
            for sect in sections
        ],
        "recent_reviews": [
            {
                "id": review.id,
                "type": review.review_type,
                "date": review.review_date.isoformat(),
                "overall_score": review.overall_score,
                "critical_issues": len(review.critical_issues or [])
            }
            for review in recent_reviews
        ],
        "readiness_gates": proposal.readiness_gates_status or {},
        "ai_recommendations": proposal.ai_recommendations or []
    }

@router.get("/proposals/{proposal_id}/sections", response_model=List[SectionResponse])
async def get_proposal_sections(
    proposal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get proposal sections"""
    
    # Verify proposal ownership
    proposal = db.query(Proposal).filter(
        Proposal.id == proposal_id,
        Proposal.created_by == current_user.id
    ).first()
    
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    
    sections = db.query(ProposalSection).filter(
        ProposalSection.proposal_id == proposal_id
    ).order_by(ProposalSection.section_number).all()
    
    return [
        SectionResponse(
            id=section.id,
            section_number=section.section_number,
            section_title=section.section_title,
            completion_percentage=section.completion_percentage,
            compliance_status=section.compliance_status.value,
            word_count=section.word_count,
            assigned_writer=section.assigned_writer
        )
        for section in sections
    ]

@router.get("/proposals/{proposal_id}/sections/{section_id}")
async def get_section_detail(
    proposal_id: int,
    section_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed section information"""
    
    # Verify proposal ownership
    proposal = db.query(Proposal).filter(
        Proposal.id == proposal_id,
        Proposal.created_by == current_user.id
    ).first()
    
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    
    section = db.query(ProposalSection).filter(
        ProposalSection.id == section_id,
        ProposalSection.proposal_id == proposal_id
    ).first()
    
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
    
    return {
        "section": {
            "id": section.id,
            "number": section.section_number,
            "title": section.section_title,
            "type": section.section_type,
            "content": section.content,
            "outline": section.content_outline or {},
            "completion": section.completion_percentage,
            "compliance_status": section.compliance_status.value,
            "compliance_notes": section.compliance_notes,
            "word_count": section.word_count,
            "page_count": section.page_count,
            "assigned_writer": section.assigned_writer,
            "assigned_reviewer": section.assigned_reviewer,
            "ai_generated": section.ai_generated_content,
            "ai_suggestions": section.ai_suggestions or [],
            "quality_score": section.quality_score,
            "requirements": section.requirements or [],
            "dependencies": section.depends_on_sections or []
        }
    }

@router.post("/proposals/sections/generate-content")
async def generate_section_content(
    request: SectionContentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate AI content for proposal section"""
    
    engine = ProposalManagementEngine(db)
    
    try:
        result = await engine.generate_section_content(
            request.section_id,
            current_user.id,
            request.context
        )
        
        return {
            "status": "success",
            **result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Content generation failed: {str(e)}")

@router.post("/proposals/{proposal_id}/compliance-check")
async def check_proposal_compliance(
    proposal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Run comprehensive compliance check"""
    
    engine = ProposalManagementEngine(db)
    
    try:
        result = await engine.check_compliance(proposal_id, current_user.id)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Compliance check failed: {str(e)}")

@router.get("/proposals/{proposal_id}/readiness-gates")
async def assess_readiness_gates(
    proposal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Assess proposal readiness gates"""
    
    engine = ProposalManagementEngine(db)
    
    try:
        result = await engine.assess_readiness_gates(proposal_id, current_user.id)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Readiness assessment failed: {str(e)}")

@router.post("/proposals/reviews")
async def conduct_proposal_review(
    request: ReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Conduct structured proposal review"""
    
    engine = ProposalManagementEngine(db)
    
    try:
        result = await engine.conduct_proposal_review(
            request.proposal_id,
            request.review_type,
            current_user.id,
            request.sections_to_review
        )
        
        return {
            "status": "success",
            **result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Proposal review failed: {str(e)}")

@router.get("/proposals/{proposal_id}/reviews")
async def get_proposal_reviews(
    proposal_id: int,
    review_type: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get proposal reviews"""
    
    # Verify proposal ownership
    proposal = db.query(Proposal).filter(
        Proposal.id == proposal_id,
        Proposal.created_by == current_user.id
    ).first()
    
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    
    query = db.query(ProposalReview).filter(ProposalReview.proposal_id == proposal_id)
    
    if review_type:
        query = query.filter(ProposalReview.review_type == review_type)
    
    reviews = query.order_by(ProposalReview.review_date.desc()).offset(skip).limit(limit).all()
    
    return [
        {
            "id": review.id,
            "type": review.review_type,
            "name": review.review_name,
            "date": review.review_date.isoformat(),
            "reviewer_id": review.reviewer_id,
            "overall_score": review.overall_score,
            "technical_score": review.technical_score,
            "management_score": review.management_score,
            "compliance_score": review.compliance_score,
            "strengths": review.strengths or [],
            "weaknesses": review.weaknesses or [],
            "critical_issues": review.critical_issues or [],
            "action_items": review.action_items or [],
            "status": review.review_status
        }
        for review in reviews
    ]

@router.put("/proposals/{proposal_id}/sections/{section_id}")
async def update_section_content(
    proposal_id: int,
    section_id: int,
    content: str,
    assigned_writer: Optional[int] = None,
    assigned_reviewer: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update section content"""
    
    # Verify proposal ownership
    proposal = db.query(Proposal).filter(
        Proposal.id == proposal_id,
        Proposal.created_by == current_user.id
    ).first()
    
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    
    section = db.query(ProposalSection).filter(
        ProposalSection.id == section_id,
        ProposalSection.proposal_id == proposal_id
    ).first()
    
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
    
    # Update section
    section.content = content
    section.word_count = len(content.split()) if content else 0
    section.assigned_writer = assigned_writer
    section.assigned_reviewer = assigned_reviewer
    section.updated_at = datetime.utcnow()
    
    # Update completion percentage based on content length
    if section.word_count > 0:
        section.completion_percentage = min(100.0, (section.word_count / 500) * 100)  # Assume 500 words = 100%
    
    db.commit()
    
    return {
        "status": "success",
        "word_count": section.word_count,
        "completion_percentage": section.completion_percentage
    }

@router.get("/proposal-library")
async def get_proposal_library(
    content_type: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get proposal library content"""
    
    query = db.query(ProposalLibrary).filter(
        ProposalLibrary.company_id == current_user.id,
        ProposalLibrary.is_active == True
    )
    
    if content_type:
        query = query.filter(ProposalLibrary.content_type == content_type)
    
    if category:
        query = query.filter(ProposalLibrary.category == category)
    
    if search:
        query = query.filter(
            ProposalLibrary.content_title.ilike(f"%{search}%") |
            ProposalLibrary.content_text.ilike(f"%{search}%")
        )
    
    library_items = query.order_by(ProposalLibrary.usage_count.desc()).offset(skip).limit(limit).all()
    
    return [
        {
            "id": item.id,
            "title": item.content_title,
            "type": item.content_type,
            "category": item.category,
            "content": item.content_text[:500] + "..." if len(item.content_text) > 500 else item.content_text,
            "usage_count": item.usage_count,
            "quality_rating": item.quality_rating,
            "tags": item.tags or [],
            "last_used": item.last_used_date.isoformat() if item.last_used_date else None
        }
        for item in library_items
    ]

@router.post("/proposal-library")
async def add_library_content(
    content_title: str,
    content_type: str,
    category: str,
    content_text: str,
    tags: List[str] = [],
    keywords: List[str] = [],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add content to proposal library"""
    
    library_item = ProposalLibrary(
        company_id=current_user.id,
        content_title=content_title,
        content_type=content_type,
        category=category,
        content_text=content_text,
        tags=tags,
        keywords=keywords,
        created_by=current_user.id
    )
    
    db.add(library_item)
    db.commit()
    db.refresh(library_item)
    
    return {
        "library_item_id": library_item.id,
        "status": "success",
        "message": "Content added to library"
    }

@router.get("/dashboard/proposal-stats")
async def get_proposal_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get proposal dashboard statistics"""
    
    # Proposal counts by status
    total_proposals = db.query(Proposal).filter(Proposal.created_by == current_user.id).count()
    
    active_proposals = db.query(Proposal).filter(
        Proposal.created_by == current_user.id,
        Proposal.status.in_([ProposalStatus.DRAFT, ProposalStatus.IN_PROGRESS, ProposalStatus.REVIEW])
    ).count()
    
    submitted_proposals = db.query(Proposal).filter(
        Proposal.created_by == current_user.id,
        Proposal.status == ProposalStatus.SUBMITTED
    ).count()
    
    awarded_proposals = db.query(Proposal).filter(
        Proposal.created_by == current_user.id,
        Proposal.status == ProposalStatus.AWARDED
    ).count()
    
    # Win rate calculation
    completed_proposals = db.query(Proposal).filter(
        Proposal.created_by == current_user.id,
        Proposal.status.in_([ProposalStatus.AWARDED, ProposalStatus.NOT_AWARDED])
    ).count()
    
    win_rate = (awarded_proposals / completed_proposals * 100) if completed_proposals > 0 else 0
    
    # Upcoming deadlines
    upcoming_deadlines = db.query(Proposal).filter(
        Proposal.created_by == current_user.id,
        Proposal.submission_deadline >= datetime.now(),
        Proposal.submission_deadline <= datetime.now() + timedelta(days=14),
        Proposal.status.in_([ProposalStatus.DRAFT, ProposalStatus.IN_PROGRESS, ProposalStatus.REVIEW])
    ).count()
    
    # Recent activity
    recent_proposals = db.query(Proposal).filter(
        Proposal.created_by == current_user.id
    ).order_by(Proposal.updated_at.desc()).limit(5).all()
    
    return {
        "proposal_stats": {
            "total_proposals": total_proposals,
            "active_proposals": active_proposals,
            "submitted_proposals": submitted_proposals,
            "awarded_proposals": awarded_proposals,
            "win_rate": round(win_rate, 1)
        },
        "deadlines": {
            "upcoming_deadlines": upcoming_deadlines
        },
        "recent_activity": [
            {
                "id": prop.id,
                "title": prop.proposal_title,
                "status": prop.status.value,
                "progress": prop.overall_progress_percentage,
                "deadline": prop.submission_deadline.isoformat(),
                "updated": prop.updated_at.isoformat()
            }
            for prop in recent_proposals
        ]
    }