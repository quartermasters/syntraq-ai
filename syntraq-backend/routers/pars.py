from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel

from database.connection import get_db
from models.pars import (
    Contract, ContractDeliverable, ContractTransition, ComplianceItem,
    PerformanceMetric, KnowledgeTransition, PostAwardChecklist, LessonsLearned,
    ContractStatus, DeliverableStatus, RiskLevel, ComplianceStatus
)
from services.pars_engine import PARSEngine
from routers.users import get_current_user
from models.user import User

router = APIRouter()

class ContractCreateRequest(BaseModel):
    proposal_id: int
    award_details: Dict[str, Any]

class DeliverableUpdateRequest(BaseModel):
    completion_percentage: Optional[float] = None
    status: Optional[str] = None
    actual_hours: Optional[float] = None
    notes: Optional[str] = None

class ComplianceAssessmentRequest(BaseModel):
    include_recommendations: bool = True
    assessment_date: Optional[str] = None

class LessonLearnedRequest(BaseModel):
    title: str
    category: str
    description: str
    situation: Optional[str] = None
    actions: Optional[str] = None
    outcomes: Optional[str] = None
    lesson_date: Optional[str] = None

class TransitionPlanRequest(BaseModel):
    transition_requirements: Dict[str, Any]
    timeline_constraints: Optional[Dict[str, Any]] = None

class ContractResponse(BaseModel):
    id: int
    contract_number: str
    contract_title: str
    status: str
    contract_value: float
    start_date: datetime
    end_date: datetime
    
    class Config:
        from_attributes = True

class DeliverableResponse(BaseModel):
    id: int
    deliverable_number: str
    deliverable_title: str
    status: str
    completion_percentage: float
    due_date: datetime
    risk_level: str
    
    class Config:
        from_attributes = True

