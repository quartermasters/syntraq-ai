from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel

from database.connection import get_db
from models.arts import (
    AIAgent, AgentTask, TeamConversation, TeamCollaboration,
    AgentKnowledgeBase, AgentPerformanceMetrics,
    AgentRole, AgentStatus, TaskStatus, TaskPriority
)
from services.arts_engine import ARTSEngine
from routers.users import get_current_user
from models.user import User

router = APIRouter()

class TeamInitializationRequest(BaseModel):
    team_configuration: Dict[str, Any] = {}

class TaskAssignmentRequest(BaseModel):
    agent_role: str
    task_title: str
    task_description: str
    task_type: str = "analysis"
    priority: str = "medium"
    input_data: Dict[str, Any] = {}
    requirements: List[str] = []
    deliverables: List[str] = []
    estimated_duration: int = 30
    opportunity_id: Optional[int] = None
    proposal_id: Optional[int] = None
    due_hours: int = 24

class CollaborationRequest(BaseModel):
    collaboration_type: str
    participants: List[str]  # List of agent roles
    objective: str
    context: Dict[str, Any] = {}

class AgentResponse(BaseModel):
    id: int
    name: str
    role: str
    status: str
    current_workload: int
    success_rate: float
    quality_score: float
    
    class Config:
        from_attributes = True

class TaskResponse(BaseModel):
    id: int
    title: str
    status: str
    priority: str
    assigned_to: str
    progress_percentage: float
    created_at: datetime
    
    class Config:
        from_attributes = True

