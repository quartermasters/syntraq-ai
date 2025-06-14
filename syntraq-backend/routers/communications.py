"""
© 2025 Aliff Capital, Quartermasters FZC, and SkillvenzA. All rights reserved.

Syntraq AI - CAH (Communication & Arrangement Hub) API Router
A Joint Innovation by Aliff Capital, Quartermasters FZC, and SkillvenzA
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel

from database.connection import get_db
from models.communications import (
    Contact, Communication, CommunicationTemplate, CommunicationDocument,
    MeetingSchedule, CommunicationType, CommunicationStatus, ContactType
)
from services.communication_hub import CommunicationHubService
from routers.users import get_current_user
from models.user import User

router = APIRouter()

class ContactCreateRequest(BaseModel):
    first_name: str
    last_name: str
    email: str
    organization: str
    contact_type: str
    title: Optional[str] = None
    phone: Optional[str] = None

class CommunicationRequest(BaseModel):
    contact_id: int
    communication_type: str
    context: Dict[str, Any]
    template_id: Optional[int] = None

class MeetingRequest(BaseModel):
    contact_ids: List[int]
    title: str
    scheduled_date: str
    duration_minutes: int = 60
    meeting_type: str = "video"
    description: Optional[str] = None
    agenda_items: List[str] = []

class ContactResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    organization: str
    contact_type: str
    title: Optional[str]
    relationship_level: str
    last_contact_date: Optional[datetime]
    
    class Config:
        from_attributes = True

@router.post("/contacts")
async def add_contact(
    request: ContactCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a new contact"""
    
    # Check if contact already exists
    existing = db.query(Contact).filter(
        Contact.company_id == current_user.id,
        Contact.email == request.email
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Contact already exists")
    
    contact = Contact(
        company_id=current_user.id,
        first_name=request.first_name,
        last_name=request.last_name,
        email=request.email,
        organization=request.organization,
        contact_type=ContactType(request.contact_type),
        title=request.title,
        phone=request.phone,
        created_by=current_user.id
    )
    
    db.add(contact)
    db.commit()
    db.refresh(contact)
    
    return {
        "contact_id": contact.id,
        "status": "success",
        "message": "Contact added successfully"
    }

@router.get("/contacts", response_model=List[ContactResponse])
async def get_contacts(
    contact_type: Optional[str] = Query(None),
    organization: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get contacts with filtering"""
    
    query = db.query(Contact).filter(
        Contact.company_id == current_user.id,
        Contact.is_active == True
    )
    
    if contact_type:
        query = query.filter(Contact.contact_type == contact_type)
    
    if organization:
        query = query.filter(Contact.organization.ilike(f"%{organization}%"))
    
    contacts = query.order_by(Contact.last_contact_date.desc()).offset(skip).limit(limit).all()
    
    return [
        ContactResponse(
            id=contact.id,
            first_name=contact.first_name,
            last_name=contact.last_name,
            email=contact.email,
            organization=contact.organization,
            contact_type=contact.contact_type.value,
            title=contact.title,
            relationship_level=contact.relationship_level,
            last_contact_date=contact.last_contact_date
        )
        for contact in contacts
    ]

@router.post("/communications/ai-generate")
async def generate_ai_communication(
    request: CommunicationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate AI-powered communication"""
    
    service = CommunicationHubService(db)
    
    try:
        result = await service.create_ai_communication(
            current_user.id,
            request.contact_id,
            request.communication_type,
            request.context,
            request.template_id
        )
        
        return {
            "status": "success",
            **result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI communication generation failed: {str(e)}")

@router.post("/documents/nda")
async def generate_nda(
    contact_id: int,
    context: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate customized NDA document"""
    
    service = CommunicationHubService(db)
    
    try:
        result = await service.generate_nda_document(
            current_user.id,
            contact_id,
            context
        )
        
        return {
            "status": "success",
            **result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"NDA generation failed: {str(e)}")

@router.post("/teaming/request-confirmation")
async def request_teaming_confirmation(
    partner_contact_id: int,
    opportunity_id: int,
    teaming_details: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Request teaming arrangement confirmation"""
    
    service = CommunicationHubService(db)
    
    try:
        result = await service.request_teaming_confirmation(
            current_user.id,
            partner_contact_id,
            opportunity_id,
            teaming_details
        )
        
        return {
            "status": "success",
            **result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Teaming confirmation request failed: {str(e)}")

@router.post("/quotes/request")
async def request_pricing_quote(
    vendor_contact_id: int,
    quote_requirements: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Request pricing quote from vendor"""
    
    service = CommunicationHubService(db)
    
    try:
        result = await service.request_pricing_quote(
            current_user.id,
            vendor_contact_id,
            quote_requirements
        )
        
        return {
            "status": "success",
            **result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quote request failed: {str(e)}")

@router.post("/meetings/schedule")
async def schedule_meeting(
    request: MeetingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Schedule meeting with AI-generated invitations"""
    
    service = CommunicationHubService(db)
    
    try:
        result = await service.schedule_meeting(
            current_user.id,
            request.contact_ids,
            request.dict()
        )
        
        return {
            "status": "success",
            **result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Meeting scheduling failed: {str(e)}")

@router.get("/communications")
async def get_communications(
    contact_id: Optional[int] = Query(None),
    communication_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get communications with filtering"""
    
    query = db.query(Communication).filter(Communication.company_id == current_user.id)
    
    if contact_id:
        query = query.filter(Communication.contact_id == contact_id)
    
    if communication_type:
        query = query.filter(Communication.communication_type == communication_type)
    
    if status:
        query = query.filter(Communication.status == status)
    
    if start_date:
        query = query.filter(Communication.created_at >= start_date)
    
    if end_date:
        query = query.filter(Communication.created_at <= end_date)
    
    communications = query.order_by(Communication.created_at.desc()).offset(skip).limit(limit).all()
    
    return [
        {
            "id": comm.id,
            "contact_name": f"{comm.contact.first_name} {comm.contact.last_name}" if comm.contact else "Unknown",
            "contact_organization": comm.contact.organization if comm.contact else None,
            "type": comm.communication_type.value,
            "subject": comm.subject,
            "status": comm.status.value,
            "direction": comm.direction,
            "created_at": comm.created_at.isoformat(),
            "sent_date": comm.sent_date.isoformat() if comm.sent_date else None,
            "ai_generated": comm.ai_generated,
            "requires_response": comm.requires_response
        }
        for comm in communications
    ]

@router.get("/communications/{comm_id}")
async def get_communication_detail(
    comm_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed communication information"""
    
    communication = db.query(Communication).filter(
        Communication.id == comm_id,
        Communication.company_id == current_user.id
    ).first()
    
    if not communication:
        raise HTTPException(status_code=404, detail="Communication not found")
    
    return {
        "id": communication.id,
        "contact": {
            "id": communication.contact.id if communication.contact else None,
            "name": f"{communication.contact.first_name} {communication.contact.last_name}" if communication.contact else "Unknown",
            "email": communication.contact.email if communication.contact else None,
            "organization": communication.contact.organization if communication.contact else None
        },
        "type": communication.communication_type.value,
        "subject": communication.subject,
        "content": communication.content,
        "status": communication.status.value,
        "direction": communication.direction,
        "priority": communication.priority,
        "created_at": communication.created_at.isoformat(),
        "sent_date": communication.sent_date.isoformat() if communication.sent_date else None,
        "ai_generated": communication.ai_generated,
        "ai_confidence": communication.ai_confidence_score,
        "sentiment_score": communication.sentiment_score,
        "key_topics": communication.key_topics or [],
        "action_items": communication.action_items or [],
        "requires_response": communication.requires_response,
        "response_deadline": communication.response_deadline.isoformat() if communication.response_deadline else None
    }

@router.post("/communications/{comm_id}/analyze")
async def analyze_communication(
    comm_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Analyze communication sentiment and extract insights"""
    
    service = CommunicationHubService(db)
    
    try:
        result = await service.analyze_communication_sentiment(comm_id, current_user.id)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Communication analysis failed: {str(e)}")

@router.post("/follow-up/generate")
async def generate_follow_up_sequence(
    contact_id: int,
    opportunity_id: Optional[int] = None,
    sequence_type: str = "general",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate AI-powered follow-up sequence"""
    
    service = CommunicationHubService(db)
    
    try:
        result = await service.generate_follow_up_sequence(
            current_user.id,
            contact_id,
            opportunity_id,
            sequence_type
        )
        
        return {
            "status": "success",
            **result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Follow-up sequence generation failed: {str(e)}")

@router.get("/meetings")
async def get_meetings(
    upcoming_only: bool = Query(True),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get scheduled meetings"""
    
    query = db.query(MeetingSchedule).filter(MeetingSchedule.company_id == current_user.id)
    
    if upcoming_only:
        query = query.filter(MeetingSchedule.scheduled_date >= datetime.now())
    
    meetings = query.order_by(MeetingSchedule.scheduled_date.asc()).offset(skip).limit(limit).all()
    
    return [
        {
            "id": meeting.id,
            "title": meeting.title,
            "description": meeting.description,
            "scheduled_date": meeting.scheduled_date.isoformat(),
            "duration_minutes": meeting.duration_minutes,
            "meeting_type": meeting.meeting_type,
            "location": meeting.location,
            "meeting_url": meeting.meeting_url,
            "participants": meeting.participants or [],
            "status": meeting.status,
            "agenda_items": meeting.agenda_items or []
        }
        for meeting in meetings
    ]

@router.get("/dashboard/communication-stats")
async def get_communication_dashboard(
    days_back: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get communication dashboard statistics"""
    
    start_date = datetime.now() - timedelta(days=days_back)
    
    # Communication stats
    total_communications = db.query(Communication).filter(
        Communication.company_id == current_user.id,
        Communication.created_at >= start_date
    ).count()
    
    sent_communications = db.query(Communication).filter(
        Communication.company_id == current_user.id,
        Communication.created_at >= start_date,
        Communication.status == CommunicationStatus.SENT
    ).count()
    
    ai_generated = db.query(Communication).filter(
        Communication.company_id == current_user.id,
        Communication.created_at >= start_date,
        Communication.ai_generated == True
    ).count()
    
    # Response rate
    communications_requiring_response = db.query(Communication).filter(
        Communication.company_id == current_user.id,
        Communication.created_at >= start_date,
        Communication.requires_response == True
    ).count()
    
    responded_communications = db.query(Communication).filter(
        Communication.company_id == current_user.id,
        Communication.created_at >= start_date,
        Communication.status == CommunicationStatus.RESPONDED
    ).count()
    
    response_rate = (responded_communications / communications_requiring_response * 100) if communications_requiring_response > 0 else 0
    
    # Active contacts
    active_contacts = db.query(Contact).filter(
        Contact.company_id == current_user.id,
        Contact.last_contact_date >= start_date,
        Contact.is_active == True
    ).count()
    
    # Upcoming meetings
    upcoming_meetings = db.query(MeetingSchedule).filter(
        MeetingSchedule.company_id == current_user.id,
        MeetingSchedule.scheduled_date >= datetime.now(),
        MeetingSchedule.scheduled_date <= datetime.now() + timedelta(days=7)
    ).count()
    
    return {
        "period_days": days_back,
        "communication_stats": {
            "total_communications": total_communications,
            "sent_communications": sent_communications,
            "ai_generated_percentage": (ai_generated / total_communications * 100) if total_communications > 0 else 0,
            "response_rate": response_rate
        },
        "relationship_stats": {
            "active_contacts": active_contacts,
            "upcoming_meetings": upcoming_meetings
        },
        "efficiency_metrics": {
            "avg_communications_per_day": total_communications / days_back if days_back > 0 else 0,
            "ai_automation_rate": (ai_generated / total_communications * 100) if total_communications > 0 else 0
        }
    }

@router.get("/documents")
async def get_communication_documents(
    contact_id: Optional[int] = Query(None),
    document_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get communication documents with filtering"""
    
    query = db.query(CommunicationDocument).filter(
        CommunicationDocument.company_id == current_user.id
    )
    
    if contact_id:
        query = query.filter(CommunicationDocument.contact_id == contact_id)
    
    if document_type:
        query = query.filter(CommunicationDocument.document_type == document_type)
    
    if status:
        query = query.filter(CommunicationDocument.status == status)
    
    documents = query.order_by(CommunicationDocument.created_at.desc()).offset(skip).limit(limit).all()
    
    return [
        {
            "id": doc.id,
            "document_name": doc.document_name,
            "document_type": doc.document_type.value,
            "status": doc.status,
            "contact_name": f"{doc.contact.first_name} {doc.contact.last_name}" if doc.contact else None,
            "contact_organization": doc.contact.organization if doc.contact else None,
            "requires_signature": doc.requires_signature,
            "signed_date": doc.signed_date.isoformat() if doc.signed_date else None,
            "expiry_date": doc.expiry_date.isoformat() if doc.expiry_date else None,
            "created_at": doc.created_at.isoformat(),
            "confidentiality_level": doc.confidentiality_level
        }
        for doc in documents
    ]

@router.get("/templates")
async def get_communication_templates(
    template_type: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get communication templates"""
    
    query = db.query(CommunicationTemplate).filter(
        CommunicationTemplate.company_id == current_user.id,
        CommunicationTemplate.is_active == True
    )
    
    if template_type:
        query = query.filter(CommunicationTemplate.template_type == template_type)
    
    if category:
        query = query.filter(CommunicationTemplate.category == category)
    
    templates = query.order_by(CommunicationTemplate.usage_count.desc()).all()
    
    return [
        {
            "id": template.id,
            "template_name": template.template_name,
            "template_type": template.template_type.value,
            "category": template.category,
            "use_case": template.use_case,
            "target_audience": template.target_audience,
            "tone": template.tone,
            "usage_count": template.usage_count,
            "success_rate": template.success_rate,
            "is_default": template.is_default
        }
        for template in templates
    ]

class TemplateCreateRequest(BaseModel):
    template_name: str
    template_type: str
    category: str
    subject_template: str
    content_template: str
    use_case: Optional[str] = None
    target_audience: Optional[str] = None
    tone: str = "professional"
    variables: List[str] = []

@router.post("/templates")
async def create_communication_template(
    request: TemplateCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create communication template"""
    
    template = CommunicationTemplate(
        company_id=current_user.id,
        template_name=request.template_name,
        template_type=CommunicationType(request.template_type),
        category=request.category,
        subject_template=request.subject_template,
        content_template=request.content_template,
        use_case=request.use_case,
        target_audience=request.target_audience,
        tone=request.tone,
        variables=request.variables,
        created_by=current_user.id
    )
    
    db.add(template)
    db.commit()
    db.refresh(template)
    
    return {
        "template_id": template.id,
        "status": "success",
        "message": "Template created successfully"
    }

@router.put("/communications/{comm_id}/send")
async def send_communication(
    comm_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Send a drafted communication"""
    
    communication = db.query(Communication).filter(
        Communication.id == comm_id,
        Communication.company_id == current_user.id,
        Communication.status == CommunicationStatus.DRAFT
    ).first()
    
    if not communication:
        raise HTTPException(status_code=404, detail="Draft communication not found")
    
    # Update communication status
    communication.status = CommunicationStatus.SENT
    communication.sent_date = datetime.utcnow()
    
    # Update contact last contact date
    if communication.contact:
        communication.contact.last_contact_date = datetime.utcnow()
    
    db.commit()
    
    return {
        "status": "success",
        "message": "Communication sent successfully",
        "sent_date": communication.sent_date.isoformat()
    }

@router.put("/documents/{doc_id}/sign")
async def mark_document_signed(
    doc_id: int,
    signed_by: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark document as signed"""
    
    document = db.query(CommunicationDocument).filter(
        CommunicationDocument.id == doc_id,
        CommunicationDocument.company_id == current_user.id
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    document.status = "signed"
    document.signed_date = datetime.utcnow()
    document.signed_by = signed_by
    
    # Update contact NDA status if it's an NDA
    if document.document_type.value == "nda" and document.contact:
        document.contact.nda_signed = True
        if document.expiry_date:
            document.contact.nda_expiry_date = document.expiry_date
    
    db.commit()
    
    return {
        "status": "success",
        "message": "Document marked as signed",
        "signed_date": document.signed_date.isoformat()
    }

@router.get("/analytics/engagement")
async def get_engagement_analytics(
    contact_id: Optional[int] = Query(None),
    days_back: int = Query(90, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get contact engagement analytics"""
    
    start_date = datetime.now() - timedelta(days=days_back)
    
    query = db.query(Communication).filter(
        Communication.company_id == current_user.id,
        Communication.created_at >= start_date
    )
    
    if contact_id:
        query = query.filter(Communication.contact_id == contact_id)
    
    communications = query.all()
    
    # Calculate engagement metrics
    total_sent = len([c for c in communications if c.direction == "outbound"])
    total_received = len([c for c in communications if c.direction == "inbound"])
    response_rate = (total_received / total_sent * 100) if total_sent > 0 else 0
    
    # Average response time
    response_times = []
    for comm in communications:
        if comm.responded_at and comm.sent_date:
            response_time = (comm.responded_at - comm.sent_date).total_seconds() / 3600  # hours
            response_times.append(response_time)
    
    avg_response_time = sum(response_times) / len(response_times) if response_times else 0
    
    # Sentiment analysis
    sentiment_scores = [c.sentiment_score for c in communications if c.sentiment_score is not None]
    avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
    
    return {
        "period_days": days_back,
        "engagement_metrics": {
            "total_communications": len(communications),
            "outbound_communications": total_sent,
            "inbound_communications": total_received,
            "response_rate": response_rate,
            "avg_response_time_hours": avg_response_time
        },
        "sentiment_analysis": {
            "avg_sentiment_score": avg_sentiment,
            "sentiment_trend": "positive" if avg_sentiment > 0.2 else "negative" if avg_sentiment < -0.2 else "neutral"
        },
        "communication_frequency": {
            "weekly_average": len(communications) / (days_back / 7) if days_back >= 7 else len(communications)
        }
    }