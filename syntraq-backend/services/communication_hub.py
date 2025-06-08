from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import json
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

from models.communications import (
    Contact, Communication, CommunicationTemplate, CommunicationDocument,
    CommunicationCampaign, CommunicationRule, MeetingSchedule,
    CommunicationType, CommunicationStatus, ContactType, DocumentType
)
from models.opportunity import Opportunity
from models.financial import FinancialProject
from services.ai_service import AIService

class CommunicationHubService:
    """AI-powered communication and arrangement management"""
    
    def __init__(self, db: Session):
        self.db = db
        self.ai_service = AIService()
    
    async def create_ai_communication(
        self,
        user_id: int,
        contact_id: int,
        communication_type: str,
        context: Dict[str, Any],
        template_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Generate AI-powered communication"""
        
        contact = self.db.query(Contact).filter(
            Contact.id == contact_id,
            Contact.company_id == user_id
        ).first()
        
        if not contact:
            raise ValueError("Contact not found")
        
        # Get communication template if specified
        template = None
        if template_id:
            template = self.db.query(CommunicationTemplate).filter(
                CommunicationTemplate.id == template_id,
                CommunicationTemplate.company_id == user_id
            ).first()
        
        # Generate AI communication content
        ai_content = await self._generate_ai_communication_content(
            contact, communication_type, context, template
        )
        
        # Create communication record
        communication = Communication(
            company_id=user_id,
            contact_id=contact_id,
            opportunity_id=context.get('opportunity_id'),
            project_id=context.get('project_id'),
            communication_type=CommunicationType(communication_type),
            subject=ai_content['subject'],
            content=ai_content['content'],
            direction="outbound",
            ai_generated=True,
            ai_confidence_score=ai_content.get('confidence_score', 85.0),
            ai_suggestions=ai_content.get('suggestions', []),
            created_by=user_id
        )
        
        self.db.add(communication)
        self.db.commit()
        self.db.refresh(communication)
        
        return {
            'communication_id': communication.id,
            'subject': ai_content['subject'],
            'content': ai_content['content'],
            'ai_confidence': ai_content.get('confidence_score', 85.0),
            'suggestions': ai_content.get('suggestions', []),
            'next_steps': ai_content.get('next_steps', [])
        }
    
    async def _generate_ai_communication_content(
        self,
        contact: Contact,
        communication_type: str,
        context: Dict[str, Any],
        template: Optional[CommunicationTemplate] = None
    ) -> Dict[str, Any]:
        """Generate AI communication content"""
        
        # Build context for AI
        ai_context = {
            'contact_details': {
                'name': f"{contact.first_name} {contact.last_name}",
                'title': contact.title,
                'organization': contact.organization,
                'relationship_level': contact.relationship_level,
                'last_contact': contact.last_contact_date.isoformat() if contact.last_contact_date else None,
                'preferred_communication': contact.preferred_communication
            },
            'communication_type': communication_type,
            'context': context,
            'template': {
                'subject': template.subject_template if template else None,
                'content': template.content_template if template else None,
                'tone': template.tone if template else 'professional'
            } if template else None
        }
        
        # Get communication history for context
        recent_communications = self.db.query(Communication).filter(
            Communication.contact_id == contact.id,
            Communication.created_at >= datetime.now() - timedelta(days=90)
        ).order_by(Communication.created_at.desc()).limit(5).all()
        
        if recent_communications:
            ai_context['recent_communications'] = [
                {
                    'date': comm.created_at.isoformat(),
                    'type': comm.communication_type.value,
                    'subject': comm.subject,
                    'direction': comm.direction
                }
                for comm in recent_communications
            ]
        
        prompt = self._create_communication_prompt(ai_context)
        
        try:
            response = await self.ai_service.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": self._get_communication_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=1500
            )
            
            ai_response = response.choices[0].message.content
            return self._parse_ai_communication_response(ai_response)
            
        except Exception as e:
            print(f"AI communication generation failed: {e}")
            return self._generate_fallback_communication(communication_type, contact, context)
    
    async def generate_nda_document(
        self,
        user_id: int,
        contact_id: int,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate customized NDA document"""
        
        contact = self.db.query(Contact).filter(
            Contact.id == contact_id,
            Contact.company_id == user_id
        ).first()
        
        if not contact:
            raise ValueError("Contact not found")
        
        # Get user/company information
        from models.user import User
        user = self.db.query(User).filter(User.id == user_id).first()
        
        # AI-generate NDA content
        nda_content = await self._generate_ai_nda_content(contact, user, context)
        
        # Create document record
        document = CommunicationDocument(
            company_id=user_id,
            contact_id=contact_id,
            document_name=f"NDA_{contact.organization}_{datetime.now().strftime('%Y%m%d')}",
            document_type=DocumentType.NDA,
            file_path=f"documents/ndas/{contact.organization}_nda.pdf",  # Would generate actual PDF
            file_format="pdf",
            description=f"Non-Disclosure Agreement with {contact.organization}",
            requires_signature=True,
            confidentiality_level="confidential",
            ai_extracted_data=nda_content.get('key_terms', {}),
            created_by=user_id
        )
        
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        
        return {
            'document_id': document.id,
            'document_name': document.document_name,
            'content': nda_content['content'],
            'key_terms': nda_content.get('key_terms', {}),
            'ai_confidence': nda_content.get('confidence_score', 85.0)
        }
    
    async def request_teaming_confirmation(
        self,
        user_id: int,
        partner_contact_id: int,
        opportunity_id: int,
        teaming_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Request teaming arrangement confirmation"""
        
        contact = self.db.query(Contact).filter(
            Contact.id == partner_contact_id,
            Contact.company_id == user_id
        ).first()
        
        opportunity = self.db.query(Opportunity).filter(
            Opportunity.id == opportunity_id
        ).first()
        
        if not contact or not opportunity:
            raise ValueError("Contact or opportunity not found")
        
        # Generate teaming confirmation request
        context = {
            'opportunity_details': {
                'title': opportunity.title,
                'agency': opportunity.agency,
                'due_date': opportunity.response_deadline.isoformat() if opportunity.response_deadline else None,
                'notice_id': opportunity.notice_id
            },
            'teaming_details': teaming_details,
            'purpose': 'teaming_confirmation'
        }
        
        communication_result = await self.create_ai_communication(
            user_id, partner_contact_id, "email", context
        )
        
        # Generate teaming agreement document
        agreement_content = await self._generate_teaming_agreement(contact, opportunity, teaming_details)
        
        document = CommunicationDocument(
            company_id=user_id,
            contact_id=partner_contact_id,
            communication_id=communication_result['communication_id'],
            document_name=f"Teaming_Agreement_{opportunity.notice_id}_{contact.organization}",
            document_type=DocumentType.TEAMING_AGREEMENT,
            file_path=f"documents/teaming/{opportunity.notice_id}_{contact.organization}.pdf",
            file_format="pdf",
            description=f"Teaming agreement for {opportunity.title}",
            requires_signature=True,
            ai_extracted_data=agreement_content.get('key_terms', {}),
            created_by=user_id
        )
        
        self.db.add(document)
        self.db.commit()
        
        return {
            **communication_result,
            'teaming_document_id': document.id,
            'agreement_terms': agreement_content.get('key_terms', {})
        }
    
    async def request_pricing_quote(
        self,
        user_id: int,
        vendor_contact_id: int,
        quote_requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Request pricing quote from vendor/subcontractor"""
        
        contact = self.db.query(Contact).filter(
            Contact.id == vendor_contact_id,
            Contact.company_id == user_id
        ).first()
        
        if not contact:
            raise ValueError("Contact not found")
        
        # Generate quote request
        context = {
            'quote_requirements': quote_requirements,
            'purpose': 'pricing_quote_request'
        }
        
        communication_result = await self.create_ai_communication(
            user_id, vendor_contact_id, "email", context
        )
        
        # Create quote request document
        quote_doc = await self._generate_quote_request_document(contact, quote_requirements)
        
        document = CommunicationDocument(
            company_id=user_id,
            contact_id=vendor_contact_id,
            communication_id=communication_result['communication_id'],
            document_name=f"Quote_Request_{contact.organization}_{datetime.now().strftime('%Y%m%d')}",
            document_type=DocumentType.QUOTE,
            file_path=f"documents/quotes/request_{contact.organization}.pdf",
            file_format="pdf",
            description=f"Quote request to {contact.organization}",
            ai_extracted_data=quote_doc.get('requirements', {}),
            created_by=user_id
        )
        
        self.db.add(document)
        self.db.commit()
        
        return {
            **communication_result,
            'quote_document_id': document.id,
            'quote_requirements': quote_doc.get('requirements', {})
        }
    
    async def schedule_meeting(
        self,
        user_id: int,
        contact_ids: List[int],
        meeting_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Schedule meeting with AI-generated invitation"""
        
        # Get all contacts
        contacts = self.db.query(Contact).filter(
            Contact.id.in_(contact_ids),
            Contact.company_id == user_id
        ).all()
        
        if len(contacts) != len(contact_ids):
            raise ValueError("Some contacts not found")
        
        # Create meeting schedule
        meeting = MeetingSchedule(
            company_id=user_id,
            title=meeting_details['title'],
            description=meeting_details.get('description'),
            meeting_type=meeting_details.get('type', 'video'),
            scheduled_date=datetime.fromisoformat(meeting_details['scheduled_date']),
            duration_minutes=meeting_details.get('duration_minutes', 60),
            location=meeting_details.get('location'),
            meeting_url=meeting_details.get('meeting_url'),
            participants=[
                {
                    'contact_id': contact.id,
                    'name': f"{contact.first_name} {contact.last_name}",
                    'email': contact.email,
                    'role': 'participant'
                }
                for contact in contacts
            ],
            agenda_items=meeting_details.get('agenda_items', []),
            organizer_id=user_id,
            created_by=user_id
        )
        
        self.db.add(meeting)
        self.db.commit()
        self.db.refresh(meeting)
        
        # Generate and send meeting invitations
        invitations_sent = []
        
        for contact in contacts:
            invitation_context = {
                'meeting_details': {
                    'title': meeting.title,
                    'date': meeting.scheduled_date.isoformat(),
                    'duration': meeting.duration_minutes,
                    'location': meeting.location or meeting.meeting_url,
                    'agenda': meeting.agenda_items or []
                },
                'purpose': 'meeting_invitation'
            }
            
            try:
                invitation_result = await self.create_ai_communication(
                    user_id, contact.id, "email", invitation_context
                )
                invitations_sent.append({
                    'contact_id': contact.id,
                    'communication_id': invitation_result['communication_id'],
                    'status': 'sent'
                })
            except Exception as e:
                invitations_sent.append({
                    'contact_id': contact.id,
                    'status': 'failed',
                    'error': str(e)
                })
        
        return {
            'meeting_id': meeting.id,
            'meeting_details': {
                'title': meeting.title,
                'scheduled_date': meeting.scheduled_date.isoformat(),
                'duration_minutes': meeting.duration_minutes,
                'participants': len(contacts)
            },
            'invitations_sent': invitations_sent
        }
    
    async def analyze_communication_sentiment(
        self,
        communication_id: int,
        user_id: int
    ) -> Dict[str, Any]:
        """Analyze communication sentiment and extract insights"""
        
        communication = self.db.query(Communication).filter(
            Communication.id == communication_id,
            Communication.company_id == user_id
        ).first()
        
        if not communication:
            raise ValueError("Communication not found")
        
        # AI sentiment analysis
        analysis_result = await self._ai_analyze_communication(communication)
        
        # Update communication with analysis
        communication.sentiment_score = analysis_result['sentiment_score']
        communication.key_topics = analysis_result['key_topics']
        communication.action_items = analysis_result['action_items']
        
        self.db.commit()
        
        return {
            'communication_id': communication_id,
            'sentiment_score': analysis_result['sentiment_score'],
            'sentiment_label': analysis_result['sentiment_label'],
            'key_topics': analysis_result['key_topics'],
            'action_items': analysis_result['action_items'],
            'urgency_level': analysis_result['urgency_level'],
            'response_required': analysis_result['response_required']
        }
    
    async def generate_follow_up_sequence(
        self,
        user_id: int,
        contact_id: int,
        opportunity_id: Optional[int] = None,
        sequence_type: str = "general"
    ) -> Dict[str, Any]:
        """Generate AI-powered follow-up sequence"""
        
        contact = self.db.query(Contact).filter(
            Contact.id == contact_id,
            Contact.company_id == user_id
        ).first()
        
        if not contact:
            raise ValueError("Contact not found")
        
        # Analyze communication history for follow-up strategy
        follow_up_strategy = await self._analyze_follow_up_strategy(contact, opportunity_id)
        
        # Generate follow-up sequence
        sequence = await self._generate_ai_follow_up_sequence(contact, follow_up_strategy, sequence_type)
        
        # Create scheduled communications
        scheduled_communications = []
        
        for i, follow_up in enumerate(sequence['follow_ups']):
            scheduled_date = datetime.now() + timedelta(days=follow_up['days_offset'])
            
            communication = Communication(
                company_id=user_id,
                contact_id=contact_id,
                opportunity_id=opportunity_id,
                communication_type=CommunicationType.EMAIL,
                subject=follow_up['subject'],
                content=follow_up['content'],
                scheduled_date=scheduled_date,
                direction="outbound",
                ai_generated=True,
                ai_confidence_score=follow_up.get('confidence_score', 80.0),
                follow_up_required=i < len(sequence['follow_ups']) - 1,
                created_by=user_id
            )
            
            self.db.add(communication)
            scheduled_communications.append(communication)
        
        self.db.commit()
        
        return {
            'sequence_type': sequence_type,
            'total_follow_ups': len(scheduled_communications),
            'sequence_duration_days': sequence['total_duration_days'],
            'follow_ups': [
                {
                    'communication_id': comm.id,
                    'scheduled_date': comm.scheduled_date.isoformat(),
                    'subject': comm.subject
                }
                for comm in scheduled_communications
            ],
            'success_probability': sequence['success_probability']
        }
    
    def _get_communication_system_prompt(self) -> str:
        """System prompt for AI communication generation"""
        return """You are an expert business development and communication specialist for government contracting.

Generate professional, compelling communications that:
1. Maintain appropriate tone for government/business context
2. Are clear, concise, and action-oriented
3. Build relationships and trust
4. Include relevant details and next steps
5. Follow professional email etiquette

Respond in JSON format:
{
    "subject": "Professional subject line",
    "content": "Full email content with proper formatting",
    "confidence_score": 85,
    "suggestions": ["suggestion1", "suggestion2"],
    "next_steps": ["step1", "step2"]
}"""
    
    def _create_communication_prompt(self, context: Dict) -> str:
        """Create communication generation prompt"""
        return f"""Generate a professional communication:

CONTACT DETAILS: {json.dumps(context['contact_details'], indent=2)}

COMMUNICATION TYPE: {context['communication_type']}

CONTEXT: {json.dumps(context['context'], indent=2)}

TEMPLATE: {json.dumps(context.get('template'), indent=2) if context.get('template') else 'None'}

RECENT HISTORY: {json.dumps(context.get('recent_communications', []), indent=2)}

Create a professional, relationship-building communication that advances business objectives while maintaining appropriate tone and etiquette."""
    
    def _parse_ai_communication_response(self, response: str) -> Dict[str, Any]:
        """Parse AI communication response"""
        try:
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            else:
                json_str = response
            
            return json.loads(json_str)
        except:
            return {
                'subject': 'Follow-up Communication',
                'content': response[:1000] if len(response) > 1000 else response,
                'confidence_score': 50,
                'suggestions': [],
                'next_steps': []
            }
    
    def _generate_fallback_communication(
        self,
        communication_type: str,
        contact: Contact,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate fallback communication when AI fails"""
        
        templates = {
            'email': {
                'subject': f"Following up - {context.get('subject', 'Opportunity Discussion')}",
                'content': f"""Dear {contact.first_name},

I hope this email finds you well. I wanted to follow up on our recent discussion regarding {context.get('topic', 'the opportunity we discussed')}.

{context.get('main_message', 'I would appreciate the opportunity to discuss this further at your convenience.')}

Please let me know if you have any questions or if there would be a good time to connect.

Best regards,
[Your Name]"""
            }
        }
        
        template = templates.get(communication_type, templates['email'])
        
        return {
            'subject': template['subject'],
            'content': template['content'],
            'confidence_score': 60,
            'suggestions': ['Manual review recommended'],
            'next_steps': ['Send communication', 'Schedule follow-up']
        }