@router.post("/team/initialize")
async def initialize_ai_team(
    request: TeamInitializationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Initialize AI team for the company"""
    
    engine = ARTSEngine(db)
    
    try:
        result = await engine.initialize_ai_team(
            current_user.id,
            request.team_configuration
        )
        
        return {
            "status": "success",
            **result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Team initialization failed: {str(e)}")

@router.get("/team/status")
async def get_team_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current AI team status"""
    
    engine = ARTSEngine(db)
    
    try:
        status = await engine.get_team_status(current_user.id)
        return status
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get team status: {str(e)}")

@router.get("/agents", response_model=List[AgentResponse])
async def get_agents(
    role: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get AI agents with filtering"""
    
    query = db.query(AIAgent).filter(AIAgent.company_id == current_user.id)
    
    if role:
        query = query.filter(AIAgent.agent_role == AgentRole(role))
    
    if status:
        query = query.filter(AIAgent.status == AgentStatus(status))
    
    agents = query.order_by(AIAgent.agent_name).offset(skip).limit(limit).all()
    
    return [
        AgentResponse(
            id=agent.id,
            name=agent.agent_name,
            role=agent.agent_role.value,
            status=agent.status.value,
            current_workload=agent.current_workload,
            success_rate=agent.success_rate,
            quality_score=agent.quality_score
        )
        for agent in agents
    ]

@router.get("/agents/{agent_id}")
async def get_agent_detail(
    agent_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed agent information"""
    
    agent = db.query(AIAgent).filter(
        AIAgent.id == agent_id,
        AIAgent.company_id == current_user.id
    ).first()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Get recent tasks
    recent_tasks = db.query(AgentTask).filter(
        AgentTask.agent_id == agent_id,
        AgentTask.created_at >= datetime.utcnow() - timedelta(days=30)
    ).order_by(AgentTask.created_at.desc()).limit(10).all()
    
    # Get performance metrics
    performance = db.query(AgentPerformanceMetrics).filter(
        AgentPerformanceMetrics.agent_id == agent_id
    ).order_by(AgentPerformanceMetrics.period_end.desc()).first()
    
    return {
        "agent": {
            "id": agent.id,
            "name": agent.agent_name,
            "role": agent.agent_role.value,
            "persona": agent.agent_persona,
            "expertise_areas": agent.expertise_areas,
            "core_skills": agent.core_skills,
            "status": agent.status.value,
            "current_workload": agent.current_workload,
            "max_concurrent_tasks": agent.max_concurrent_tasks,
            "tasks_completed": agent.tasks_completed,
            "success_rate": agent.success_rate,
            "quality_score": agent.quality_score,
            "last_active": agent.last_active.isoformat()
        },
        "recent_tasks": [
            {
                "id": task.id,
                "title": task.task_title,
                "type": task.task_type,
                "status": task.status.value,
                "priority": task.priority.value,
                "progress": task.progress_percentage,
                "created_at": task.created_at.isoformat(),
                "completed_at": task.completed_at.isoformat() if task.completed_at else None
            }
            for task in recent_tasks
        ],
        "performance": {
            "avg_completion_time": performance.avg_completion_time_minutes if performance else None,
            "avg_quality_score": performance.avg_quality_score if performance else None,
            "satisfaction_score": performance.human_satisfaction_score if performance else None
        } if performance else None
    }

@router.post("/tasks/assign")
async def assign_task(
    request: TaskAssignmentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Assign task to AI agent"""
    
    engine = ARTSEngine(db)
    
    try:
        task_details = {
            'title': request.task_title,
            'description': request.task_description,
            'type': request.task_type,
            'input_data': request.input_data,
            'requirements': request.requirements,
            'deliverables': request.deliverables,
            'estimated_duration': request.estimated_duration,
            'opportunity_id': request.opportunity_id,
            'proposal_id': request.proposal_id,
            'due_hours': request.due_hours
        }
        
        result = await engine.assign_task_to_agent(
            current_user.id,
            request.agent_role,
            task_details,
            request.priority
        )
        
        return {
            "status": "success",
            **result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Task assignment failed: {str(e)}")

@router.get("/tasks", response_model=List[TaskResponse])
async def get_tasks(
    agent_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get agent tasks with filtering"""
    
    query = db.query(AgentTask).filter(AgentTask.company_id == current_user.id)
    
    if agent_id:
        query = query.filter(AgentTask.agent_id == agent_id)
    
    if status:
        query = query.filter(AgentTask.status == TaskStatus(status))
    
    if priority:
        query = query.filter(AgentTask.priority == TaskPriority(priority))
    
    tasks = query.order_by(AgentTask.created_at.desc()).offset(skip).limit(limit).all()
    
    return [
        TaskResponse(
            id=task.id,
            title=task.task_title,
            status=task.status.value,
            priority=task.priority.value,
            assigned_to=task.agent.agent_name if task.agent else "Unknown",
            progress_percentage=task.progress_percentage,
            created_at=task.created_at
        )
        for task in tasks
    ]

@router.get("/tasks/{task_id}")
async def get_task_detail(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed task information"""
    
    task = db.query(AgentTask).filter(
        AgentTask.id == task_id,
        AgentTask.company_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {
        "task": {
            "id": task.id,
            "title": task.task_title,
            "description": task.task_description,
            "type": task.task_type,
            "status": task.status.value,
            "priority": task.priority.value,
            "progress_percentage": task.progress_percentage,
            "input_data": task.input_data,
            "requirements": task.requirements,
            "deliverables": task.deliverables,
            "estimated_duration": task.estimated_duration_minutes,
            "actual_duration": task.actual_duration_minutes,
            "assigned_at": task.assigned_at.isoformat(),
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "due_date": task.due_date.isoformat() if task.due_date else None
        },
        "agent": {
            "id": task.agent.id,
            "name": task.agent.agent_name,
            "role": task.agent.agent_role.value
        } if task.agent else None,
        "output": task.output_data,
        "ai_reasoning": task.ai_reasoning,
        "confidence_score": task.confidence_score,
        "quality_metrics": task.quality_metrics,
        "human_feedback": task.human_feedback,
        "task_rating": task.task_rating
    }

@router.post("/tasks/{task_id}/feedback")
async def provide_task_feedback(
    task_id: int,
    rating: float,
    feedback: str,
    suggestions: List[str] = [],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Provide feedback on completed task"""
    
    task = db.query(AgentTask).filter(
        AgentTask.id == task_id,
        AgentTask.company_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.status != TaskStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Can only provide feedback on completed tasks")
    
    # Update task with feedback
    task.task_rating = rating
    task.human_feedback = {
        "rating": rating,
        "feedback": feedback,
        "suggestions": suggestions,
        "provided_at": datetime.utcnow().isoformat(),
        "provided_by": current_user.id
    }
    
    # Update agent metrics
    if task.agent:
        agent = task.agent
        total_ratings = db.query(AgentTask).filter(
            AgentTask.agent_id == agent.id,
            AgentTask.task_rating.isnot(None)
        ).count()
        
        if total_ratings > 0:
            avg_rating = db.query(AgentTask).filter(
                AgentTask.agent_id == agent.id,
                AgentTask.task_rating.isnot(None)
            ).with_entities(AgentTask.task_rating).all()
            
            agent.quality_score = sum([r[0] for r in avg_rating]) / len(avg_rating)
    
    db.commit()
    
    return {
        "status": "success",
        "message": "Feedback recorded successfully"
    }

@router.post("/collaborate")
async def initiate_collaboration(
    request: CollaborationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Initiate AI team collaboration"""
    
    engine = ARTSEngine(db)
    
    try:
        result = await engine.initiate_team_collaboration(
            current_user.id,
            request.collaboration_type,
            request.participants,
            request.objective,
            request.context
        )
        
        return {
            "status": "success",
            **result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Collaboration initiation failed: {str(e)}")

@router.get("/collaborations")
async def get_collaborations(
    collaboration_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get team collaborations"""
    
    query = db.query(TeamCollaboration).filter(TeamCollaboration.company_id == current_user.id)
    
    if collaboration_type:
        query = query.filter(TeamCollaboration.collaboration_type == collaboration_type)
    
    if status:
        query = query.filter(TeamCollaboration.status == status)
    
    collaborations = query.order_by(TeamCollaboration.created_at.desc()).offset(skip).limit(limit).all()
    
    return [
        {
            "id": collab.id,
            "name": collab.collaboration_name,
            "type": collab.collaboration_type,
            "description": collab.description,
            "status": collab.status,
            "progress_percentage": collab.progress_percentage,
            "participants_count": len(collab.participating_agents or []),
            "start_date": collab.start_date.isoformat(),
            "target_completion": collab.target_completion.isoformat() if collab.target_completion else None,
            "actual_completion": collab.actual_completion.isoformat() if collab.actual_completion else None
        }
        for collab in collaborations
    ]

@router.get("/conversations")
async def get_conversations(
    agent_id: Optional[int] = Query(None),
    conversation_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get team conversations"""
    
    query = db.query(TeamConversation).filter(TeamConversation.company_id == current_user.id)
    
    if agent_id:
        query = query.filter(TeamConversation.agent_id == agent_id)
    
    if conversation_type:
        query = query.filter(TeamConversation.conversation_type == conversation_type)
    
    if status:
        query = query.filter(TeamConversation.status == status)
    
    conversations = query.order_by(TeamConversation.started_at.desc()).offset(skip).limit(limit).all()
    
    return [
        {
            "id": conv.id,
            "title": conv.conversation_title,
            "type": conv.conversation_type,
            "topic": conv.topic,
            "status": conv.status.value,
            "participants_count": len(conv.participants or []),
            "messages_count": len(conv.messages or []),
            "started_at": conv.started_at.isoformat(),
            "last_activity": conv.last_activity.isoformat(),
            "ended_at": conv.ended_at.isoformat() if conv.ended_at else None,
            "escalated_to_human": conv.escalated_to_human
        }
        for conv in conversations
    ]

@router.get("/conversations/{conversation_id}")
async def get_conversation_detail(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed conversation information"""
    
    conversation = db.query(TeamConversation).filter(
        TeamConversation.id == conversation_id,
        TeamConversation.company_id == current_user.id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return {
        "conversation": {
            "id": conversation.id,
            "title": conversation.conversation_title,
            "type": conversation.conversation_type,
            "topic": conversation.topic,
            "status": conversation.status.value,
            "priority": conversation.priority.value,
            "participants": conversation.participants,
            "started_at": conversation.started_at.isoformat(),
            "last_activity": conversation.last_activity.isoformat(),
            "ended_at": conversation.ended_at.isoformat() if conversation.ended_at else None,
            "escalated_to_human": conversation.escalated_to_human
        },
        "messages": conversation.messages or [],
        "summary": conversation.conversation_summary,
        "key_decisions": conversation.key_decisions or [],
        "action_items": conversation.action_items or [],
        "resolution": conversation.resolution,
        "recommendations": conversation.recommendations or []
    }

@router.get("/agents/{agent_id}/tasks", response_model=List[TaskResponse])
async def get_agent_tasks(
    agent_id: int,
    status: Optional[str] = Query(None),
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get tasks for specific agent"""
    
    # Verify agent belongs to user
    agent = db.query(AIAgent).filter(
        AIAgent.id == agent_id,
        AIAgent.company_id == current_user.id
    ).first()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    engine = ARTSEngine(db)
    
    try:
        tasks = await engine.get_agent_task_history(current_user.id, agent_id, limit)
        return [TaskResponse(**task) for task in tasks]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get agent tasks: {str(e)}")

@router.get("/dashboard/team-analytics")
async def get_team_analytics(
    days_back: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get AI team analytics dashboard"""
    
    start_date = datetime.utcnow() - timedelta(days=days_back)
    
    # Task statistics
    total_tasks = db.query(AgentTask).filter(
        AgentTask.company_id == current_user.id,
        AgentTask.created_at >= start_date
    ).count()
    
    completed_tasks = db.query(AgentTask).filter(
        AgentTask.company_id == current_user.id,
        AgentTask.created_at >= start_date,
        AgentTask.status == TaskStatus.COMPLETED
    ).count()
    
    failed_tasks = db.query(AgentTask).filter(
        AgentTask.company_id == current_user.id,
        AgentTask.created_at >= start_date,
        AgentTask.status == TaskStatus.FAILED
    ).count()
    
    # Performance metrics
    avg_completion_time = db.query(AgentTask).filter(
        AgentTask.company_id == current_user.id,
        AgentTask.created_at >= start_date,
        AgentTask.status == TaskStatus.COMPLETED,
        AgentTask.actual_duration_minutes.isnot(None)
    ).with_entities(AgentTask.actual_duration_minutes).all()
    
    avg_duration = sum([t[0] for t in avg_completion_time]) / len(avg_completion_time) if avg_completion_time else 0
    
    # Team utilization
    active_agents = db.query(AIAgent).filter(
        AIAgent.company_id == current_user.id,
        AIAgent.status != AgentStatus.OFFLINE
    ).count()
    
    busy_agents = db.query(AIAgent).filter(
        AIAgent.company_id == current_user.id,
        AIAgent.status == AgentStatus.BUSY
    ).count()
    
    # Collaboration metrics
    collaborations = db.query(TeamCollaboration).filter(
        TeamCollaboration.company_id == current_user.id,
        TeamCollaboration.created_at >= start_date
    ).count()
    
    conversations = db.query(TeamConversation).filter(
        TeamConversation.company_id == current_user.id,
        TeamConversation.started_at >= start_date
    ).count()
    
    return {
        "period_days": days_back,
        "task_metrics": {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "completion_rate": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0,
            "avg_completion_time_minutes": round(avg_duration, 1)
        },
        "team_utilization": {
            "active_agents": active_agents,
            "busy_agents": busy_agents,
            "utilization_rate": (busy_agents / active_agents * 100) if active_agents > 0 else 0
        },
        "collaboration_metrics": {
            "collaborations_initiated": collaborations,
            "conversations_held": conversations,
            "avg_conversations_per_day": conversations / days_back if days_back > 0 else 0
        },
        "efficiency_metrics": {
            "tasks_per_day": total_tasks / days_back if days_back > 0 else 0,
            "automation_savings_hours": round((total_tasks * 2.5), 1)  # Estimate 2.5 hours saved per automated task
        }
    }