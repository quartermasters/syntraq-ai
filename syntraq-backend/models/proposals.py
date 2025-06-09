"""
© 2025 Aliff Capital, Quartermasters FZC, and SkillvenzA. All rights reserved.

Syntraq AI - PME (Proposal Management Engine) Models
A Joint Innovation by Aliff Capital, Quartermasters FZC, and SkillvenzA
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, JSON, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()

class ProposalStatus(enum.Enum):
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    READY = "ready"
    SUBMITTED = "submitted"
    AWARDED = "awarded"
    NOT_AWARDED = "not_awarded"
    CANCELLED = "cancelled"

class VolumeType(enum.Enum):
    TECHNICAL = "technical"
    MANAGEMENT = "management"
    PAST_PERFORMANCE = "past_performance"
    PRICING = "pricing"
    ADMINISTRATIVE = "administrative"

class ComplianceStatus(enum.Enum):
    NOT_CHECKED = "not_checked"
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    NEEDS_REVIEW = "needs_review"

class ReadinessGate(enum.Enum):
    OPPORTUNITY_ANALYSIS = "opportunity_analysis"
    FINANCIAL_APPROVAL = "financial_approval"
    RESOURCE_ALLOCATION = "resource_allocation"
    TEAMING_CONFIRMED = "teaming_confirmed"
    COMPLIANCE_VERIFIED = "compliance_verified"
    CONTENT_COMPLETE = "content_complete"
    QUALITY_REVIEWED = "quality_reviewed"
    EXECUTIVE_APPROVED = "executive_approved"

class Proposal(Base):
    __tablename__ = "proposals"
    
    id = Column(Integer, primary_key=True, index=True)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"))
    project_id = Column(Integer, ForeignKey("financial_projects.id"), nullable=True)
    delivery_plan_id = Column(Integer, ForeignKey("delivery_plans.id"), nullable=True)
    
    # Proposal identification
    proposal_number = Column(String, unique=True, index=True)
    proposal_title = Column(String)
    solicitation_number = Column(String, index=True)
    
    # Timeline
    submission_deadline = Column(DateTime)
    started_date = Column(DateTime, default=datetime.utcnow)
    submitted_date = Column(DateTime, nullable=True)
    
    # Status and progress
    status = Column(Enum(ProposalStatus), default=ProposalStatus.DRAFT)
    overall_progress_percentage = Column(Float, default=0.0)
    
    # Proposal structure
    proposal_sections = Column(JSON)  # Section structure based on RFP
    compliance_matrix = Column(JSON)  # Compliance tracking matrix
    evaluation_criteria = Column(JSON)  # How proposal will be evaluated
    
    # Team and assignments
    proposal_manager = Column(Integer, ForeignKey("users.id"))
    capture_manager = Column(Integer, ForeignKey("users.id"), nullable=True)
    technical_lead = Column(Integer, ForeignKey("users.id"), nullable=True)
    pricing_lead = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Collaboration
    team_members = Column(JSON)  # List of team members and roles
    external_contributors = Column(JSON)  # Subcontractor/partner contributors
    
    # Financial summary
    proposed_price = Column(Float, nullable=True)
    estimated_cost = Column(Float, nullable=True)
    margin_percentage = Column(Float, nullable=True)
    
    # Strategy and positioning
    win_strategy = Column(Text, nullable=True)
    value_proposition = Column(Text, nullable=True)
    discriminators = Column(JSON)  # Key differentiators
    
    # Risk assessment
    proposal_risks = Column(JSON)  # Identified risks and mitigations
    risk_score = Column(Float, nullable=True)
    
    # Quality and compliance
    compliance_score = Column(Float, nullable=True)
    quality_score = Column(Float, nullable=True)
    readiness_gates_status = Column(JSON)  # Status of each readiness gate
    
    # AI insights
    ai_recommendations = Column(JSON)  # AI-generated recommendations
    competitive_analysis = Column(JSON)  # AI competitive insights
    win_probability = Column(Float, nullable=True)  # AI-predicted win probability
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    volumes = relationship("ProposalVolume", back_populates="proposal", cascade="all, delete-orphan")
    sections = relationship("ProposalSection", back_populates="proposal", cascade="all, delete-orphan")
    reviews = relationship("ProposalReview", back_populates="proposal", cascade="all, delete-orphan")
    submissions = relationship("ProposalSubmission", back_populates="proposal", cascade="all, delete-orphan")

class ProposalVolume(Base):
    __tablename__ = "proposal_volumes"
    
    id = Column(Integer, primary_key=True, index=True)
    proposal_id = Column(Integer, ForeignKey("proposals.id"))
    
    # Volume details
    volume_name = Column(String)
    volume_type = Column(Enum(VolumeType))
    volume_number = Column(Integer)
    description = Column(Text, nullable=True)
    
    # Content management
    page_limit = Column(Integer, nullable=True)
    current_page_count = Column(Integer, default=0)
    word_limit = Column(Integer, nullable=True)
    current_word_count = Column(Integer, default=0)
    
    # Status and progress
    completion_percentage = Column(Float, default=0.0)
    assigned_lead = Column(Integer, ForeignKey("users.id"), nullable=True)
    due_date = Column(DateTime, nullable=True)
    
    # Content structure
    required_sections = Column(JSON)  # Sections required in this volume
    optional_sections = Column(JSON)  # Optional sections
    
    # Quality tracking
    draft_complete = Column(Boolean, default=False)
    review_complete = Column(Boolean, default=False)
    final_complete = Column(Boolean, default=False)
    
    # File management
    file_path = Column(String, nullable=True)
    file_version = Column(String, default="1.0")
    last_modified = Column(DateTime, default=datetime.utcnow)
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    proposal = relationship("Proposal", back_populates="volumes")
    sections = relationship("ProposalSection", back_populates="volume")

class ProposalSection(Base):
    __tablename__ = "proposal_sections"
    
    id = Column(Integer, primary_key=True, index=True)
    proposal_id = Column(Integer, ForeignKey("proposals.id"))
    volume_id = Column(Integer, ForeignKey("proposal_volumes.id"), nullable=True)
    
    # Section identification
    section_number = Column(String)
    section_title = Column(String)
    section_type = Column(String)  # executive_summary, technical_approach, etc.
    
    # Content management
    content = Column(Text, nullable=True)
    content_outline = Column(JSON)  # Section outline/structure
    word_count = Column(Integer, default=0)
    page_count = Column(Integer, default=0)
    
    # Requirements and compliance
    requirements = Column(JSON)  # Specific requirements for this section
    compliance_status = Column(Enum(ComplianceStatus), default=ComplianceStatus.NOT_CHECKED)
    compliance_notes = Column(Text, nullable=True)
    
    # Assignment and progress
    assigned_writer = Column(Integer, ForeignKey("users.id"), nullable=True)
    assigned_reviewer = Column(Integer, ForeignKey("users.id"), nullable=True)
    completion_percentage = Column(Float, default=0.0)
    
    # Status tracking
    outline_complete = Column(Boolean, default=False)
    draft_complete = Column(Boolean, default=False)
    review_complete = Column(Boolean, default=False)
    final_complete = Column(Boolean, default=False)
    
    # Quality metrics
    quality_score = Column(Float, nullable=True)
    readability_score = Column(Float, nullable=True)
    technical_accuracy = Column(Float, nullable=True)
    
    # AI assistance
    ai_generated_content = Column(Boolean, default=False)
    ai_suggestions = Column(JSON)  # AI content suggestions
    ai_quality_analysis = Column(JSON)  # AI quality assessment
    
    # Dependencies
    depends_on_sections = Column(JSON)  # Other sections this depends on
    blocks_sections = Column(JSON)  # Sections that depend on this one
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    proposal = relationship("Proposal", back_populates="sections")
    volume = relationship("ProposalVolume", back_populates="sections")

class ProposalReview(Base):
    __tablename__ = "proposal_reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    proposal_id = Column(Integer, ForeignKey("proposals.id"))
    section_id = Column(Integer, ForeignKey("proposal_sections.id"), nullable=True)
    
    # Review details
    review_type = Column(String)  # pink_team, red_team, gold_team, compliance, executive
    review_name = Column(String)
    review_date = Column(DateTime)
    
    # Reviewer information
    reviewer_id = Column(Integer, ForeignKey("users.id"))
    reviewer_role = Column(String)  # internal, external, subject_matter_expert
    
    # Review scope
    sections_reviewed = Column(JSON)  # Sections covered in this review
    review_criteria = Column(JSON)  # What was evaluated
    
    # Findings and scores
    overall_score = Column(Float, nullable=True)  # 1-10 scale
    strengths = Column(JSON)  # List of strengths identified
    weaknesses = Column(JSON)  # List of weaknesses/issues
    recommendations = Column(JSON)  # Specific recommendations
    
    # Detailed feedback
    technical_score = Column(Float, nullable=True)
    management_score = Column(Float, nullable=True)
    pricing_score = Column(Float, nullable=True)
    compliance_score = Column(Float, nullable=True)
    
    # Comments and notes
    general_comments = Column(Text, nullable=True)
    critical_issues = Column(JSON)  # Critical issues that must be addressed
    
    # Action items
    action_items = Column(JSON)  # Specific actions to take
    follow_up_required = Column(Boolean, default=False)
    follow_up_date = Column(DateTime, nullable=True)
    
    # Status
    review_status = Column(String, default="in_progress")  # in_progress, completed, cancelled
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    proposal = relationship("Proposal", back_populates="reviews")

class ProposalSubmission(Base):
    __tablename__ = "proposal_submissions"
    
    id = Column(Integer, primary_key=True, index=True)
    proposal_id = Column(Integer, ForeignKey("proposals.id"))
    
    # Submission details
    submission_date = Column(DateTime)
    submission_method = Column(String)  # email, portal, hand_delivery, mail
    confirmation_number = Column(String, nullable=True)
    
    # Files and packages
    submitted_files = Column(JSON)  # List of files submitted
    package_size_mb = Column(Float, nullable=True)
    file_formats = Column(JSON)  # Formats of submitted files
    
    # Submission validation
    all_volumes_included = Column(Boolean, default=False)
    all_requirements_met = Column(Boolean, default=False)
    submission_complete = Column(Boolean, default=False)
    
    # Delivery confirmation
    delivered_successfully = Column(Boolean, default=False)
    delivery_confirmation = Column(String, nullable=True)
    delivery_receipt = Column(String, nullable=True)
    
    # Post-submission tracking
    acknowledgment_received = Column(Boolean, default=False)
    acknowledgment_date = Column(DateTime, nullable=True)
    questions_received = Column(Boolean, default=False)
    
    # Results tracking
    award_notification_date = Column(DateTime, nullable=True)
    award_result = Column(String, nullable=True)  # awarded, not_awarded, cancelled
    award_amount = Column(Float, nullable=True)
    
    # Feedback and lessons learned
    client_feedback = Column(Text, nullable=True)
    lessons_learned = Column(JSON)
    win_loss_analysis = Column(JSON)
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    submitted_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    proposal = relationship("Proposal", back_populates="submissions")

class ProposalTemplate(Base):
    __tablename__ = "proposal_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("users.id"))
    
    # Template details
    template_name = Column(String)
    template_type = Column(String)  # rfp_response, capability_statement, etc.
    description = Column(Text, nullable=True)
    
    # Template structure
    sections_template = Column(JSON)  # Standard sections structure
    content_templates = Column(JSON)  # Content templates for sections
    
    # Usage context
    applicable_naics = Column(JSON)  # NAICS codes this applies to
    contract_types = Column(JSON)  # Contract types (FFP, T&M, etc.)
    agencies = Column(JSON)  # Government agencies
    
    # Performance tracking
    usage_count = Column(Integer, default=0)
    success_rate = Column(Float, nullable=True)
    avg_win_rate = Column(Float, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    version = Column(String, default="1.0")
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"))

class ProposalLibrary(Base):
    __tablename__ = "proposal_library"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("users.id"))
    
    # Content details
    content_title = Column(String)
    content_type = Column(String)  # boilerplate, case_study, technical_description, etc.
    category = Column(String)  # company_info, past_performance, technical_capabilities
    
    # Content
    content_text = Column(Text)
    content_metadata = Column(JSON)  # Tags, keywords, usage notes
    
    # Applicability
    applicable_sections = Column(JSON)  # Which proposal sections this fits
    keywords = Column(JSON)  # Search keywords
    tags = Column(JSON)  # Organizational tags
    
    # Usage tracking
    usage_count = Column(Integer, default=0)
    last_used_date = Column(DateTime, nullable=True)
    success_rate = Column(Float, nullable=True)
    
    # Quality metrics
    quality_rating = Column(Float, nullable=True)
    reviewer_approved = Column(Boolean, default=False)
    approval_date = Column(DateTime, nullable=True)
    
    # Versioning
    version = Column(String, default="1.0")
    is_current_version = Column(Boolean, default=True)
    superseded_by = Column(Integer, ForeignKey("proposal_library.id"), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"))