@router.post("/contracts")
async def create_contract(
    request: ContractCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create contract from awarded proposal"""
    
    engine = PARSEngine(db)
    
    try:
        result = await engine.create_contract_from_proposal(
            current_user.id,
            request.proposal_id,
            request.award_details
        )
        
        return {
            "status": "success",
            **result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Contract creation failed: {str(e)}")

@router.get("/contracts", response_model=List[ContractResponse])
async def get_contracts(
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get contracts with filtering"""
    
    query = db.query(Contract).filter(Contract.company_id == current_user.id)
    
    if status:
        query = query.filter(Contract.status == ContractStatus(status))
    
    contracts = query.order_by(Contract.created_at.desc()).offset(skip).limit(limit).all()
    
    return [
        ContractResponse(
            id=contract.id,
            contract_number=contract.contract_number,
            contract_title=contract.contract_title,
            status=contract.status.value,
            contract_value=contract.contract_value,
            start_date=contract.start_date,
            end_date=contract.end_date
        )
        for contract in contracts
    ]

@router.get("/contracts/{contract_id}")
async def get_contract_detail(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed contract information"""
    
    contract = db.query(Contract).filter(
        Contract.id == contract_id,
        Contract.company_id == current_user.id
    ).first()
    
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    # Get related data
    deliverables = db.query(ContractDeliverable).filter(
        ContractDeliverable.contract_id == contract_id
    ).all()
    
    transitions = db.query(ContractTransition).filter(
        ContractTransition.contract_id == contract_id
    ).order_by(ContractTransition.planned_start_date).all()
    
    compliance_items = db.query(ComplianceItem).filter(
        ComplianceItem.contract_id == contract_id
    ).all()
    
    # Calculate summary metrics
    total_deliverables = len(deliverables)
    completed_deliverables = len([d for d in deliverables if d.status == DeliverableStatus.DELIVERED])
    avg_completion = sum([d.completion_percentage for d in deliverables]) / total_deliverables if total_deliverables > 0 else 0
    
    overdue_deliverables = len([
        d for d in deliverables 
        if d.due_date < datetime.utcnow() and d.status not in [DeliverableStatus.DELIVERED, DeliverableStatus.APPROVED]
    ])
    
    return {
        "contract": {
            "id": contract.id,
            "contract_number": contract.contract_number,
            "contract_title": contract.contract_title,
            "contracting_agency": contract.contracting_agency,
            "contract_type": contract.contract_type,
            "contract_value": contract.contract_value,
            "status": contract.status.value,
            "start_date": contract.start_date.isoformat() if contract.start_date else None,
            "end_date": contract.end_date.isoformat() if contract.end_date else None,
            "award_date": contract.award_date.isoformat() if contract.award_date else None,
            "performance_rating": contract.performance_rating,
            "schedule_performance": contract.schedule_performance,
            "cost_performance": contract.cost_performance,
            "government_pm": contract.government_pm,
            "government_cor": contract.government_cor
        },
        "financial_summary": {
            "contract_value": contract.contract_value,
            "total_obligated": contract.total_obligated,
            "total_invoiced": contract.total_invoiced,
            "total_paid": contract.total_paid,
            "remaining_funds": contract.remaining_funds
        },
        "deliverables_summary": {
            "total_deliverables": total_deliverables,
            "completed_deliverables": completed_deliverables,
            "overdue_deliverables": overdue_deliverables,
            "avg_completion_percentage": round(avg_completion, 1)
        },
        "transitions_count": len(transitions),
        "compliance_items_count": len(compliance_items),
        "current_risks": contract.current_risks or [],
        "open_issues": contract.open_issues or []
    }

@router.get("/contracts/{contract_id}/deliverables", response_model=List[DeliverableResponse])
async def get_contract_deliverables(
    contract_id: int,
    status: Optional[str] = Query(None),
    overdue_only: bool = Query(False),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get contract deliverables"""
    
    # Verify contract ownership
    contract = db.query(Contract).filter(
        Contract.id == contract_id,
        Contract.company_id == current_user.id
    ).first()
    
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    query = db.query(ContractDeliverable).filter(
        ContractDeliverable.contract_id == contract_id
    )
    
    if status:
        query = query.filter(ContractDeliverable.status == DeliverableStatus(status))
    
    if overdue_only:
        query = query.filter(
            ContractDeliverable.due_date < datetime.utcnow(),
            ContractDeliverable.status.notin_([DeliverableStatus.DELIVERED, DeliverableStatus.APPROVED])
        )
    
    deliverables = query.order_by(ContractDeliverable.due_date).offset(skip).limit(limit).all()
    
    return [
        DeliverableResponse(
            id=deliverable.id,
            deliverable_number=deliverable.deliverable_number,
            deliverable_title=deliverable.deliverable_title,
            status=deliverable.status.value,
            completion_percentage=deliverable.completion_percentage,
            due_date=deliverable.due_date,
            risk_level=deliverable.risk_level.value
        )
        for deliverable in deliverables
    ]

@router.get("/deliverables/{deliverable_id}")
async def get_deliverable_detail(
    deliverable_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed deliverable information"""
    
    deliverable = db.query(ContractDeliverable).filter(
        ContractDeliverable.id == deliverable_id,
        ContractDeliverable.company_id == current_user.id
    ).first()
    
    if not deliverable:
        raise HTTPException(status_code=404, detail="Deliverable not found")
    
    return {
        "deliverable": {
            "id": deliverable.id,
            "deliverable_number": deliverable.deliverable_number,
            "deliverable_title": deliverable.deliverable_title,
            "deliverable_type": deliverable.deliverable_type,
            "description": deliverable.description,
            "status": deliverable.status.value,
            "completion_percentage": deliverable.completion_percentage,
            "due_date": deliverable.due_date.isoformat(),
            "submitted_date": deliverable.submitted_date.isoformat() if deliverable.submitted_date else None,
            "approved_date": deliverable.approved_date.isoformat() if deliverable.approved_date else None,
            "acceptance_criteria": deliverable.acceptance_criteria or [],
            "quality_requirements": deliverable.quality_requirements or [],
            "compliance_requirements": deliverable.compliance_requirements or [],
            "government_reviewer": deliverable.government_reviewer,
            "review_period_days": deliverable.review_period_days,
            "delivery_method": deliverable.delivery_method,
            "estimated_hours": deliverable.estimated_hours,
            "actual_hours": deliverable.actual_hours,
            "assigned_team_members": deliverable.assigned_team_members or [],
            "risk_level": deliverable.risk_level.value,
            "risk_factors": deliverable.risk_factors or [],
            "depends_on_deliverables": deliverable.depends_on_deliverables or [],
            "government_feedback": deliverable.government_feedback,
            "current_version": deliverable.current_version
        },
        "schedule_status": {
            "days_until_due": (deliverable.due_date - datetime.utcnow()).days,
            "is_overdue": deliverable.due_date < datetime.utcnow() and deliverable.status not in [DeliverableStatus.DELIVERED, DeliverableStatus.APPROVED],
            "on_track": deliverable.completion_percentage >= 75 or deliverable.due_date > datetime.utcnow() + timedelta(days=7)
        }
    }

@router.put("/deliverables/{deliverable_id}")
async def update_deliverable_progress(
    deliverable_id: int,
    request: DeliverableUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update deliverable progress"""
    
    engine = PARSEngine(db)
    
    try:
        progress_update = {
            'completion_percentage': request.completion_percentage,
            'status': request.status,
            'actual_hours': request.actual_hours,
            'notes': request.notes
        }
        
        result = await engine.track_deliverable_progress(
            deliverable_id,
            current_user.id,
            progress_update
        )
        
        return {
            "status": "success",
            **result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Deliverable update failed: {str(e)}")

@router.post("/contracts/{contract_id}/transition-plan")
async def generate_transition_plan(
    contract_id: int,
    request: TransitionPlanRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate AI-powered transition plan"""
    
    engine = PARSEngine(db)
    
    try:
        result = await engine.generate_transition_plan(
            contract_id,
            current_user.id,
            request.transition_requirements
        )
        
        return {
            "status": "success",
            **result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transition plan generation failed: {str(e)}")

@router.get("/contracts/{contract_id}/transitions")
async def get_contract_transitions(
    contract_id: int,
    phase: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get contract transitions"""
    
    # Verify contract ownership
    contract = db.query(Contract).filter(
        Contract.id == contract_id,
        Contract.company_id == current_user.id
    ).first()
    
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    query = db.query(ContractTransition).filter(
        ContractTransition.contract_id == contract_id
    )
    
    if phase:
        from models.pars import TransitionPhase
        query = query.filter(ContractTransition.transition_phase == TransitionPhase(phase))
    
    if status:
        query = query.filter(ContractTransition.status == status)
    
    transitions = query.order_by(ContractTransition.planned_start_date).all()
    
    return [
        {
            "id": transition.id,
            "transition_name": transition.transition_name,
            "transition_phase": transition.transition_phase.value,
            "description": transition.description,
            "status": transition.status,
            "completion_percentage": transition.completion_percentage,
            "planned_start_date": transition.planned_start_date.isoformat(),
            "planned_end_date": transition.planned_end_date.isoformat(),
            "actual_start_date": transition.actual_start_date.isoformat() if transition.actual_start_date else None,
            "actual_end_date": transition.actual_end_date.isoformat() if transition.actual_end_date else None,
            "responsible_person": transition.responsible_person,
            "government_poc": transition.government_poc,
            "milestones": transition.milestones or [],
            "transition_risks": transition.transition_risks or []
        }
        for transition in transitions
    ]

@router.post("/contracts/{contract_id}/compliance-assessment")
async def conduct_compliance_assessment(
    contract_id: int,
    request: ComplianceAssessmentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Conduct comprehensive compliance assessment"""
    
    engine = PARSEngine(db)
    
    try:
        result = await engine.conduct_compliance_assessment(
            contract_id,
            current_user.id
        )
        
        return {
            "status": "success",
            **result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Compliance assessment failed: {str(e)}")

@router.get("/contracts/{contract_id}/compliance")
async def get_compliance_status(
    contract_id: int,
    category: Optional[str] = Query(None),
    criticality: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get contract compliance status"""
    
    # Verify contract ownership
    contract = db.query(Contract).filter(
        Contract.id == contract_id,
        Contract.company_id == current_user.id
    ).first()
    
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    query = db.query(ComplianceItem).filter(
        ComplianceItem.contract_id == contract_id
    )
    
    if category:
        query = query.filter(ComplianceItem.compliance_category == category)
    
    if criticality:
        query = query.filter(ComplianceItem.criticality_level == RiskLevel(criticality))
    
    if status:
        query = query.filter(ComplianceItem.compliance_status == ComplianceStatus(status))
    
    compliance_items = query.all()
    
    return [
        {
            "id": item.id,
            "requirement_title": item.requirement_title,
            "requirement_source": item.requirement_source,
            "compliance_category": item.compliance_category,
            "compliance_status": item.compliance_status.value,
            "criticality_level": item.criticality_level.value,
            "regulatory_requirement": item.regulatory_requirement,
            "last_review_date": item.last_review_date.isoformat() if item.last_review_date else None,
            "next_review_date": item.next_review_date.isoformat() if item.next_review_date else None,
            "responsible_person": item.responsible_person,
            "evidence_required": item.evidence_required or [],
            "evidence_provided": item.evidence_provided or [],
            "non_compliance_risk": item.non_compliance_risk
        }
        for item in compliance_items
    ]

@router.post("/contracts/{contract_id}/lessons-learned")
async def capture_lesson_learned(
    contract_id: int,
    request: LessonLearnedRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Capture lessons learned"""
    
    engine = PARSEngine(db)
    
    try:
        lesson_data = {
            'title': request.title,
            'category': request.category,
            'description': request.description,
            'situation': request.situation,
            'actions': request.actions,
            'outcomes': request.outcomes,
            'lesson_date': request.lesson_date
        }
        
        result = await engine.capture_lessons_learned(
            contract_id,
            current_user.id,
            lesson_data
        )
        
        return {
            "status": "success",
            **result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lesson capture failed: {str(e)}")

@router.get("/contracts/{contract_id}/lessons-learned")
async def get_lessons_learned(
    contract_id: int,
    category: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get lessons learned for contract"""
    
    # Verify contract ownership
    contract = db.query(Contract).filter(
        Contract.id == contract_id,
        Contract.company_id == current_user.id
    ).first()
    
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    query = db.query(LessonsLearned).filter(
        LessonsLearned.contract_id == contract_id
    )
    
    if category:
        query = query.filter(LessonsLearned.lesson_category == category)
    
    lessons = query.order_by(LessonsLearned.lesson_date.desc()).offset(skip).limit(limit).all()
    
    return [
        {
            "id": lesson.id,
            "lesson_title": lesson.lesson_title,
            "lesson_category": lesson.lesson_category,
            "lesson_description": lesson.lesson_description,
            "lesson_date": lesson.lesson_date.isoformat(),
            "what_worked_well": lesson.what_worked_well,
            "what_could_improve": lesson.what_could_improve,
            "recommendations": lesson.recommendations or [],
            "best_practices": lesson.best_practices or [],
            "applicable_situations": lesson.applicable_situations or [],
            "estimated_value": lesson.estimated_value,
            "implemented_changes": lesson.implemented_changes or []
        }
        for lesson in lessons
    ]

@router.get("/contracts/{contract_id}/checklists")
async def get_post_award_checklists(
    contract_id: int,
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get post-award checklists"""
    
    # Verify contract ownership
    contract = db.query(Contract).filter(
        Contract.id == contract_id,
        Contract.company_id == current_user.id
    ).first()
    
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    query = db.query(PostAwardChecklist).filter(
        PostAwardChecklist.contract_id == contract_id
    )
    
    if category:
        query = query.filter(PostAwardChecklist.checklist_category == category)
    
    if status:
        query = query.filter(PostAwardChecklist.checklist_status == status)
    
    checklists = query.all()
    
    return [
        {
            "id": checklist.id,
            "checklist_name": checklist.checklist_name,
            "checklist_category": checklist.checklist_category,
            "checklist_phase": checklist.checklist_phase.value,
            "checklist_status": checklist.checklist_status,
            "total_items": checklist.total_items,
            "completed_items": checklist.completed_items,
            "completion_percentage": checklist.completion_percentage,
            "target_completion_date": checklist.target_completion_date.isoformat(),
            "actual_completion_date": checklist.actual_completion_date.isoformat() if checklist.actual_completion_date else None,
            "responsible_person": checklist.responsible_person,
            "checklist_items": checklist.checklist_items or []
        }
        for checklist in checklists
    ]

@router.put("/checklists/{checklist_id}/items/{item_id}")
async def update_checklist_item(
    checklist_id: int,
    item_id: int,
    completed: bool,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update checklist item status"""
    
    checklist = db.query(PostAwardChecklist).filter(
        PostAwardChecklist.id == checklist_id,
        PostAwardChecklist.company_id == current_user.id
    ).first()
    
    if not checklist:
        raise HTTPException(status_code=404, detail="Checklist not found")
    
    # Update specific checklist item
    items = checklist.checklist_items or []
    
    for item in items:
        if item.get('id') == item_id:
            item['completed'] = completed
            item['completed_date'] = datetime.utcnow().isoformat() if completed else None
            if notes:
                item['notes'] = notes
            break
    else:
        raise HTTPException(status_code=404, detail="Checklist item not found")
    
    # Update checklist summary
    checklist.checklist_items = items
    checklist.completed_items = len([item for item in items if item.get('completed', False)])
    checklist.completion_percentage = (checklist.completed_items / checklist.total_items * 100) if checklist.total_items > 0 else 0
    
    if checklist.completion_percentage >= 100:
        checklist.checklist_status = "completed"
        checklist.actual_completion_date = datetime.utcnow()
    
    db.commit()
    
    return {
        "status": "success",
        "checklist_id": checklist_id,
        "item_id": item_id,
        "completion_percentage": checklist.completion_percentage,
        "checklist_status": checklist.checklist_status
    }

@router.get("/dashboard/contract-analytics")
async def get_contract_analytics(
    days_back: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get contract analytics dashboard"""
    
    start_date = datetime.utcnow() - timedelta(days=days_back)
    
    # Contract statistics
    total_contracts = db.query(Contract).filter(Contract.company_id == current_user.id).count()
    
    active_contracts = db.query(Contract).filter(
        Contract.company_id == current_user.id,
        Contract.status == ContractStatus.ACTIVE
    ).count()
    
    total_contract_value = db.query(Contract).filter(
        Contract.company_id == current_user.id
    ).with_entities(Contract.contract_value).all()
    
    total_value = sum([c[0] for c in total_contract_value if c[0]]) if total_contract_value else 0
    
    # Deliverable statistics
    total_deliverables = db.query(ContractDeliverable).filter(
        ContractDeliverable.company_id == current_user.id
    ).count()
    
    overdue_deliverables = db.query(ContractDeliverable).filter(
        ContractDeliverable.company_id == current_user.id,
        ContractDeliverable.due_date < datetime.utcnow(),
        ContractDeliverable.status.notin_([DeliverableStatus.DELIVERED, DeliverableStatus.APPROVED])
    ).count()
    
    completed_deliverables = db.query(ContractDeliverable).filter(
        ContractDeliverable.company_id == current_user.id,
        ContractDeliverable.status.in_([DeliverableStatus.DELIVERED, DeliverableStatus.APPROVED])
    ).count()
    
    # Compliance statistics
    compliance_items = db.query(ComplianceItem).filter(
        ComplianceItem.company_id == current_user.id
    ).all()
    
    compliant_items = len([c for c in compliance_items if c.compliance_status == ComplianceStatus.COMPLIANT])
    non_compliant_items = len([c for c in compliance_items if c.compliance_status == ComplianceStatus.NON_COMPLIANT])
    
    compliance_rate = (compliant_items / len(compliance_items) * 100) if compliance_items else 100
    
    # Recent lessons learned
    recent_lessons = db.query(LessonsLearned).filter(
        LessonsLearned.company_id == current_user.id,
        LessonsLearned.created_at >= start_date
    ).count()
    
    return {
        "period_days": days_back,
        "contract_metrics": {
            "total_contracts": total_contracts,
            "active_contracts": active_contracts,
            "total_contract_value": total_value,
            "avg_contract_value": total_value / total_contracts if total_contracts > 0 else 0
        },
        "deliverable_metrics": {
            "total_deliverables": total_deliverables,
            "completed_deliverables": completed_deliverables,
            "overdue_deliverables": overdue_deliverables,
            "completion_rate": (completed_deliverables / total_deliverables * 100) if total_deliverables > 0 else 100,
            "overdue_rate": (overdue_deliverables / total_deliverables * 100) if total_deliverables > 0 else 0
        },
        "compliance_metrics": {
            "total_items": len(compliance_items),
            "compliant_items": compliant_items,
            "non_compliant_items": non_compliant_items,
            "compliance_rate": round(compliance_rate, 1)
        },
        "learning_metrics": {
            "recent_lessons_captured": recent_lessons,
            "lessons_per_month": recent_lessons * 30 / days_back if days_back > 0 else 0
        },
        "performance_indicators": {
            "contract_health_score": round((compliance_rate + (100 - (overdue_deliverables / total_deliverables * 100) if total_deliverables > 0 else 100)) / 2, 1),
            "delivery_reliability": round((completed_deliverables / total_deliverables * 100) if total_deliverables > 0 else 100, 1)
        }
    }