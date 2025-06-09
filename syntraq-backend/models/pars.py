"""
© 2025 Aliff Capital, Quartermasters FZC, and SkillvenzA. All rights reserved.

Syntraq AI - PARS (Post-Award Readiness Suite) Models
A Joint Innovation by Aliff Capital, Quartermasters FZC, and SkillvenzA
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, JSON, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()

class ContractStatus(enum.Enum):
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    NEGOTIATING = "negotiating"
    EXECUTED = "executed"
    ACTIVE = "active"
    COMPLETED = "completed"
    TERMINATED = "terminated"

class DeliverableStatus(enum.Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    DELIVERED = "delivered"
    REJECTED = "rejected"

class RiskLevel(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ComplianceStatus(enum.Enum):
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    NEEDS_REVIEW = "needs_review"
    PENDING_APPROVAL = "pending_approval"

class TransitionPhase(enum.Enum):
    PRE_AWARD = "pre_award"
    KICK_OFF = "kick_off"
    MOBILIZATION = "mobilization"
    EXECUTION = "execution"
    CLOSE_OUT = "close_out"

class Contract(Base):
    __tablename__ = "contracts"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("users.id"))
    proposal_id = Column(Integer, ForeignKey("proposals.id"), nullable=True)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"), nullable=True)
    
    # Contract identification
    contract_number = Column(String, unique=True, index=True)
    contract_title = Column(String)
    contracting_agency = Column(String)
    contracting_officer = Column(String)
    
    # Contract details
    contract_type = Column(String)  # FFP, T&M, CPFF, etc.
    contract_value = Column(Float)
    base_period_months = Column(Integer)
    option_periods = Column(JSON)  # Array of option period details
    
    # Timeline
    award_date = Column(DateTime, nullable=True)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    current_period_end = Column(DateTime, nullable=True)
    
    # Status and performance
    status = Column(Enum(ContractStatus), default=ContractStatus.DRAFT)
    performance_rating = Column(String, nullable=True)  # Excellent, Very Good, Satisfactory, etc.
    
    # Financial tracking
    total_obligated = Column(Float, default=0.0)
    total_invoiced = Column(Float, default=0.0)
    total_paid = Column(Float, default=0.0)
    remaining_funds = Column(Float, default=0.0)
    
    # Key personnel and contacts
    program_manager = Column(Integer, ForeignKey("users.id"), nullable=True)
    contract_administrator = Column(Integer, ForeignKey("users.id"), nullable=True)
    government_pm = Column(String, nullable=True)
    government_cor = Column(String, nullable=True)  # Contracting Officer Representative
    
    # Documentation
    contract_documents = Column(JSON)  # List of contract documents
    amendments = Column(JSON)  # Contract modifications
    compliance_requirements = Column(JSON)  # Specific compliance items
    
    # Performance metrics
    schedule_performance = Column(Float, nullable=True)  # SPI
    cost_performance = Column(Float, nullable=True)  # CPI
    quality_metrics = Column(JSON)  # Quality measurements
    
    # Risk and issues
    current_risks = Column(JSON)  # Active risks
    open_issues = Column(JSON)  # Unresolved issues
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    deliverables = relationship("ContractDeliverable", back_populates="contract", cascade="all, delete-orphan")
    transitions = relationship("ContractTransition", back_populates="contract", cascade="all, delete-orphan")
    compliance_items = relationship("ComplianceItem", back_populates="contract", cascade="all, delete-orphan")

class ContractDeliverable(Base):
    __tablename__ = "contract_deliverables"
    
    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"))
    company_id = Column(Integer, ForeignKey("users.id"))
    
    # Deliverable identification
    deliverable_number = Column(String)
    deliverable_title = Column(String)
    deliverable_type = Column(String)  # report, software, service, data, etc.
    description = Column(Text)
    
    # Schedule
    due_date = Column(DateTime)
    submitted_date = Column(DateTime, nullable=True)
    approved_date = Column(DateTime, nullable=True)
    
    # Status and progress
    status = Column(Enum(DeliverableStatus), default=DeliverableStatus.NOT_STARTED)
    completion_percentage = Column(Float, default=0.0)
    
    # Requirements and acceptance
    acceptance_criteria = Column(JSON)  # What constitutes acceptance
    government_reviewer = Column(String, nullable=True)
    review_period_days = Column(Integer, default=10)
    
    # Quality and compliance
    quality_requirements = Column(JSON)  # Quality standards
    compliance_requirements = Column(JSON)  # Specific compliance needs
    inspection_required = Column(Boolean, default=False)
    
    # Delivery information
    delivery_method = Column(String, nullable=True)  # email, portal, physical, etc.
    delivery_address = Column(Text, nullable=True)
    file_format_requirements = Column(JSON)  # Required file formats
    
    # Dependencies
    depends_on_deliverables = Column(JSON)  # Other deliverables this depends on
    blocks_deliverables = Column(JSON)  # Deliverables that depend on this one
    
    # Resources and effort
    estimated_hours = Column(Float, nullable=True)
    actual_hours = Column(Float, nullable=True)
    assigned_team_members = Column(JSON)  # Team working on this
    
    # Feedback and revisions
    government_feedback = Column(Text, nullable=True)
    revision_history = Column(JSON)  # History of revisions
    current_version = Column(String, default="1.0")
    
    # Risk factors
    risk_level = Column(Enum(RiskLevel), default=RiskLevel.LOW)
    risk_factors = Column(JSON)  # Identified risks
    mitigation_actions = Column(JSON)  # Risk mitigation steps
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    assigned_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    contract = relationship("Contract", back_populates="deliverables")

class ContractTransition(Base):
    __tablename__ = "contract_transitions"
    
    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"))
    company_id = Column(Integer, ForeignKey("users.id"))
    
    # Transition details
    transition_name = Column(String)
    transition_phase = Column(Enum(TransitionPhase))
    description = Column(Text)
    
    # Timeline
    planned_start_date = Column(DateTime)
    planned_end_date = Column(DateTime)
    actual_start_date = Column(DateTime, nullable=True)
    actual_end_date = Column(DateTime, nullable=True)
    
    # Progress tracking
    completion_percentage = Column(Float, default=0.0)
    milestones = Column(JSON)  # Key milestones
    checklist_items = Column(JSON)  # Transition checklist
    
    # Stakeholders
    responsible_person = Column(Integer, ForeignKey("users.id"))
    government_poc = Column(String, nullable=True)
    participating_teams = Column(JSON)  # Teams involved in transition
    
    # Documentation and deliverables
    required_documents = Column(JSON)  # Documents needed for transition
    transition_deliverables = Column(JSON)  # Specific transition deliverables
    lessons_learned = Column(Text, nullable=True)
    
    # Risks and issues
    transition_risks = Column(JSON)  # Transition-specific risks
    issues_encountered = Column(JSON)  # Problems during transition
    mitigation_actions = Column(JSON)  # Actions taken to address issues
    
    # Success criteria
    success_criteria = Column(JSON)  # What defines successful transition
    performance_metrics = Column(JSON)  # Metrics to track
    
    # Status
    status = Column(String, default="planned")  # planned, in_progress, completed, delayed
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    contract = relationship("Contract", back_populates="transitions")

class ComplianceItem(Base):
    __tablename__ = "compliance_items"
    
    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"))
    company_id = Column(Integer, ForeignKey("users.id"))
    
    # Compliance requirement
    requirement_title = Column(String)
    requirement_source = Column(String)  # FAR, DFARS, Contract clause, etc.
    requirement_description = Column(Text)
    compliance_category = Column(String)  # financial, security, quality, reporting, etc.
    
    # Criticality and priority
    criticality_level = Column(Enum(RiskLevel), default=RiskLevel.MEDIUM)
    regulatory_requirement = Column(Boolean, default=False)  # Required by regulation
    
    # Status and tracking
    compliance_status = Column(Enum(ComplianceStatus), default=ComplianceStatus.NEEDS_REVIEW)
    last_review_date = Column(DateTime, nullable=True)
    next_review_date = Column(DateTime, nullable=True)
    review_frequency_days = Column(Integer, default=90)
    
    # Implementation
    implementation_approach = Column(Text, nullable=True)
    responsible_person = Column(Integer, ForeignKey("users.id"), nullable=True)
    implementation_date = Column(DateTime, nullable=True)
    
    # Evidence and documentation
    evidence_required = Column(JSON)  # What evidence is needed
    evidence_provided = Column(JSON)  # Evidence collected
    documentation_location = Column(String, nullable=True)
    
    # Monitoring and verification
    monitoring_method = Column(String, nullable=True)  # How compliance is monitored
    verification_method = Column(String, nullable=True)  # How compliance is verified
    last_verification_date = Column(DateTime, nullable=True)
    
    # Non-compliance handling
    non_compliance_risk = Column(Text, nullable=True)  # What happens if non-compliant
    corrective_actions = Column(JSON)  # Actions if non-compliant
    waivers_or_deviations = Column(JSON)  # Any approved waivers
    
    # Costs and resources
    compliance_cost = Column(Float, nullable=True)  # Cost to maintain compliance
    effort_required_hours = Column(Float, nullable=True)
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    contract = relationship("Contract", back_populates="compliance_items")

class PerformanceMetric(Base):
    __tablename__ = "performance_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"))
    company_id = Column(Integer, ForeignKey("users.id"))
    
    # Metric definition
    metric_name = Column(String)
    metric_category = Column(String)  # schedule, cost, quality, customer_satisfaction
    metric_description = Column(Text)
    measurement_unit = Column(String)  # percentage, dollars, days, etc.
    
    # Targets and thresholds
    target_value = Column(Float)
    minimum_acceptable = Column(Float, nullable=True)
    maximum_acceptable = Column(Float, nullable=True)
    
    # Current performance
    current_value = Column(Float, nullable=True)
    trend_direction = Column(String, nullable=True)  # improving, declining, stable
    
    # Measurement details
    measurement_frequency = Column(String)  # daily, weekly, monthly, quarterly
    data_source = Column(String)  # Where the data comes from
    calculation_method = Column(Text)  # How metric is calculated
    
    # Performance analysis
    variance_from_target = Column(Float, nullable=True)
    performance_rating = Column(String, nullable=True)  # exceeds, meets, below, poor
    
    # Action items
    improvement_actions = Column(JSON)  # Actions to improve performance
    responsible_person = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Historical data
    historical_values = Column(JSON)  # Time series of metric values
    benchmark_values = Column(JSON)  # Industry or historical benchmarks
    
    # Reporting
    report_to_government = Column(Boolean, default=False)
    reporting_frequency = Column(String, nullable=True)
    last_reported_date = Column(DateTime, nullable=True)
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"))

class KnowledgeTransition(Base):
    __tablename__ = "knowledge_transitions"
    
    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"))
    company_id = Column(Integer, ForeignKey("users.id"))
    
    # Knowledge transfer details
    knowledge_area = Column(String)
    knowledge_description = Column(Text)
    criticality_level = Column(Enum(RiskLevel), default=RiskLevel.MEDIUM)
    
    # Source and destination
    knowledge_source = Column(String)  # incumbent contractor, government, documents
    source_contact = Column(String, nullable=True)
    destination_team_members = Column(JSON)  # Who needs to receive knowledge
    
    # Transfer methods
    transfer_methods = Column(JSON)  # documentation, training, shadowing, etc.
    documentation_requirements = Column(JSON)  # What documentation is needed
    training_requirements = Column(JSON)  # Training that must be provided
    
    # Timeline
    transfer_start_date = Column(DateTime)
    transfer_end_date = Column(DateTime)
    key_milestones = Column(JSON)  # Important milestones in transfer
    
    # Progress tracking
    completion_percentage = Column(Float, default=0.0)
    knowledge_transfer_status = Column(String, default="planned")  # planned, in_progress, completed
    
    # Validation and verification
    competency_requirements = Column(JSON)  # Skills that must be demonstrated
    verification_methods = Column(JSON)  # How to verify knowledge transfer
    certification_required = Column(Boolean, default=False)
    
    # Documentation
    knowledge_artifacts = Column(JSON)  # Documents, procedures, etc.
    lessons_learned = Column(Text, nullable=True)
    best_practices = Column(JSON)  # Best practices captured
    
    # Risks and mitigation
    transfer_risks = Column(JSON)  # Risks to knowledge transfer
    mitigation_strategies = Column(JSON)  # How to mitigate risks
    contingency_plans = Column(JSON)  # Backup plans
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"))

class PostAwardChecklist(Base):
    __tablename__ = "post_award_checklists"
    
    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"))
    company_id = Column(Integer, ForeignKey("users.id"))
    
    # Checklist details
    checklist_name = Column(String)
    checklist_category = Column(String)  # administrative, technical, financial, etc.
    checklist_phase = Column(Enum(TransitionPhase))
    
    # Items and completion
    checklist_items = Column(JSON)  # Array of checklist items with status
    total_items = Column(Integer, default=0)
    completed_items = Column(Integer, default=0)
    completion_percentage = Column(Float, default=0.0)
    
    # Timeline
    target_completion_date = Column(DateTime)
    actual_completion_date = Column(DateTime, nullable=True)
    
    # Responsibility
    responsible_person = Column(Integer, ForeignKey("users.id"))
    approval_required_by = Column(String, nullable=True)
    approved_by = Column(String, nullable=True)
    approval_date = Column(DateTime, nullable=True)
    
    # Status
    checklist_status = Column(String, default="active")  # active, completed, cancelled
    
    # Notes and comments
    notes = Column(Text, nullable=True)
    issues_encountered = Column(JSON)  # Problems during execution
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"))

class LessonsLearned(Base):
    __tablename__ = "lessons_learned"
    
    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"))
    company_id = Column(Integer, ForeignKey("users.id"))
    
    # Lesson details
    lesson_title = Column(String)
    lesson_category = Column(String)  # process, technical, management, etc.
    lesson_description = Column(Text)
    
    # Context
    situation_description = Column(Text)  # What was the situation
    actions_taken = Column(Text)  # What actions were taken
    outcomes_achieved = Column(Text)  # What were the results
    
    # Analysis
    what_worked_well = Column(Text, nullable=True)
    what_could_improve = Column(Text, nullable=True)
    root_cause_analysis = Column(Text, nullable=True)
    
    # Recommendations
    recommendations = Column(JSON)  # Specific recommendations
    best_practices = Column(JSON)  # Best practices identified
    process_improvements = Column(JSON)  # Process improvement suggestions
    
    # Applicability
    applicable_situations = Column(JSON)  # When this lesson applies
    relevant_contract_types = Column(JSON)  # What contract types this applies to
    relevant_phases = Column(JSON)  # What project phases this applies to
    
    # Implementation
    implemented_changes = Column(JSON)  # Changes made based on lesson
    implementation_date = Column(DateTime, nullable=True)
    responsible_for_implementation = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Value and impact
    estimated_value = Column(Float, nullable=True)  # Business value of lesson
    risk_mitigation_value = Column(Float, nullable=True)  # Risk reduction value
    
    # Sharing and dissemination
    shared_with_team = Column(Boolean, default=False)
    shared_with_organization = Column(Boolean, default=False)
    training_material_created = Column(Boolean, default=False)
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    captured_by = Column(Integer, ForeignKey("users.id"))
    lesson_date = Column(DateTime, default=datetime.utcnow)  # When the lesson occurred