from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel

from database.connection import get_db
from models.resources import (
    Employee, ExternalResource, DeliveryPlan, ResourceAllocation,
    TimeEntry, DeliveryStatusUpdate, ResourceCapacityPlan,
    SkillLevel, ResourceType, AllocationStatus
)
from services.resource_planning import ResourcePlanningService
from routers.users import get_current_user
from models.user import User

router = APIRouter()

class EmployeeCreateRequest(BaseModel):
    first_name: str
    last_name: str
    email: str
    position_title: str
    employment_type: str = "full_time"
    start_date: datetime
    primary_skills: List[str] = []
    base_location: str
    hourly_rate: Optional[float] = None
    billable_rate: Optional[float] = None
    security_clearance: Optional[str] = None

class DeliveryPlanCreateRequest(BaseModel):
    plan_name: str
    start_date: str
    end_date: str
    duration_days: int
    description: Optional[str] = None
    methodology: str = "Agile"
    total_effort_hours: Optional[float] = None
    peak_team_size: Optional[int] = None

class ResourceAllocationRequest(BaseModel):
    role_title: str
    start_date: datetime
    end_date: datetime
    allocation_percentage: float
    estimated_hours: float
    hourly_rate: float
    required_skills: List[str] = []

class TimeEntryRequest(BaseModel):
    work_date: datetime
    hours_worked: float
    task_description: str
    billable_hours: float
    work_package: Optional[str] = None

class EmployeeResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    email: str
    position_title: str
    primary_skills: List[str]
    current_utilization: float
    is_available: bool
    
    class Config:
        from_attributes = True

class DeliveryPlanResponse(BaseModel):
    id: int
    plan_name: str
    project_start_date: datetime
    project_end_date: datetime
    total_duration_days: int
    total_effort_hours: float
    peak_team_size: int
    status: str
    confidence_score: Optional[float]
    
    class Config:
        from_attributes = True

