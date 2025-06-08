from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, JSON, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()

class CommunicationType(enum.Enum):
    EMAIL = "email"
    PHONE_CALL = "phone_call"
    MEETING = "meeting"
    DOCUMENT = "document"
    PROPOSAL_SUBMISSION = "proposal_submission"
    QUOTE_REQUEST = "quote_request"
    NDA_REQUEST = "nda_request"
    TEAM_CONFIRMATION = "team_confirmation"

class CommunicationStatus(enum.Enum):
    DRAFT = "draft"
    SENT = "sent"
    RECEIVED = "received"
    RESPONDED = "responded"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class ContactType(enum.Enum):
    CLIENT = "client"
    PARTNER = "partner"
    SUBCONTRACTOR = "subcontractor"
    VENDOR = "vendor"
    TEAM_MEMBER = "team_member"
    GOVERNMENT_OFFICIAL = "government_official"

class DocumentType(enum.Enum):
    NDA = "nda"
    TEAMING_AGREEMENT = "teaming_agreement"
    QUOTE = "quote"
    PROPOSAL = "proposal"
    CONTRACT = "contract"
    CAPABILITY_STATEMENT = "capability_statement"
    PAST_PERFORMANCE = "past_performance"
    COMPLIANCE_DOCUMENT = "compliance_document"

class Contact(Base):
    __tablename__ = "contacts"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("users.id"))
    
    # Basic information
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, index=True)
    phone = Column(String, nullable=True)
    title = Column(String, nullable=True)
    
    # Organization details
    organization = Column(String)
    department = Column(String, nullable=True)
    contact_type = Column(Enum(ContactType))
    
    # Address
    address_line1 = Column(String, nullable=True)
    address_line2 = Column(String, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    zip_code = Column(String, nullable=True)
    country = Column(String, default="USA")
    
    # Professional details
    linkedin_url = Column(String, nullable=True)
    website = Column(String, nullable=True)
    bio = Column(Text, nullable=True)
    
    # Relationship management
    relationship_level = Column(String, default="new")  # new, warm, established, key
    last_contact_date = Column(DateTime, nullable=True)
    preferred_communication = Column(String, default="email")  # email, phone, in_person
    
    # Capabilities and interests
    specializations = Column(JSON)  # Areas of expertise
    certifications = Column(JSON)  # Professional certifications
    past_collaborations = Column(JSON)  # Previous work together
    
    # Engagement tracking
    engagement_score = Column(Float, default=0.0)  # 0-100 based on interactions
    response_rate = Column(Float, nullable=True)  # Average response rate
    avg_response_time_hours = Column(Float, nullable=True)
    
    # Notes and tags
    notes = Column(Text, nullable=True)
    tags = Column(JSON)  # Custom tags for organization
    
    # Privacy and compliance
    gdpr_consent = Column(Boolean, default=False)
    marketing_consent = Column(Boolean, default=False)
    nda_signed = Column(Boolean, default=False)
    nda_expiry_date = Column(DateTime, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_blacklisted = Column(Boolean, default=False)
    blacklist_reason = Column(String, nullable=True)
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    communications = relationship("Communication", back_populates="contact")
    documents = relationship("CommunicationDocument", back_populates="contact")

class Communication(Base):
    __tablename__ = "communications"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("users.id"))
    contact_id = Column(Integer, ForeignKey("contacts.id"))
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"), nullable=True)
    project_id = Column(Integer, ForeignKey("financial_projects.id"), nullable=True)
    
    # Communication details
    communication_type = Column(Enum(CommunicationType))
    subject = Column(String)
    content = Column(Text)
    
    # Timing
    scheduled_date = Column(DateTime, nullable=True)
    sent_date = Column(DateTime, nullable=True)
    received_date = Column(DateTime, nullable=True)
    
    # Status and tracking
    status = Column(Enum(CommunicationStatus), default=CommunicationStatus.DRAFT)
    priority = Column(String, default="medium")  # low, medium, high, urgent
    
    # Communication metadata
    direction = Column(String)  # inbound, outbound
    thread_id = Column(String, nullable=True)  # For tracking email threads
    reference_number = Column(String, nullable=True)  # Internal reference
    
    # Response tracking
    requires_response = Column(Boolean, default=False)
    response_deadline = Column(DateTime, nullable=True)
    responded_at = Column(DateTime, nullable=True)
    response_id = Column(Integer, ForeignKey("communications.id"), nullable=True)
    
    # Content analysis
    sentiment_score = Column(Float, nullable=True)  # AI sentiment analysis
    key_topics = Column(JSON)  # AI-extracted topics
    action_items = Column(JSON)  # AI-identified action items
    
    # Follow-up
    follow_up_required = Column(Boolean, default=False)
    follow_up_date = Column(DateTime, nullable=True)
    follow_up_notes = Column(Text, nullable=True)
    
    # Integration
    external_message_id = Column(String, nullable=True)  # Email message ID
    external_thread_id = Column(String, nullable=True)  # Email thread ID
    integration_source = Column(String, nullable=True)  # outlook, gmail, etc.
    
    # AI enhancement
    ai_generated = Column(Boolean, default=False)
    ai_confidence_score = Column(Float, nullable=True)
    ai_suggestions = Column(JSON)  # AI improvement suggestions
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    contact = relationship("Contact", back_populates="communications")
    attachments = relationship("CommunicationAttachment", back_populates="communication")
    responses = relationship("Communication", remote_side=[id])

class CommunicationTemplate(Base):
    __tablename__ = "communication_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("users.id"))
    
    # Template details
    template_name = Column(String)
    template_type = Column(Enum(CommunicationType))
    category = Column(String)  # business_development, proposal, follow_up, etc.
    
    # Content
    subject_template = Column(String)
    content_template = Column(Text)
    variables = Column(JSON)  # Template variables and their descriptions
    
    # Usage context
    use_case = Column(String)  # When to use this template
    target_audience = Column(String)  # Who this is for
    tone = Column(String)  # formal, informal, friendly, professional
    
    # Personalization
    personalization_fields = Column(JSON)  # Fields for AI personalization
    ai_enhancement_enabled = Column(Boolean, default=True)
    
    # Performance tracking
    usage_count = Column(Integer, default=0)
    success_rate = Column(Float, nullable=True)  # Response rate for this template
    avg_response_time = Column(Float, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"))

class CommunicationDocument(Base):
    __tablename__ = "communication_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("users.id"))
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=True)
    communication_id = Column(Integer, ForeignKey("communications.id"), nullable=True)
    
    # Document details
    document_name = Column(String)
    document_type = Column(Enum(DocumentType))
    file_path = Column(String)
    file_size = Column(Integer, nullable=True)
    file_format = Column(String)  # pdf, docx, etc.
    
    # Document metadata
    version = Column(String, default="1.0")
    status = Column(String, default="draft")  # draft, final, signed, expired
    description = Column(Text, nullable=True)
    
    # Legal and compliance
    requires_signature = Column(Boolean, default=False)
    signed_date = Column(DateTime, nullable=True)
    signed_by = Column(String, nullable=True)
    expiry_date = Column(DateTime, nullable=True)
    
    # Access control
    confidentiality_level = Column(String, default="internal")  # public, internal, confidential, restricted
    access_permissions = Column(JSON)  # Who can access this document
    
    # Workflow
    approval_required = Column(Boolean, default=False)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    
    # AI processing
    ai_extracted_data = Column(JSON)  # AI-extracted key information
    ai_risk_assessment = Column(JSON)  # AI risk analysis
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    contact = relationship("Contact", back_populates="documents")

class CommunicationAttachment(Base):
    __tablename__ = "communication_attachments"
    
    id = Column(Integer, primary_key=True, index=True)
    communication_id = Column(Integer, ForeignKey("communications.id"))
    
    # File details
    filename = Column(String)
    file_path = Column(String)
    file_size = Column(Integer)
    content_type = Column(String)
    
    # Metadata
    description = Column(String, nullable=True)
    is_inline = Column(Boolean, default=False)
    
    # Tracking
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    communication = relationship("Communication", back_populates="attachments")

class CommunicationCampaign(Base):
    __tablename__ = "communication_campaigns"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("users.id"))
    
    # Campaign details
    campaign_name = Column(String)
    campaign_type = Column(String)  # outreach, follow_up, nurture
    description = Column(Text, nullable=True)
    
    # Target audience
    target_contact_type = Column(Enum(ContactType))
    target_criteria = Column(JSON)  # Filtering criteria for contacts
    
    # Campaign timeline
    start_date = Column(DateTime)
    end_date = Column(DateTime, nullable=True)
    
    # Content
    template_id = Column(Integer, ForeignKey("communication_templates.id"), nullable=True)
    message_variants = Column(JSON)  # A/B test variants
    
    # Automation settings
    auto_send = Column(Boolean, default=False)
    send_interval_hours = Column(Integer, nullable=True)
    max_contacts_per_day = Column(Integer, nullable=True)
    
    # Performance tracking
    total_sent = Column(Integer, default=0)
    total_delivered = Column(Integer, default=0)
    total_opened = Column(Integer, default=0)
    total_responded = Column(Integer, default=0)
    
    # Status
    status = Column(String, default="draft")  # draft, active, paused, completed
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"))

