"""
© 2025 Aliff Capital, Quartermasters FZC, and SkillvenzA. All rights reserved.

Syntraq AI - ARTS (AI Role-Based Team Simulation) Models
A Joint Innovation by Aliff Capital, Quartermasters FZC, and SkillvenzA
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, JSON, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()

class AgentRole(enum.Enum):
    CAPTURE_MANAGER = "capture_manager"
    PROPOSAL_MANAGER = "proposal_manager"
    TECHNICAL_LEAD = "technical_lead"
    PRICING_ANALYST = "pricing_analyst"
    CONTRACTS_SPECIALIST = "contracts_specialist"
    MARKETING_SPECIALIST = "marketing_specialist"
    BD_SPECIALIST = "bd_specialist"
    PROJECT_MANAGER = "project_manager"
    QUALITY_REVIEWER = "quality_reviewer"
    COMPLIANCE_OFFICER = "compliance_officer"

class AgentStatus(enum.Enum):
    AVAILABLE = "available"
    ASSIGNED = "assigned"
    BUSY = "busy"
    OFFLINE = "offline"

class TaskPriority(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class TaskStatus(enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ConversationStatus(enum.Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"

class AIAgent(Base):
    __tablename__ = "ai_agents"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("users.id"))
    
    # Agent identity
    agent_name = Column(String)
    agent_role = Column(Enum(AgentRole))
    agent_persona = Column(Text)  # AI personality and communication style
    expertise_areas = Column(JSON)  # Areas of specialization
    
    # Capabilities
    core_skills = Column(JSON)  # Core competencies
    knowledge_domains = Column(JSON)  # Subject matter expertise
    tools_access = Column(JSON)  # Which tools/systems agent can use
    permission_level = Column(String, default="standard")  # access permissions
    
    # Performance metrics
    tasks_completed = Column(Integer, default=0)
    success_rate = Column(Float, default=100.0)
    avg_response_time_minutes = Column(Float, default=5.0)
    quality_score = Column(Float, default=8.5)
    
    # Status and availability
    status = Column(Enum(AgentStatus), default=AgentStatus.AVAILABLE)
    current_workload = Column(Integer, default=0)
    max_concurrent_tasks = Column(Integer, default=5)
    last_active = Column(DateTime, default=datetime.utcnow)
    
    # Learning and adaptation
    training_data = Column(JSON)  # Accumulated knowledge
    performance_feedback = Column(JSON)  # Feedback for improvement
    adaptation_notes = Column(Text)  # How agent has evolved
    
    # AI model configuration
    model_name = Column(String, default="gpt-4o-mini")
    temperature = Column(Float, default=0.3)
    max_tokens = Column(Integer, default=2000)
    system_prompt = Column(Text)  # Base system prompt for agent
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    tasks = relationship("AgentTask", back_populates="agent", cascade="all, delete-orphan")
    conversations = relationship("TeamConversation", back_populates="agent")

class AgentTask(Base):
    __tablename__ = "agent_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("ai_agents.id"))
    company_id = Column(Integer, ForeignKey("users.id"))
    
    # Task details
    task_title = Column(String)
    task_description = Column(Text)
    task_type = Column(String)  # analysis, content_creation, review, research, etc.
    priority = Column(Enum(TaskPriority), default=TaskPriority.MEDIUM)
    
    # Context and requirements
    input_data = Column(JSON)  # Data/context for the task
    requirements = Column(JSON)  # Specific requirements
    deliverables = Column(JSON)  # Expected outputs
    constraints = Column(JSON)  # Limitations or constraints
    
    # Execution
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    progress_percentage = Column(Float, default=0.0)
    estimated_duration_minutes = Column(Integer, default=30)
    actual_duration_minutes = Column(Integer, nullable=True)
    
    # Results
    output_data = Column(JSON)  # Task results
    ai_reasoning = Column(Text)  # AI's reasoning process
    confidence_score = Column(Float, nullable=True)  # AI confidence in result
    quality_metrics = Column(JSON)  # Quality assessment
    
    # Dependencies
    depends_on_tasks = Column(JSON)  # Other tasks this depends on
    blocks_tasks = Column(JSON)  # Tasks that depend on this one
    related_opportunity_id = Column(Integer, ForeignKey("opportunities.id"), nullable=True)
    related_proposal_id = Column(Integer, ForeignKey("proposals.id"), nullable=True)
    
    # Feedback and learning
    human_feedback = Column(JSON)  # Feedback from users
    task_rating = Column(Float, nullable=True)  # 1-10 rating
    lessons_learned = Column(Text)  # What was learned from this task
    
    # Timeline
    assigned_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    due_date = Column(DateTime, nullable=True)
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    assigned_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    agent = relationship("AIAgent", back_populates="tasks")

class TeamConversation(Base):
    __tablename__ = "team_conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("ai_agents.id"))
    company_id = Column(Integer, ForeignKey("users.id"))
    
    # Conversation details
    conversation_title = Column(String)
    conversation_type = Column(String)  # collaboration, consultation, escalation, etc.
    participants = Column(JSON)  # List of participating agents and users
    
    # Context
    topic = Column(String)
    related_opportunity_id = Column(Integer, ForeignKey("opportunities.id"), nullable=True)
    related_proposal_id = Column(Integer, ForeignKey("proposals.id"), nullable=True)
    related_task_id = Column(Integer, ForeignKey("agent_tasks.id"), nullable=True)
    
    # Conversation flow
    messages = Column(JSON)  # Array of conversation messages
    conversation_summary = Column(Text)  # AI-generated summary
    key_decisions = Column(JSON)  # Important decisions made
    action_items = Column(JSON)  # Actions agreed upon
    
    # Status and management
    status = Column(Enum(ConversationStatus), default=ConversationStatus.ACTIVE)
    priority = Column(Enum(TaskPriority), default=TaskPriority.MEDIUM)
    escalated_to_human = Column(Boolean, default=False)
    
    # Outcomes
    resolution = Column(Text, nullable=True)
    recommendations = Column(JSON)  # Recommendations from conversation
    follow_up_required = Column(Boolean, default=False)
    follow_up_date = Column(DateTime, nullable=True)
    
    # Tracking
    started_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    agent = relationship("AIAgent", back_populates="conversations")

class TeamCollaboration(Base):
    __tablename__ = "team_collaborations"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("users.id"))
    
    # Collaboration details
    collaboration_name = Column(String)
    collaboration_type = Column(String)  # project_team, review_panel, working_group
    description = Column(Text)
    
    # Team composition
    participating_agents = Column(JSON)  # List of agent IDs and roles
    human_participants = Column(JSON)  # List of human participants
    team_lead_agent_id = Column(Integer, ForeignKey("ai_agents.id"), nullable=True)
    
    # Scope and objectives
    objectives = Column(JSON)  # Collaboration goals
    deliverables = Column(JSON)  # Expected outputs
    success_criteria = Column(JSON)  # How success is measured
    
    # Timeline and progress
    start_date = Column(DateTime, default=datetime.utcnow)
    target_completion = Column(DateTime, nullable=True)
    actual_completion = Column(DateTime, nullable=True)
    progress_percentage = Column(Float, default=0.0)
    
    # Work products
    shared_workspace = Column(JSON)  # Shared documents and resources
    meeting_minutes = Column(JSON)  # Record of team meetings
    decisions_log = Column(JSON)  # Important decisions made
    
    # Performance tracking
    efficiency_score = Column(Float, nullable=True)
    quality_score = Column(Float, nullable=True)
    collaboration_rating = Column(Float, nullable=True)
    
    # Status
    status = Column(String, default="active")  # active, paused, completed, cancelled
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"))

class AgentKnowledgeBase(Base):
    __tablename__ = "agent_knowledge_base"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("ai_agents.id"))
    company_id = Column(Integer, ForeignKey("users.id"))
    
    # Knowledge item details
    knowledge_title = Column(String)
    knowledge_type = Column(String)  # fact, procedure, template, best_practice, lesson_learned
    category = Column(String)  # domain categorization
    
    # Content
    content = Column(Text)
    structured_data = Column(JSON)  # Structured knowledge representation
    source = Column(String)  # Where knowledge came from
    
    # Applicability
    context_tags = Column(JSON)  # When this knowledge applies
    use_cases = Column(JSON)  # Specific scenarios for use
    confidence_level = Column(Float, default=0.8)  # Confidence in knowledge
    
    # Usage tracking
    access_count = Column(Integer, default=0)
    last_accessed = Column(DateTime, nullable=True)
    effectiveness_rating = Column(Float, nullable=True)
    
    # Validation
    verified_by_human = Column(Boolean, default=False)
    verification_date = Column(DateTime, nullable=True)
    needs_review = Column(Boolean, default=False)
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    learned_from_task_id = Column(Integer, ForeignKey("agent_tasks.id"), nullable=True)

class AgentPerformanceMetrics(Base):
    __tablename__ = "agent_performance_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("ai_agents.id"))
    company_id = Column(Integer, ForeignKey("users.id"))
    
    # Reporting period
    period_start = Column(DateTime)
    period_end = Column(DateTime)
    measurement_type = Column(String)  # daily, weekly, monthly, quarterly
    
    # Task performance
    tasks_assigned = Column(Integer, default=0)
    tasks_completed = Column(Integer, default=0)
    tasks_failed = Column(Integer, default=0)
    avg_completion_time_minutes = Column(Float, default=0.0)
    
    # Quality metrics
    avg_quality_score = Column(Float, default=0.0)
    avg_accuracy_score = Column(Float, default=0.0)
    human_satisfaction_score = Column(Float, default=0.0)
    improvement_suggestions_count = Column(Integer, default=0)
    
    # Collaboration metrics
    conversations_participated = Column(Integer, default=0)
    collaborations_led = Column(Integer, default=0)
    peer_rating_avg = Column(Float, default=0.0)
    
    # Learning metrics
    new_knowledge_items = Column(Integer, default=0)
    knowledge_applied_count = Column(Integer, default=0)
    adaptation_score = Column(Float, default=0.0)
    
    # Availability metrics
    uptime_percentage = Column(Float, default=100.0)
    response_time_avg_minutes = Column(Float, default=5.0)
    
    # Tracking
    calculated_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"))