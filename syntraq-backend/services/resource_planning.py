from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import json
from collections import defaultdict

from models.resources import (
    Employee, ExternalResource, DeliveryPlan, ResourceAllocation,
    TimeEntry, DeliveryStatusUpdate, ResourceCapacityPlan,
    SkillLevel, ResourceType, AllocationStatus
)
from models.financial import FinancialProject
from services.ai_service import AIService

class ResourcePlanningService:
    """AI-powered resource planning and delivery management"""
    
    def __init__(self, db: Session):
        self.db = db
        self.ai_service = AIService()
    
    async def create_delivery_plan(
        self, 
        project_id: int, 
        plan_data: Dict[str, Any],
        user_id: int
    ) -> Dict[str, Any]:
        """Create comprehensive delivery plan with AI optimization"""
        
        project = self.db.query(FinancialProject).filter(FinancialProject.id == project_id).first()
        if not project:
            raise ValueError("Project not found")
        
        # Get available resources
        available_resources = await self._get_available_resources(user_id, plan_data.get('start_date'), plan_data.get('end_date'))
        
        # AI optimization of delivery plan
        optimized_plan = await self._ai_optimize_delivery_plan(plan_data, available_resources, project)
        
        # Create delivery plan
        delivery_plan = DeliveryPlan(
            project_id=project_id,
            plan_name=optimized_plan['plan_name'],
            description=optimized_plan.get('description'),
            project_start_date=datetime.fromisoformat(optimized_plan['start_date']),
            project_end_date=datetime.fromisoformat(optimized_plan['end_date']),
            total_duration_days=optimized_plan['duration_days'],
            work_packages=optimized_plan['work_packages'],
            deliverables=optimized_plan['deliverables'],
            milestones=optimized_plan['milestones'],
            total_effort_hours=optimized_plan['total_effort_hours'],
            peak_team_size=optimized_plan['peak_team_size'],
            required_skills=optimized_plan['required_skills'],
            risks=optimized_plan.get('risks', []),
            assumptions=optimized_plan.get('assumptions', []),
            delivery_methodology=optimized_plan.get('methodology', 'Agile'),
            ai_recommendations=optimized_plan.get('ai_recommendations', []),
            confidence_score=optimized_plan.get('confidence_score', 80.0),
            created_by=user_id
        )
        
        self.db.add(delivery_plan)
        self.db.commit()
        self.db.refresh(delivery_plan)
        
        # Create initial resource allocations
        allocations = await self._create_resource_allocations(delivery_plan.id, optimized_plan['resource_plan'], user_id)
        
        return {
            'delivery_plan_id': delivery_plan.id,
            'plan_summary': {
                'duration_days': delivery_plan.total_duration_days,
                'total_effort_hours': delivery_plan.total_effort_hours,
                'peak_team_size': delivery_plan.peak_team_size,
                'confidence_score': delivery_plan.confidence_score
            },
            'resource_allocations': len(allocations),
            'ai_recommendations': delivery_plan.ai_recommendations
        }
    
    async def _ai_optimize_delivery_plan(
        self, 
        plan_data: Dict[str, Any], 
        available_resources: List[Dict],
        project: FinancialProject
    ) -> Dict[str, Any]:
        """AI-powered delivery plan optimization"""
        
        context = {
            'project_details': {
                'name': project.project_name,
                'value': project.estimated_value,
                'agency': project.client_agency,
                'contract_type': project.contract_type,
                'performance_period': project.performance_period
            },
            'plan_requirements': plan_data,
            'available_resources': available_resources,
            'constraints': {
                'budget': project.estimated_value,
                'timeline': plan_data.get('duration_days', 365),
                'team_size_limit': len(available_resources) + 5  # Allow for some external hires
            }
        }
        
        prompt = self._create_delivery_planning_prompt(context)
        
        try:
            response = await self.ai_service.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": self._get_delivery_planning_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=3000
            )
            
            ai_plan = self._parse_ai_delivery_response(response.choices[0].message.content)
            
            # Merge AI optimizations with original plan
            optimized_plan = plan_data.copy()
            optimized_plan.update(ai_plan.get('optimizations', {}))
            optimized_plan['ai_recommendations'] = ai_plan.get('recommendations', [])
            optimized_plan['confidence_score'] = ai_plan.get('confidence_score', 80.0)
            
            # Ensure required fields
            optimized_plan.setdefault('work_packages', self._generate_default_work_packages(plan_data))
            optimized_plan.setdefault('deliverables', self._generate_default_deliverables(plan_data))
            optimized_plan.setdefault('milestones', self._generate_default_milestones(plan_data))
            optimized_plan.setdefault('resource_plan', self._generate_resource_plan(optimized_plan, available_resources))
            
            return optimized_plan
            
        except Exception as e:
            print(f"AI delivery plan optimization failed: {e}")
            # Return plan with basic optimizations
            return self._apply_basic_optimizations(plan_data, available_resources)
    
    async def _get_available_resources(self, user_id: int, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Get available internal and external resources"""
        
        start_dt = datetime.fromisoformat(start_date) if start_date else datetime.now()
        end_dt = datetime.fromisoformat(end_date) if end_date else start_dt + timedelta(days=365)
        
        # Get internal employees
        employees = self.db.query(Employee).filter(
            Employee.company_id == user_id,
            Employee.is_active == True,
            Employee.is_available == True
        ).all()
        
        # Get external resources
        external_resources = self.db.query(ExternalResource).filter(
            ExternalResource.company_id == user_id,
            ExternalResource.is_active == True,
            ExternalResource.is_vetted == True
        ).all()
        
        available_resources = []
        
        # Process internal employees
        for emp in employees:
            # Calculate availability
            current_allocations = self._calculate_current_utilization(emp.id, start_dt, end_dt)
            available_capacity = emp.max_utilization_percentage - current_allocations
            
            if available_capacity > 10:  # At least 10% available
                available_resources.append({
                    'id': emp.id,
                    'type': 'internal',
                    'name': f"{emp.first_name} {emp.last_name}",
                    'position': emp.position_title,
                    'skills': emp.primary_skills or [],
                    'skill_level': emp.career_level.value if emp.career_level else 'mid_level',
                    'hourly_rate': emp.billable_rate or emp.hourly_rate,
                    'available_capacity': available_capacity,
                    'security_clearance': emp.security_clearance,
                    'location': emp.base_location,
                    'rating': emp.performance_rating
                })
        
        # Process external resources
        for ext in external_resources:
            if self._is_external_resource_available(ext, start_dt, end_dt):
                available_resources.append({
                    'id': ext.id,
                    'type': 'external',
                    'name': ext.resource_name,
                    'company': ext.company_name,
                    'specialization': ext.specialization,
                    'skills': ext.skills or [],
                    'experience_years': ext.experience_years,
                    'hourly_rate': ext.hourly_rate,
                    'available_capacity': 100.0,  # Assume full availability
                    'security_clearance': ext.security_clearance,
                    'rating': ext.rating
                })
        
        return available_resources
    
    async def _create_resource_allocations(
        self, 
        delivery_plan_id: int, 
        resource_plan: Dict[str, Any],
        user_id: int
    ) -> List[ResourceAllocation]:
        """Create resource allocations based on plan"""
        
        allocations = []
        
        for allocation_data in resource_plan.get('allocations', []):
            # Determine if internal or external resource
            if allocation_data.get('type') == 'internal':
                employee_id = allocation_data['resource_id']
                external_resource_id = None
            else:
                employee_id = None
                external_resource_id = allocation_data['resource_id']
            
            allocation = ResourceAllocation(
                delivery_plan_id=delivery_plan_id,
                employee_id=employee_id,
                external_resource_id=external_resource_id,
                role_title=allocation_data['role'],
                work_package=allocation_data.get('work_package'),
                responsibilities=allocation_data.get('responsibilities', ''),
                start_date=datetime.fromisoformat(allocation_data['start_date']),
                end_date=datetime.fromisoformat(allocation_data['end_date']),
                allocation_percentage=allocation_data['allocation_percentage'],
                estimated_hours=allocation_data['estimated_hours'],
                required_skills=allocation_data.get('required_skills', []),
                hourly_rate=allocation_data['hourly_rate'],
                estimated_cost=allocation_data['estimated_hours'] * allocation_data['hourly_rate'],
                created_by=user_id
            )
            
            self.db.add(allocation)
            allocations.append(allocation)
        
        self.db.commit()
        return allocations
    
    async def optimize_resource_allocation(self, delivery_plan_id: int, user_id: int) -> Dict[str, Any]:
        """Optimize existing resource allocation using AI"""
        
        delivery_plan = self.db.query(DeliveryPlan).filter(
            DeliveryPlan.id == delivery_plan_id,
            DeliveryPlan.created_by == user_id
        ).first()
        
        if not delivery_plan:
            raise ValueError("Delivery plan not found")
        
        # Get current allocations
        current_allocations = self.db.query(ResourceAllocation).filter(
            ResourceAllocation.delivery_plan_id == delivery_plan_id
        ).all()
        
        # Get available resources
        available_resources = await self._get_available_resources(
            user_id, 
            delivery_plan.project_start_date.isoformat(), 
            delivery_plan.project_end_date.isoformat()
        )
        
        # Analyze current performance
        performance_data = await self._analyze_current_performance(delivery_plan_id)
        
        # AI optimization
        optimization_suggestions = await self._ai_optimize_allocations(
            current_allocations, available_resources, performance_data, delivery_plan
        )
        
        return {
            'current_allocations': len(current_allocations),
            'optimization_suggestions': optimization_suggestions,
            'potential_savings': optimization_suggestions.get('cost_savings', 0),
            'efficiency_improvement': optimization_suggestions.get('efficiency_gain', 0)
        }
    
    async def generate_capacity_plan(self, user_id: int, planning_period_months: int = 12) -> Dict[str, Any]:
        """Generate comprehensive resource capacity plan"""
        
        start_date = datetime.now()
        end_date = start_date + timedelta(days=30 * planning_period_months)
        
        # Get all resources
        employees = self.db.query(Employee).filter(
            Employee.company_id == user_id,
            Employee.is_active == True
        ).all()
        
        external_resources = self.db.query(ExternalResource).filter(
            ExternalResource.company_id == user_id,
            ExternalResource.is_active == True
        ).all()
        
        # Calculate capacity metrics
        total_internal_hours = sum(emp.standard_hours_per_week * 52 * (planning_period_months / 12) for emp in employees)
        
        # Get current and planned allocations
        current_allocations = self._get_allocations_in_period(user_id, start_date, end_date)
        total_allocated_hours = sum(alloc.estimated_hours for alloc in current_allocations)
        
        utilization_percentage = (total_allocated_hours / total_internal_hours * 100) if total_internal_hours > 0 else 0
        
        # Skill gap analysis
        skill_gaps = await self._analyze_skill_gaps(user_id, current_allocations)
        
        # AI capacity optimization
        capacity_insights = await self._ai_analyze_capacity(employees, external_resources, current_allocations, skill_gaps)
        
        # Create capacity plan
        capacity_plan = ResourceCapacityPlan(
            company_id=user_id,
            plan_name=f"Capacity Plan {start_date.strftime('%Y-%m')}",
            start_date=start_date,
            end_date=end_date,
            total_available_hours=total_internal_hours,
            total_allocated_hours=total_allocated_hours,
            utilization_percentage=utilization_percentage,
            skill_gaps=skill_gaps,
            recommended_hires=capacity_insights.get('recommended_hires', []),
            training_needs=capacity_insights.get('training_needs', []),
            optimization_suggestions=capacity_insights.get('optimization_suggestions', []),
            demand_forecast=capacity_insights.get('demand_forecast', {}),
            supply_forecast=capacity_insights.get('supply_forecast', {}),
            created_by=user_id
        )
        
        self.db.add(capacity_plan)
        self.db.commit()
        
        return {
            'capacity_plan_id': capacity_plan.id,
            'utilization_percentage': utilization_percentage,
            'available_hours': total_internal_hours,
            'allocated_hours': total_allocated_hours,
            'skill_gaps': skill_gaps,
            'ai_insights': capacity_insights
        }
    
    async def track_delivery_progress(self, delivery_plan_id: int, user_id: int) -> Dict[str, Any]:
        """Track and analyze delivery progress"""
        
        delivery_plan = self.db.query(DeliveryPlan).filter(
            DeliveryPlan.id == delivery_plan_id,
            DeliveryPlan.created_by == user_id
        ).first()
        
        if not delivery_plan:
            raise ValueError("Delivery plan not found")
        
        # Get latest status update
        latest_update = self.db.query(DeliveryStatusUpdate).filter(
            DeliveryStatusUpdate.delivery_plan_id == delivery_plan_id
        ).order_by(DeliveryStatusUpdate.update_date.desc()).first()
        
        # Calculate current progress
        current_progress = await self._calculate_delivery_progress(delivery_plan_id)
        
        # Resource utilization analysis
        resource_utilization = await self._analyze_resource_utilization(delivery_plan_id)
        
        # Risk assessment
        risk_assessment = await self._assess_delivery_risks(delivery_plan, current_progress)
        
        # AI insights
        ai_insights = await self._generate_delivery_insights(delivery_plan, current_progress, resource_utilization)
        
        return {
            'delivery_plan_id': delivery_plan_id,
            'overall_progress': current_progress['overall_progress'],
            'schedule_variance': current_progress['schedule_variance'],
            'budget_variance': current_progress['budget_variance'],
            'resource_utilization': resource_utilization,
            'risk_level': risk_assessment['overall_risk'],
            'key_risks': risk_assessment['key_risks'],
            'ai_insights': ai_insights,
            'last_update': latest_update.update_date.isoformat() if latest_update else None
        }
    
    def _calculate_current_utilization(self, employee_id: int, start_date: datetime, end_date: datetime) -> float:
        """Calculate current utilization percentage for employee"""
        
        allocations = self.db.query(ResourceAllocation).filter(
            ResourceAllocation.employee_id == employee_id,
            ResourceAllocation.start_date <= end_date,
            ResourceAllocation.end_date >= start_date,
            ResourceAllocation.status.in_([AllocationStatus.CONFIRMED, AllocationStatus.ACTIVE])
        ).all()
        
        total_allocation = sum(alloc.allocation_percentage for alloc in allocations)
        return min(total_allocation, 100.0)  # Cap at 100%
    
    def _is_external_resource_available(self, resource: ExternalResource, start_date: datetime, end_date: datetime) -> bool:
        """Check if external resource is available for period"""
        
        if resource.available_start_date and resource.available_start_date > end_date:
            return False
        
        if resource.available_end_date and resource.available_end_date < start_date:
            return False
        
        # Check existing allocations
        existing_allocations = self.db.query(ResourceAllocation).filter(
            ResourceAllocation.external_resource_id == resource.id,
            ResourceAllocation.start_date <= end_date,
            ResourceAllocation.end_date >= start_date,
            ResourceAllocation.status.in_([AllocationStatus.CONFIRMED, AllocationStatus.ACTIVE])
        ).all()
        
        total_allocation = sum(alloc.allocation_percentage for alloc in existing_allocations)
        return total_allocation < 80  # Available if less than 80% allocated
    
    def _generate_default_work_packages(self, plan_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate default work breakdown structure"""
        
        return [
            {
                'id': 'WP1',
                'name': 'Project Initiation',
                'description': 'Project startup and planning activities',
                'duration_days': 14,
                'effort_hours': 120,
                'dependencies': []
            },
            {
                'id': 'WP2', 
                'name': 'Requirements Analysis',
                'description': 'Gather and analyze requirements',
                'duration_days': 21,
                'effort_hours': 240,
                'dependencies': ['WP1']
            },
            {
                'id': 'WP3',
                'name': 'Design & Development',
                'description': 'Core development work',
                'duration_days': 90,
                'effort_hours': 1200,
                'dependencies': ['WP2']
            },
            {
                'id': 'WP4',
                'name': 'Testing & Quality Assurance',
                'description': 'Testing and quality validation',
                'duration_days': 30,
                'effort_hours': 400,
                'dependencies': ['WP3']
            },
            {
                'id': 'WP5',
                'name': 'Deployment & Closeout',
                'description': 'Deployment and project closure',
                'duration_days': 14,
                'effort_hours': 160,
                'dependencies': ['WP4']
            }
        ]
    
    def _generate_default_deliverables(self, plan_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate default deliverables"""
        
        start_date = datetime.fromisoformat(plan_data.get('start_date', datetime.now().isoformat()))
        
        return [
            {
                'name': 'Project Management Plan',
                'description': 'Comprehensive project management plan',
                'due_date': (start_date + timedelta(days=14)).isoformat(),
                'work_package': 'WP1'
            },
            {
                'name': 'Requirements Document',
                'description': 'Detailed requirements specification',
                'due_date': (start_date + timedelta(days=35)).isoformat(),
                'work_package': 'WP2'
            },
            {
                'name': 'System Design Document',
                'description': 'Technical design documentation',
                'due_date': (start_date + timedelta(days=60)).isoformat(),
                'work_package': 'WP3'
            },
            {
                'name': 'Developed Solution',
                'description': 'Completed software solution',
                'due_date': (start_date + timedelta(days=125)).isoformat(),
                'work_package': 'WP3'
            },
            {
                'name': 'Test Results Report',
                'description': 'Comprehensive testing results',
                'due_date': (start_date + timedelta(days=155)).isoformat(),
                'work_package': 'WP4'
            }
        ]
    
    def _generate_default_milestones(self, plan_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate default project milestones"""
        
        start_date = datetime.fromisoformat(plan_data.get('start_date', datetime.now().isoformat()))
        
        return [
            {
                'name': 'Project Kickoff',
                'date': start_date.isoformat(),
                'description': 'Official project start'
            },
            {
                'name': 'Requirements Approval',
                'date': (start_date + timedelta(days=35)).isoformat(),
                'description': 'Client approval of requirements'
            },
            {
                'name': 'Design Review',
                'date': (start_date + timedelta(days=60)).isoformat(),
                'description': 'Technical design review checkpoint'
            },
            {
                'name': 'Development Complete',
                'date': (start_date + timedelta(days=125)).isoformat(),
                'description': 'All development work finished'
            },
            {
                'name': 'Final Delivery',
                'date': (start_date + timedelta(days=169)).isoformat(),
                'description': 'Project completion and handover'
            }
        ]
    
    def _generate_resource_plan(self, optimized_plan: Dict[str, Any], available_resources: List[Dict]) -> Dict[str, Any]:
        """Generate resource allocation plan"""
        
        # Simple resource allocation based on available resources
        allocations = []
        total_hours = optimized_plan.get('total_effort_hours', 2000)
        duration_days = optimized_plan.get('duration_days', 169)
        
        # Allocate based on skills and availability
        hours_allocated = 0
        
        for resource in available_resources[:optimized_plan.get('peak_team_size', 5)]:
            allocation_percentage = min(resource.get('available_capacity', 50), 80)
            
            # Calculate hours for this resource
            working_days = duration_days * 0.7  # Assume 70% working days
            hours_per_day = 8 * (allocation_percentage / 100)
            resource_hours = working_days * hours_per_day
            
            allocations.append({
                'resource_id': resource['id'],
                'type': resource['type'],
                'role': resource.get('position', 'Team Member'),
                'start_date': optimized_plan.get('start_date'),
                'end_date': optimized_plan.get('end_date'),
                'allocation_percentage': allocation_percentage,
                'estimated_hours': resource_hours,
                'hourly_rate': resource.get('hourly_rate', 100),
                'required_skills': resource.get('skills', [])
            })
            
            hours_allocated += resource_hours
            
            if hours_allocated >= total_hours:
                break
        
        return {'allocations': allocations}
    
    def _get_delivery_planning_system_prompt(self) -> str:
        """System prompt for delivery planning AI"""
        return """You are an expert project manager specializing in government contracting delivery planning.

Optimize delivery plans for:
1. Resource efficiency and allocation
2. Risk mitigation
3. Timeline optimization
4. Cost effectiveness
5. Quality assurance

Respond in JSON format:
{
    "optimizations": {
        "duration_days": 150,
        "methodology": "Agile",
        "peak_team_size": 6,
        "total_effort_hours": 1800
    },
    "recommendations": [
        "Specific recommendation 1",
        "Specific recommendation 2"
    ],
    "risks": [
        {"risk": "Risk description", "mitigation": "Mitigation strategy"}
    ],
    "confidence_score": 85
}"""
    
    def _create_delivery_planning_prompt(self, context: Dict) -> str:
        """Create prompt for delivery planning optimization"""
        return f"""Optimize this government contract delivery plan:

PROJECT: {json.dumps(context['project_details'], indent=2)}

REQUIREMENTS: {json.dumps(context['plan_requirements'], indent=2)}

AVAILABLE RESOURCES: {json.dumps(context['available_resources'][:10], indent=2)}

CONSTRAINTS: {json.dumps(context['constraints'], indent=2)}

Focus on realistic timelines, efficient resource utilization, and risk mitigation while ensuring quality delivery."""
    
    def _parse_ai_delivery_response(self, response: str) -> Dict[str, Any]:
        """Parse AI delivery planning response"""
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
                'optimizations': {},
                'recommendations': ['Manual planning review recommended'],
                'risks': [],
                'confidence_score': 50
            }
    
    def _apply_basic_optimizations(self, plan_data: Dict[str, Any], available_resources: List[Dict]) -> Dict[str, Any]:
        """Apply basic optimizations when AI fails"""
        
        # Basic optimization logic
        optimized = plan_data.copy()
        
        # Adjust team size based on available resources
        optimized['peak_team_size'] = min(len(available_resources), 8)
        
        # Conservative duration estimate
        base_duration = optimized.get('duration_days', 180)
        optimized['duration_days'] = int(base_duration * 1.2)  # Add 20% buffer
        
        # Calculate effort based on team size and duration
        team_size = optimized['peak_team_size']
        working_days = optimized['duration_days'] * 0.7
        optimized['total_effort_hours'] = team_size * working_days * 6  # 6 hours/day average
        
        return optimized