class CommunicationRule(Base):
    __tablename__ = "communication_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("users.id"))
    
    # Rule details
    rule_name = Column(String)
    rule_type = Column(String)  # auto_respond, follow_up, escalation, tagging
    description = Column(Text, nullable=True)
    
    # Trigger conditions
    trigger_conditions = Column(JSON)  # When this rule should fire
    
    # Actions
    actions = Column(JSON)  # What actions to take
    
    # Settings
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=1)  # Rule execution priority
    
    # Performance
    execution_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"))

class MeetingSchedule(Base):
    __tablename__ = "meeting_schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("users.id"))
    communication_id = Column(Integer, ForeignKey("communications.id"), nullable=True)
    
    # Meeting details
    title = Column(String)
    description = Column(Text, nullable=True)
    meeting_type = Column(String)  # call, video, in_person
    
    # Scheduling
    scheduled_date = Column(DateTime)
    duration_minutes = Column(Integer, default=60)
    timezone = Column(String, default="UTC")
    
    # Location/Access
    location = Column(String, nullable=True)  # Physical address or meeting URL
    meeting_url = Column(String, nullable=True)  # Video conference link
    dial_in_info = Column(JSON, nullable=True)  # Phone dial-in details
    
    # Participants
    participants = Column(JSON)  # List of participants with roles
    organizer_id = Column(Integer, ForeignKey("users.id"))
    
    # Agenda and preparation
    agenda_items = Column(JSON)  # Meeting agenda
    preparation_notes = Column(Text, nullable=True)
    pre_meeting_materials = Column(JSON)  # Documents to review
    
    # Status and tracking
    status = Column(String, default="scheduled")  # scheduled, confirmed, completed, cancelled
    confirmation_sent = Column(Boolean, default=False)
    reminder_sent = Column(Boolean, default=False)
    
    # Follow-up
    meeting_notes = Column(Text, nullable=True)
    action_items = Column(JSON, nullable=True)
    follow_up_required = Column(Boolean, default=False)
    next_meeting_date = Column(DateTime, nullable=True)
    
    # Integration
    external_calendar_id = Column(String, nullable=True)  # Calendar system integration
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"))