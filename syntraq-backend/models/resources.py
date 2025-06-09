"""
© 2025 Aliff Capital, Quartermasters FZC, and SkillvenzA. All rights reserved.

Syntraq AI - RDP (Resource & Delivery Planner) Models
A Joint Innovation by Aliff Capital, Quartermasters FZC, and SkillvenzA
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, JSON, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()

class SkillLevel(enum.Enum):
    JUNIOR = "junior"
    MID_LEVEL = "mid_level"
    SENIOR = "senior"
    PRINCIPAL = "principal"
    EXPERT = "expert"

class ResourceType(enum.Enum):
    INTERNAL = "internal"
    CONTRACTOR = "contractor"
    SUBCONTRACTOR = "subcontractor"
    PARTNER = "partner"

class AllocationStatus(enum.Enum):
    PLANNED = "planned"
    CONFIRMED = "confirmed"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class Employee(Base):
    __tablename__ = "employees"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("users.id"))  # Company owner
    
    # Personal information
    employee_id = Column(String, unique=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True, index=True)
    phone = Column(String, nullable=True)
    
    # Employment details
    position_title = Column(String)
    department = Column(String, nullable=True)
    employment_type = Column(String, default="full_time")  # full_time, part_time, contractor
    start_date = Column(DateTime)
    end_date = Column(DateTime, nullable=True)
    
    # Skills and qualifications
    primary_skills = Column(JSON)  # List of primary skills
    secondary_skills = Column(JSON)  # List of secondary skills
    certifications = Column(JSON)  # Professional certifications
    education = Column(JSON)  # Education background
    
    # Work details
    base_location = Column(String)
    security_clearance = Column(String, nullable=True)
    hourly_rate = Column(Float, nullable=True)
    annual_salary = Column(Float, nullable=True)
    billable_rate = Column(Float, nullable=True)
    
    # Capacity planning
    standard_hours_per_week = Column(Float, default=40.0)
    max_utilization_percentage = Column(Float, default=85.0)
    current_utilization = Column(Float, default=0.0)
    
    # Performance tracking
    performance_rating = Column(Float, nullable=True)  # 1-5 scale
    last_review_date = Column(DateTime, nullable=True)
    career_level = Column(Enum(SkillLevel), default=SkillLevel.MID_LEVEL)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_available = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    allocations = relationship("ResourceAllocation", back_populates="employee")
    time_entries = relationship("TimeEntry", back_populates="employee")

class ExternalResource(Base):
    __tablename__ = "external_resources"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("users.id"))
    
    # Basic information
    resource_name = Column(String)
    company_name = Column(String)
    contact_email = Column(String)
    contact_phone = Column(String, nullable=True)
    
    # Resource details
    resource_type = Column(Enum(ResourceType))
    specialization = Column(String)
    skills = Column(JSON)  # List of skills
    experience_years = Column(Integer, nullable=True)
    
    # Financial
    hourly_rate = Column(Float)
    daily_rate = Column(Float, nullable=True)
    currency = Column(String, default="USD")
    
    # Availability
    available_start_date = Column(DateTime, nullable=True)
    available_end_date = Column(DateTime, nullable=True)
    max_hours_per_week = Column(Float, default=40.0)
    
    # Qualifications
    security_clearance = Column(String, nullable=True)
    certifications = Column(JSON)
    previous_work = Column(JSON)  # Previous project history
    
    # Contract details
    contract_terms = Column(JSON)  # Contract terms and conditions
    payment_terms = Column(String, nullable=True)
    
    # Performance
    rating = Column(Float, nullable=True)  # 1-5 scale
    feedback = Column(Text, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_vetted = Column(Boolean, default=False)
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    allocations = relationship("ResourceAllocation", back_populates="external_resource")

class DeliveryPlan(Base):
    __tablename__ = "delivery_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("financial_projects.id"))
    
    # Plan details
    plan_name = Column(String)
    plan_version = Column(String, default="1.0")
    description = Column(Text, nullable=True)
    
    # Timeline
    project_start_date = Column(DateTime)
    project_end_date = Column(DateTime)
    total_duration_days = Column(Integer)
    
    # Work breakdown structure
    work_packages = Column(JSON)  # Hierarchical work breakdown
    deliverables = Column(JSON)  # List of deliverables with due dates
    milestones = Column(JSON)  # Key milestones and dates
    
    # Resource requirements
    total_effort_hours = Column(Float)
    peak_team_size = Column(Integer)
    required_skills = Column(JSON)  # Skills needed with quantities
    
    # Risk and assumptions
    risks = Column(JSON)  # Identified delivery risks
    assumptions = Column(JSON)  # Planning assumptions
    dependencies = Column(JSON)  # External dependencies
    
    # Methodology
    delivery_methodology = Column(String)  # Agile, Waterfall, Hybrid
    sprint_length = Column(Integer, nullable=True)  # For Agile projects
    review_frequency = Column(String, nullable=True)
    
    # Quality assurance
    qa_approach = Column(Text, nullable=True)
    testing_strategy = Column(Text, nullable=True)
    acceptance_criteria = Column(JSON)
    
    # Client interaction
    communication_plan = Column(JSON)  # Client communication schedule
    reporting_schedule = Column(JSON)  # Regular reporting cadence
    
    # Approval workflow
    status = Column(String, default="draft")  # draft, review, approved, active
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    
    # AI insights
    ai_recommendations = Column(JSON)  # AI-generated optimization suggestions
    confidence_score = Column(Float, nullable=True)
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    allocations = relationship("ResourceAllocation", back_populates="delivery_plan")
    status_updates = relationship("DeliveryStatusUpdate", back_populates="delivery_plan")

class ResourceAllocation(Base):
    __tablename__ = "resource_allocations"
    
    id = Column(Integer, primary_key=True, index=True)
    delivery_plan_id = Column(Integer, ForeignKey("delivery_plans.id"))
    
    # Resource assignment
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    external_resource_id = Column(Integer, ForeignKey("external_resources.id"), nullable=True)
    
    # Role and responsibilities
    role_title = Column(String)
    work_package = Column(String, nullable=True)
    responsibilities = Column(Text)
    
    # Timeline
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    allocation_percentage = Column(Float)  # 0-100% allocation
    estimated_hours = Column(Float)
    
    # Skills required
    required_skills = Column(JSON)  # Skills needed for this allocation
    skill_match_score = Column(Float, nullable=True)  # How well resource matches
    
    # Financial
    hourly_rate = Column(Float)
    estimated_cost = Column(Float)
    actual_cost = Column(Float, nullable=True)
    
    # Status and tracking
    status = Column(Enum(AllocationStatus), default=AllocationStatus.PLANNED)
    confirmed_date = Column(DateTime, nullable=True)
    actual_start_date = Column(DateTime, nullable=True)
    actual_end_date = Column(DateTime, nullable=True)
    
    # Performance
    planned_productivity = Column(Float, default=1.0)  # Expected productivity factor
    actual_productivity = Column(Float, nullable=True)
    quality_rating = Column(Float, nullable=True)
    
    # Notes and feedback
    allocation_notes = Column(Text, nullable=True)
    performance_notes = Column(Text, nullable=True)
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    delivery_plan = relationship("DeliveryPlan", back_populates="allocations")
    employee = relationship("Employee", back_populates="allocations")
    external_resource = relationship("ExternalResource", back_populates="allocations")
    time_entries = relationship("TimeEntry", back_populates="allocation")

class TimeEntry(Base):
    __tablename__ = "time_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    allocation_id = Column(Integer, ForeignKey("resource_allocations.id"))
    employee_id = Column(Integer, ForeignKey("employees.id"))
    
    # Time details
    work_date = Column(DateTime)
    hours_worked = Column(Float)
    overtime_hours = Column(Float, default=0.0)
    
    # Work description
    task_description = Column(Text)
    work_package = Column(String, nullable=True)
    deliverable = Column(String, nullable=True)
    
    # Billing
    billable_hours = Column(Float)
    non_billable_hours = Column(Float, default=0.0)
    billing_rate = Column(Float)
    
    # Status
    status = Column(String, default="draft")  # draft, submitted, approved, billed
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    
    # Quality and efficiency
    quality_score = Column(Float, nullable=True)  # Self-assessed quality
    efficiency_score = Column(Float, nullable=True)  # Planned vs actual
    
    # Notes
    notes = Column(Text, nullable=True)
    issues_encountered = Column(Text, nullable=True)
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    allocation = relationship("ResourceAllocation", back_populates="time_entries")
    employee = relationship("Employee", back_populates="time_entries")

class DeliveryStatusUpdate(Base):
    __tablename__ = "delivery_status_updates"
    
    id = Column(Integer, primary_key=True, index=True)
    delivery_plan_id = Column(Integer, ForeignKey("delivery_plans.id"))
    
    # Update details
    update_date = Column(DateTime)
    reporting_period_start = Column(DateTime)
    reporting_period_end = Column(DateTime)
    
    # Progress metrics
    overall_progress_percentage = Column(Float)  # 0-100%
    schedule_variance_days = Column(Integer)  # + or - days from baseline
    budget_variance_percentage = Column(Float)  # + or - % from baseline
    
    # Work package progress
    work_package_status = Column(JSON)  # Status of each work package
    completed_deliverables = Column(JSON)  # List of completed deliverables
    upcoming_deliverables = Column(JSON)  # Deliverables due soon
    
    # Resource utilization
    team_utilization = Column(Float)  # Average team utilization %
    resource_changes = Column(JSON)  # Any resource additions/changes
    
    # Issues and risks
    current_issues = Column(JSON)  # Active issues
    resolved_issues = Column(JSON)  # Issues resolved this period
    risk_updates = Column(JSON)  # Risk status changes
    
    # Quality metrics
    defect_count = Column(Integer, default=0)
    rework_hours = Column(Float, default=0.0)
    client_satisfaction = Column(Float, nullable=True)  # 1-5 scale
    
    # Financial
    costs_incurred = Column(Float)
    budget_consumed_percentage = Column(Float)
    forecast_final_cost = Column(Float, nullable=True)
    
    # Client communication
    client_feedback = Column(Text, nullable=True)
    change_requests = Column(JSON)  # Any scope changes
    
    # AI insights
    ai_analysis = Column(JSON)  # AI-generated insights
    recommendations = Column(JSON)  # AI recommendations
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    delivery_plan = relationship("DeliveryPlan", back_populates="status_updates")

class ResourceCapacityPlan(Base):
    __tablename__ = "resource_capacity_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("users.id"))
    
    # Planning period
    plan_name = Column(String)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    
    # Capacity analysis
    total_available_hours = Column(Float)
    total_allocated_hours = Column(Float)
    utilization_percentage = Column(Float)
    
    # Skill gaps
    skill_gaps = Column(JSON)  # Identified skill shortages
    recommended_hires = Column(JSON)  # Recommended new hires
    training_needs = Column(JSON)  # Training recommendations
    
    # Resource optimization
    optimization_suggestions = Column(JSON)  # AI optimization suggestions
    cost_optimization = Column(JSON)  # Cost reduction opportunities
    
    # Forecasting
    demand_forecast = Column(JSON)  # Projected resource demand
    supply_forecast = Column(JSON)  # Projected resource supply
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"))