@router.post("/employees")
async def add_employee(
    request: EmployeeCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a new employee to the team"""
    
    # Generate employee ID
    employee_count = db.query(Employee).filter(Employee.company_id == current_user.id).count()
    employee_id = f"EMP-{employee_count + 1:04d}"
    
    employee = Employee(
        company_id=current_user.id,
        employee_id=employee_id,
        first_name=request.first_name,
        last_name=request.last_name,
        email=request.email,
        position_title=request.position_title,
        employment_type=request.employment_type,
        start_date=request.start_date,
        primary_skills=request.primary_skills,
        base_location=request.base_location,
        hourly_rate=request.hourly_rate,
        billable_rate=request.billable_rate,
        security_clearance=request.security_clearance
    )
    
    db.add(employee)
    db.commit()
    db.refresh(employee)
    
    return {
        "employee_id": employee.id,
        "employee_code": employee.employee_id,
        "status": "success",
        "message": "Employee added successfully"
    }

@router.get("/employees", response_model=List[EmployeeResponse])
async def get_employees(
    active_only: bool = Query(True),
    skill: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get company employees"""
    
    query = db.query(Employee).filter(Employee.company_id == current_user.id)
    
    if active_only:
        query = query.filter(Employee.is_active == True)
    
    if skill:
        query = query.filter(Employee.primary_skills.contains([skill]))
    
    employees = query.offset(skip).limit(limit).all()
    
    return [
        EmployeeResponse(
            id=emp.id,
            first_name=emp.first_name,
            last_name=emp.last_name,
            email=emp.email,
            position_title=emp.position_title,
            primary_skills=emp.primary_skills or [],
            current_utilization=emp.current_utilization,
            is_available=emp.is_available
        )
        for emp in employees
    ]

@router.get("/employees/{employee_id}")
async def get_employee_detail(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed employee information"""
    
    employee = db.query(Employee).filter(
        Employee.id == employee_id,
        Employee.company_id == current_user.id
    ).first()
    
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Get current allocations
    current_allocations = db.query(ResourceAllocation).filter(
        ResourceAllocation.employee_id == employee_id,
        ResourceAllocation.status.in_([AllocationStatus.CONFIRMED, AllocationStatus.ACTIVE])
    ).all()
    
    # Get recent time entries
    recent_time = db.query(TimeEntry).filter(
        TimeEntry.employee_id == employee_id
    ).order_by(TimeEntry.work_date.desc()).limit(10).all()
    
    return {
        "employee": {
            "id": employee.id,
            "employee_id": employee.employee_id,
            "name": f"{employee.first_name} {employee.last_name}",
            "email": employee.email,
            "position": employee.position_title,
            "skills": employee.primary_skills or [],
            "location": employee.base_location,
            "clearance": employee.security_clearance,
            "utilization": employee.current_utilization,
            "billable_rate": employee.billable_rate,
            "performance_rating": employee.performance_rating
        },
        "current_allocations": [
            {
                "project": alloc.delivery_plan.project_id if alloc.delivery_plan else None,
                "role": alloc.role_title,
                "allocation": alloc.allocation_percentage,
                "start_date": alloc.start_date.isoformat(),
                "end_date": alloc.end_date.isoformat()
            }
            for alloc in current_allocations
        ],
        "recent_time_entries": [
            {
                "date": entry.work_date.isoformat(),
                "hours": entry.hours_worked,
                "description": entry.task_description,
                "billable": entry.billable_hours
            }
            for entry in recent_time
        ]
    }

@router.post("/external-resources")
async def add_external_resource(
    resource_name: str,
    company_name: str,
    contact_email: str,
    resource_type: str,
    specialization: str,
    skills: List[str],
    hourly_rate: float,
    contact_phone: Optional[str] = None,
    security_clearance: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add external resource/contractor"""
    
    external_resource = ExternalResource(
        company_id=current_user.id,
        resource_name=resource_name,
        company_name=company_name,
        contact_email=contact_email,
        contact_phone=contact_phone,
        resource_type=ResourceType(resource_type),
        specialization=specialization,
        skills=skills,
        hourly_rate=hourly_rate,
        security_clearance=security_clearance
    )
    
    db.add(external_resource)
    db.commit()
    db.refresh(external_resource)
    
    return {
        "resource_id": external_resource.id,
        "status": "success",
        "message": "External resource added successfully"
    }

@router.get("/external-resources")
async def get_external_resources(
    resource_type: Optional[str] = Query(None),
    skill: Optional[str] = Query(None),
    vetted_only: bool = Query(True),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get external resources"""
    
    query = db.query(ExternalResource).filter(
        ExternalResource.company_id == current_user.id,
        ExternalResource.is_active == True
    )
    
    if vetted_only:
        query = query.filter(ExternalResource.is_vetted == True)
    
    if resource_type:
        query = query.filter(ExternalResource.resource_type == resource_type)
    
    if skill:
        query = query.filter(ExternalResource.skills.contains([skill]))
    
    resources = query.offset(skip).limit(limit).all()
    
    return [
        {
            "id": resource.id,
            "name": resource.resource_name,
            "company": resource.company_name,
            "type": resource.resource_type.value,
            "specialization": resource.specialization,
            "skills": resource.skills or [],
            "hourly_rate": resource.hourly_rate,
            "rating": resource.rating,
            "is_vetted": resource.is_vetted
        }
        for resource in resources
    ]

@router.post("/delivery-plans")
async def create_delivery_plan(
    project_id: int,
    request: DeliveryPlanCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create AI-optimized delivery plan"""
    
    service = ResourcePlanningService(db)
    
    try:
        plan_data = request.dict()
        result = await service.create_delivery_plan(project_id, plan_data, current_user.id)
        
        return {
            "status": "success",
            "delivery_plan_id": result['delivery_plan_id'],
            "plan_summary": result['plan_summary'],
            "ai_recommendations": result['ai_recommendations']
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delivery plan creation failed: {str(e)}")

@router.get("/delivery-plans", response_model=List[DeliveryPlanResponse])
async def get_delivery_plans(
    project_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get delivery plans"""
    
    query = db.query(DeliveryPlan).filter(DeliveryPlan.created_by == current_user.id)
    
    if project_id:
        query = query.filter(DeliveryPlan.project_id == project_id)
    
    if status:
        query = query.filter(DeliveryPlan.status == status)
    
    plans = query.order_by(DeliveryPlan.created_at.desc()).offset(skip).limit(limit).all()
    
    return [
        DeliveryPlanResponse(
            id=plan.id,
            plan_name=plan.plan_name,
            project_start_date=plan.project_start_date,
            project_end_date=plan.project_end_date,
            total_duration_days=plan.total_duration_days,
            total_effort_hours=plan.total_effort_hours,
            peak_team_size=plan.peak_team_size,
            status=plan.status,
            confidence_score=plan.confidence_score
        )
        for plan in plans
    ]

@router.get("/delivery-plans/{plan_id}")
async def get_delivery_plan_detail(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed delivery plan"""
    
    plan = db.query(DeliveryPlan).filter(
        DeliveryPlan.id == plan_id,
        DeliveryPlan.created_by == current_user.id
    ).first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="Delivery plan not found")
    
    # Get resource allocations
    allocations = db.query(ResourceAllocation).filter(
        ResourceAllocation.delivery_plan_id == plan_id
    ).all()
    
    # Get latest status update
    latest_update = db.query(DeliveryStatusUpdate).filter(
        DeliveryStatusUpdate.delivery_plan_id == plan_id
    ).order_by(DeliveryStatusUpdate.update_date.desc()).first()
    
    return {
        "plan": {
            "id": plan.id,
            "plan_name": plan.plan_name,
            "description": plan.description,
            "start_date": plan.project_start_date.isoformat(),
            "end_date": plan.project_end_date.isoformat(),
            "duration_days": plan.total_duration_days,
            "effort_hours": plan.total_effort_hours,
            "team_size": plan.peak_team_size,
            "methodology": plan.delivery_methodology,
            "status": plan.status,
            "confidence_score": plan.confidence_score
        },
        "work_packages": plan.work_packages or [],
        "deliverables": plan.deliverables or [],
        "milestones": plan.milestones or [],
        "resource_allocations": [
            {
                "id": alloc.id,
                "resource_name": f"{alloc.employee.first_name} {alloc.employee.last_name}" if alloc.employee else alloc.external_resource.resource_name,
                "resource_type": "internal" if alloc.employee else "external",
                "role": alloc.role_title,
                "allocation": alloc.allocation_percentage,
                "hours": alloc.estimated_hours,
                "rate": alloc.hourly_rate,
                "cost": alloc.estimated_cost,
                "status": alloc.status.value,
                "start_date": alloc.start_date.isoformat(),
                "end_date": alloc.end_date.isoformat()
            }
            for alloc in allocations
        ],
        "ai_recommendations": plan.ai_recommendations or [],
        "latest_update": {
            "date": latest_update.update_date.isoformat(),
            "progress": latest_update.overall_progress_percentage,
            "schedule_variance": latest_update.schedule_variance_days
        } if latest_update else None
    }

@router.post("/delivery-plans/{plan_id}/allocations")
async def add_resource_allocation(
    plan_id: int,
    employee_id: Optional[int] = None,
    external_resource_id: Optional[int] = None,
    allocation_data: ResourceAllocationRequest = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add resource allocation to delivery plan"""
    
    # Verify plan ownership
    plan = db.query(DeliveryPlan).filter(
        DeliveryPlan.id == plan_id,
        DeliveryPlan.created_by == current_user.id
    ).first()
    
    if not plan:
        raise HTTPException(status_code=404, detail="Delivery plan not found")
    
    if not employee_id and not external_resource_id:
        raise HTTPException(status_code=400, detail="Must specify either employee or external resource")
    
    allocation = ResourceAllocation(
        delivery_plan_id=plan_id,
        employee_id=employee_id,
        external_resource_id=external_resource_id,
        role_title=allocation_data.role_title,
        start_date=allocation_data.start_date,
        end_date=allocation_data.end_date,
        allocation_percentage=allocation_data.allocation_percentage,
        estimated_hours=allocation_data.estimated_hours,
        hourly_rate=allocation_data.hourly_rate,
        estimated_cost=allocation_data.estimated_hours * allocation_data.hourly_rate,
        required_skills=allocation_data.required_skills,
        created_by=current_user.id
    )
    
    db.add(allocation)
    db.commit()
    db.refresh(allocation)
    
    return {
        "allocation_id": allocation.id,
        "status": "success",
        "message": "Resource allocation added"
    }

@router.post("/time-entries")
async def add_time_entry(
    allocation_id: int,
    request: TimeEntryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add time entry for resource allocation"""
    
    # Verify allocation exists and user has access
    allocation = db.query(ResourceAllocation).filter(
        ResourceAllocation.id == allocation_id
    ).first()
    
    if not allocation:
        raise HTTPException(status_code=404, detail="Allocation not found")
    
    # Verify access through delivery plan
    plan = db.query(DeliveryPlan).filter(
        DeliveryPlan.id == allocation.delivery_plan_id,
        DeliveryPlan.created_by == current_user.id
    ).first()
    
    if not plan:
        raise HTTPException(status_code=403, detail="Access denied")
    
    time_entry = TimeEntry(
        allocation_id=allocation_id,
        employee_id=allocation.employee_id,
        work_date=request.work_date,
        hours_worked=request.hours_worked,
        task_description=request.task_description,
        billable_hours=request.billable_hours,
        non_billable_hours=request.hours_worked - request.billable_hours,
        work_package=request.work_package,
        billing_rate=allocation.hourly_rate
    )
    
    db.add(time_entry)
    db.commit()
    db.refresh(time_entry)
    
    return {
        "time_entry_id": time_entry.id,
        "status": "success",
        "message": "Time entry added"
    }

@router.get("/delivery-plans/{plan_id}/progress")
async def get_delivery_progress(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get delivery plan progress tracking"""
    
    service = ResourcePlanningService(db)
    
    try:
        progress = await service.track_delivery_progress(plan_id, current_user.id)
        return progress
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Progress tracking failed: {str(e)}")

@router.post("/delivery-plans/{plan_id}/optimize")
async def optimize_resource_allocation(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Optimize resource allocation using AI"""
    
    service = ResourcePlanningService(db)
    
    try:
        optimization = await service.optimize_resource_allocation(plan_id, current_user.id)
        return optimization
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")

@router.get("/capacity-analysis")
async def get_capacity_analysis(
    planning_months: int = Query(12, ge=3, le=36),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive resource capacity analysis"""
    
    service = ResourcePlanningService(db)
    
    try:
        capacity_plan = await service.generate_capacity_plan(current_user.id, planning_months)
        return capacity_plan
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Capacity analysis failed: {str(e)}")

@router.get("/resource-utilization")
async def get_resource_utilization(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get resource utilization report"""
    
    if not start_date:
        start_date = datetime.now() - timedelta(days=30)
    if not end_date:
        end_date = datetime.now()
    
    # Get all employees
    employees = db.query(Employee).filter(
        Employee.company_id == current_user.id,
        Employee.is_active == True
    ).all()
    
    utilization_data = []
    
    for emp in employees:
        # Get allocations in period
        allocations = db.query(ResourceAllocation).filter(
            ResourceAllocation.employee_id == emp.id,
            ResourceAllocation.start_date <= end_date,
            ResourceAllocation.end_date >= start_date
        ).all()
        
        total_allocation = sum(alloc.allocation_percentage for alloc in allocations)
        
        # Get actual time entries
        time_entries = db.query(TimeEntry).filter(
            TimeEntry.employee_id == emp.id,
            TimeEntry.work_date >= start_date,
            TimeEntry.work_date <= end_date
        ).all()
        
        total_hours = sum(entry.hours_worked for entry in time_entries)
        billable_hours = sum(entry.billable_hours for entry in time_entries)
        
        utilization_data.append({
            "employee_id": emp.id,
            "name": f"{emp.first_name} {emp.last_name}",
            "position": emp.position_title,
            "planned_allocation": min(total_allocation, 100),
            "actual_hours": total_hours,
            "billable_hours": billable_hours,
            "billable_rate": (billable_hours / total_hours * 100) if total_hours > 0 else 0,
            "skills": emp.primary_skills or []
        })
    
    return {
        "period": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        },
        "utilization_data": utilization_data,
        "summary": {
            "total_employees": len(employees),
            "average_utilization": sum(u["planned_allocation"] for u in utilization_data) / len(utilization_data) if utilization_data else 0,
            "total_hours": sum(u["actual_hours"] for u in utilization_data),
            "total_billable": sum(u["billable_hours"] for u in utilization_data)
        }
    }

@router.get("/skills-inventory")
async def get_skills_inventory(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get company skills inventory and gaps"""
    
    # Get all employees and their skills
    employees = db.query(Employee).filter(
        Employee.company_id == current_user.id,
        Employee.is_active == True
    ).all()
    
    # Aggregate skills
    skills_inventory = {}
    
    for emp in employees:
        primary_skills = emp.primary_skills or []
        secondary_skills = emp.secondary_skills or []
        
        for skill in primary_skills:
            if skill not in skills_inventory:
                skills_inventory[skill] = {'primary': 0, 'secondary': 0, 'total': 0}
            skills_inventory[skill]['primary'] += 1
            skills_inventory[skill]['total'] += 1
        
        for skill in secondary_skills:
            if skill not in skills_inventory:
                skills_inventory[skill] = {'primary': 0, 'secondary': 0, 'total': 0}
            skills_inventory[skill]['secondary'] += 1
            skills_inventory[skill]['total'] += 1
    
    # Get current project requirements
    active_plans = db.query(DeliveryPlan).filter(
        DeliveryPlan.created_by == current_user.id,
        DeliveryPlan.status.in_(['approved', 'active'])
    ).all()
    
    required_skills = {}
    for plan in active_plans:
        if plan.required_skills:
            for skill_req in plan.required_skills:
                skill_name = skill_req.get('skill') if isinstance(skill_req, dict) else skill_req
                quantity = skill_req.get('quantity', 1) if isinstance(skill_req, dict) else 1
                
                if skill_name not in required_skills:
                    required_skills[skill_name] = 0
                required_skills[skill_name] += quantity
    
    # Identify gaps
    skill_gaps = []
    for skill, required_count in required_skills.items():
        available_count = skills_inventory.get(skill, {}).get('total', 0)
        if required_count > available_count:
            skill_gaps.append({
                'skill': skill,
                'required': required_count,
                'available': available_count,
                'gap': required_count - available_count
            })
    
    return {
        "skills_inventory": skills_inventory,
        "required_skills": required_skills,
        "skill_gaps": skill_gaps,
        "summary": {
            "total_skills": len(skills_inventory),
            "total_gaps": len(skill_gaps),
            "coverage_percentage": (len(skills_inventory) - len(skill_gaps)) / len(required_skills) * 100 if required_skills else 100
        }
    }