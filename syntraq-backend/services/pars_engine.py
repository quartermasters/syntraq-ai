from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import json

from models.pars import (
    Contract, ContractDeliverable, ContractTransition, ComplianceItem,
    PerformanceMetric, KnowledgeTransition, PostAwardChecklist, LessonsLearned,
    ContractStatus, DeliverableStatus, RiskLevel, ComplianceStatus, TransitionPhase
)
from models.proposals import Proposal
from models.opportunity import Opportunity
from services.ai_service import AIService

class PARSEngine:
    """Post-Award Readiness Suite Engine"""
    
    def __init__(self, db: Session):
        self.db = db
        self.ai_service = AIService()
    
    async def create_contract_from_proposal(
        self,
        company_id: int,
        proposal_id: int,
        award_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create contract structure from awarded proposal"""
        
        proposal = self.db.query(Proposal).filter(
            Proposal.id == proposal_id,
            Proposal.created_by == company_id
        ).first()
        
        if not proposal:
            raise ValueError("Proposal not found")
        
        opportunity = self.db.query(Opportunity).filter(
            Opportunity.id == proposal.opportunity_id
        ).first()
        
        # Generate contract number
        contract_count = self.db.query(Contract).filter(
            Contract.company_id == company_id
        ).count()
        contract_number = f"CONTRACT-{datetime.now().year}-{contract_count + 1:04d}"
        
        # Create contract
        contract = Contract(
            company_id=company_id,
            proposal_id=proposal_id,
            opportunity_id=proposal.opportunity_id,
            contract_number=contract_number,
            contract_title=award_details.get('contract_title', proposal.proposal_title),
            contracting_agency=opportunity.agency if opportunity else award_details.get('agency'),
            contracting_officer=award_details.get('contracting_officer'),
            contract_type=award_details.get('contract_type', 'FFP'),
            contract_value=award_details.get('contract_value', proposal.proposed_price),
            base_period_months=award_details.get('base_period_months', 12),
            option_periods=award_details.get('option_periods', []),
            award_date=datetime.fromisoformat(award_details['award_date']) if award_details.get('award_date') else datetime.utcnow(),
            start_date=datetime.fromisoformat(award_details['start_date']) if award_details.get('start_date') else datetime.utcnow(),
            end_date=datetime.fromisoformat(award_details['end_date']) if award_details.get('end_date') else datetime.utcnow() + timedelta(days=365),
            status=ContractStatus.EXECUTED,
            total_obligated=award_details.get('contract_value', proposal.proposed_price or 0),
            remaining_funds=award_details.get('contract_value', proposal.proposed_price or 0),
            program_manager=company_id,
            government_pm=award_details.get('government_pm'),
            government_cor=award_details.get('government_cor'),
            contract_documents=award_details.get('contract_documents', []),
            compliance_requirements=award_details.get('compliance_requirements', []),
            created_by=company_id
        )
        
        self.db.add(contract)
        self.db.commit()
        self.db.refresh(contract)
        
        # Create initial deliverables from proposal requirements
        deliverables_created = await self._create_contract_deliverables(contract.id, award_details)
        
        # Create transition plan
        transitions_created = await self._create_transition_plan(contract.id, award_details)
        
        # Create compliance items
        compliance_items = await self._create_compliance_items(contract.id, award_details)
        
        # Create post-award checklists
        checklists_created = await self._create_post_award_checklists(contract.id)
        
        return {
            'contract_id': contract.id,
            'contract_number': contract.contract_number,
            'deliverables_created': len(deliverables_created),
            'transitions_created': len(transitions_created),
            'compliance_items': len(compliance_items),
            'checklists_created': len(checklists_created),
            'status': 'contract_initiated'
        }
    
    async def _create_contract_deliverables(
        self,
        contract_id: int,
        award_details: Dict[str, Any]
    ) -> List[ContractDeliverable]:
        """Create contract deliverables"""
        
        deliverables = []
        deliverable_specs = award_details.get('deliverables', self._get_default_deliverables())
        
        for i, spec in enumerate(deliverable_specs):
            deliverable = ContractDeliverable(
                contract_id=contract_id,
                company_id=self.db.query(Contract).filter(Contract.id == contract_id).first().company_id,
                deliverable_number=spec.get('number', f"D-{i+1:03d}"),
                deliverable_title=spec['title'],
                deliverable_type=spec.get('type', 'report'),
                description=spec.get('description', ''),
                due_date=datetime.fromisoformat(spec['due_date']) if spec.get('due_date') else datetime.utcnow() + timedelta(days=30),
                acceptance_criteria=spec.get('acceptance_criteria', []),
                government_reviewer=spec.get('government_reviewer'),
                review_period_days=spec.get('review_period_days', 10),
                quality_requirements=spec.get('quality_requirements', []),
                compliance_requirements=spec.get('compliance_requirements', []),
                estimated_hours=spec.get('estimated_hours'),
                risk_level=RiskLevel(spec.get('risk_level', 'medium')),
                assigned_by=self.db.query(Contract).filter(Contract.id == contract_id).first().company_id
            )
            
            self.db.add(deliverable)
            deliverables.append(deliverable)
        
        self.db.commit()
        return deliverables
    
    async def _create_transition_plan(
        self,
        contract_id: int,
        award_details: Dict[str, Any]
    ) -> List[ContractTransition]:
        """Create contract transition plan"""
        
        transitions = []
        contract = self.db.query(Contract).filter(Contract.id == contract_id).first()
        
        # Standard transition phases
        transition_phases = [
            {
                'name': 'Contract Award Notification',
                'phase': TransitionPhase.PRE_AWARD,
                'description': 'Initial contract award processing and notification',
                'duration_days': 5
            },
            {
                'name': 'Kick-off Meeting Preparation',
                'phase': TransitionPhase.KICK_OFF,
                'description': 'Prepare for and conduct contract kick-off meeting',
                'duration_days': 10
            },
            {
                'name': 'Team Mobilization',
                'phase': TransitionPhase.MOBILIZATION,
                'description': 'Mobilize project team and establish work environment',
                'duration_days': 15
            },
            {
                'name': 'Knowledge Transfer',
                'phase': TransitionPhase.MOBILIZATION,
                'description': 'Transfer knowledge from incumbent or government',
                'duration_days': 20
            },
            {
                'name': 'Baseline Establishment',
                'phase': TransitionPhase.EXECUTION,
                'description': 'Establish baseline performance metrics and processes',
                'duration_days': 10
            }
        ]
        
        current_date = contract.start_date or datetime.utcnow()
        
        for phase_spec in transition_phases:
            transition = ContractTransition(
                contract_id=contract_id,
                company_id=contract.company_id,
                transition_name=phase_spec['name'],
                transition_phase=phase_spec['phase'],
                description=phase_spec['description'],
                planned_start_date=current_date,
                planned_end_date=current_date + timedelta(days=phase_spec['duration_days']),
                responsible_person=contract.program_manager,
                checklist_items=self._get_transition_checklist(phase_spec['phase']),
                success_criteria=self._get_transition_success_criteria(phase_spec['phase']),
                created_by=contract.company_id
            )
            
            self.db.add(transition)
            transitions.append(transition)
            
            current_date = transition.planned_end_date
        
        self.db.commit()
        return transitions
    
    async def _create_compliance_items(
        self,
        contract_id: int,
        award_details: Dict[str, Any]
    ) -> List[ComplianceItem]:
        """Create compliance tracking items"""
        
        compliance_items = []
        contract = self.db.query(Contract).filter(Contract.id == contract_id).first()
        
        # Standard compliance requirements
        standard_requirements = [
            {
                'title': 'Contract Data Requirements List (CDRL) Compliance',
                'source': 'Contract',
                'description': 'Ensure all CDRL items are delivered per contract requirements',
                'category': 'reporting',
                'criticality': RiskLevel.HIGH,
                'regulatory': True
            },
            {
                'title': 'Security Clearance Requirements',
                'source': 'Contract/NISPOM',
                'description': 'Maintain required security clearances for all personnel',
                'category': 'security',
                'criticality': RiskLevel.CRITICAL,
                'regulatory': True
            },
            {
                'title': 'Quality Assurance Program',
                'source': 'Contract',
                'description': 'Implement and maintain quality assurance program',
                'category': 'quality',
                'criticality': RiskLevel.MEDIUM,
                'regulatory': False
            },
            {
                'title': 'Financial Reporting Requirements',
                'source': 'FAR/Contract',
                'description': 'Submit required financial reports and documentation',
                'category': 'financial',
                'criticality': RiskLevel.HIGH,
                'regulatory': True
            },
            {
                'title': 'Property Management',
                'source': 'FAR 45',
                'description': 'Manage government property per FAR requirements',
                'category': 'property',
                'criticality': RiskLevel.MEDIUM,
                'regulatory': True
            }
        ]
        
        # Add custom compliance requirements from award details
        custom_requirements = award_details.get('compliance_requirements', [])
        all_requirements = standard_requirements + custom_requirements
        
        for req in all_requirements:
            compliance_item = ComplianceItem(
                contract_id=contract_id,
                company_id=contract.company_id,
                requirement_title=req['title'],
                requirement_source=req['source'],
                requirement_description=req['description'],
                compliance_category=req['category'],
                criticality_level=req.get('criticality', RiskLevel.MEDIUM),
                regulatory_requirement=req.get('regulatory', False),
                compliance_status=ComplianceStatus.NEEDS_REVIEW,
                next_review_date=datetime.utcnow() + timedelta(days=30),
                review_frequency_days=req.get('review_frequency', 90),
                responsible_person=contract.program_manager,
                created_by=contract.company_id
            )
            
            self.db.add(compliance_item)
            compliance_items.append(compliance_item)
        
        self.db.commit()
        return compliance_items
    
    async def _create_post_award_checklists(self, contract_id: int) -> List[PostAwardChecklist]:
        """Create post-award checklists"""
        
        checklists = []
        contract = self.db.query(Contract).filter(Contract.id == contract_id).first()
        
        # Standard checklist categories
        checklist_categories = [
            {
                'name': 'Administrative Setup',
                'category': 'administrative',
                'phase': TransitionPhase.PRE_AWARD,
                'items': [
                    'Contract file established',
                    'Insurance certificates obtained',
                    'Bonding requirements satisfied',
                    'Contract routing and signatures completed',
                    'Project codes established in accounting system'
                ]
            },
            {
                'name': 'Team Mobilization',
                'category': 'technical',
                'phase': TransitionPhase.MOBILIZATION,
                'items': [
                    'Key personnel identified and confirmed',
                    'Security clearances verified',
                    'Facility access arranged',
                    'Equipment and tools procured',
                    'Communication channels established'
                ]
            },
            {
                'name': 'Financial Setup',
                'category': 'financial',
                'phase': TransitionPhase.KICK_OFF,
                'items': [
                    'Budget baseline established',
                    'Cost accounting system configured',
                    'Invoicing procedures established',
                    'Financial reporting schedule confirmed',
                    'Subcontractor agreements executed'
                ]
            }
        ]
        
        for checklist_spec in checklist_categories:
            checklist_items = [
                {
                    'id': i + 1,
                    'item': item,
                    'completed': False,
                    'completed_date': None,
                    'notes': ''
                }
                for i, item in enumerate(checklist_spec['items'])
            ]
            
            checklist = PostAwardChecklist(
                contract_id=contract_id,
                company_id=contract.company_id,
                checklist_name=checklist_spec['name'],
                checklist_category=checklist_spec['category'],
                checklist_phase=checklist_spec['phase'],
                checklist_items=checklist_items,
                total_items=len(checklist_items),
                target_completion_date=datetime.utcnow() + timedelta(days=30),
                responsible_person=contract.program_manager,
                created_by=contract.company_id
            )
            
            self.db.add(checklist)
            checklists.append(checklist)
        
        self.db.commit()
        return checklists
    
    async def generate_transition_plan(
        self,
        contract_id: int,
        user_id: int,
        transition_requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate AI-powered transition plan"""
        
        contract = self.db.query(Contract).filter(
            Contract.id == contract_id,
            Contract.company_id == user_id
        ).first()
        
        if not contract:
            raise ValueError("Contract not found")
        
        # AI analysis for transition planning
        transition_analysis = await self._ai_analyze_transition_requirements(contract, transition_requirements)
        
        # Create detailed transition tasks
        transition_tasks = await self._generate_transition_tasks(transition_analysis)
        
        # Identify risks and mitigation strategies
        risk_analysis = await self._analyze_transition_risks(contract, transition_requirements)
        
        return {
            'contract_id': contract_id,
            'transition_analysis': transition_analysis,
            'transition_tasks': transition_tasks,
            'risk_analysis': risk_analysis,
            'estimated_duration_days': transition_analysis.get('estimated_duration', 45),
            'critical_path': transition_analysis.get('critical_path', []),
            'resource_requirements': transition_analysis.get('resources', [])
        }
    
    async def track_deliverable_progress(
        self,
        deliverable_id: int,
        user_id: int,
        progress_update: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Track and update deliverable progress"""
        
        deliverable = self.db.query(ContractDeliverable).filter(
            ContractDeliverable.id == deliverable_id,
            ContractDeliverable.company_id == user_id
        ).first()
        
        if not deliverable:
            raise ValueError("Deliverable not found")
        
        # Update progress
        deliverable.completion_percentage = progress_update.get('completion_percentage', deliverable.completion_percentage)
        deliverable.actual_hours = progress_update.get('actual_hours', deliverable.actual_hours)
        
        if progress_update.get('status'):
            deliverable.status = DeliverableStatus(progress_update['status'])
        
        # Check for completion
        if deliverable.completion_percentage >= 100:
            deliverable.status = DeliverableStatus.UNDER_REVIEW
        
        # Risk assessment
        risk_factors = await self._assess_deliverable_risks(deliverable)
        deliverable.risk_factors = risk_factors
        
        # Update risk level based on analysis
        if any(risk['level'] == 'high' for risk in risk_factors):
            deliverable.risk_level = RiskLevel.HIGH
        elif any(risk['level'] == 'medium' for risk in risk_factors):
            deliverable.risk_level = RiskLevel.MEDIUM
        
        self.db.commit()
        
        return {
            'deliverable_id': deliverable_id,
            'current_status': deliverable.status.value,
            'completion_percentage': deliverable.completion_percentage,
            'risk_level': deliverable.risk_level.value,
            'risk_factors': risk_factors,
            'on_schedule': deliverable.due_date >= datetime.utcnow(),
            'days_until_due': (deliverable.due_date - datetime.utcnow()).days if deliverable.due_date else None
        }
    
    async def conduct_compliance_assessment(
        self,
        contract_id: int,
        user_id: int
    ) -> Dict[str, Any]:
        """Conduct comprehensive compliance assessment"""
        
        contract = self.db.query(Contract).filter(
            Contract.id == contract_id,
            Contract.company_id == user_id
        ).first()
        
        if not contract:
            raise ValueError("Contract not found")
        
        compliance_items = self.db.query(ComplianceItem).filter(
            ComplianceItem.contract_id == contract_id
        ).all()
        
        assessment_results = []
        overall_compliance_score = 0
        critical_issues = []
        
        for item in compliance_items:
            # AI-powered compliance assessment
            item_assessment = await self._ai_assess_compliance_item(item)
            
            # Update compliance status
            item.compliance_status = ComplianceStatus(item_assessment.get('status', 'needs_review'))
            item.last_review_date = datetime.utcnow()
            item.next_review_date = datetime.utcnow() + timedelta(days=item.review_frequency_days)
            
            if item_assessment.get('evidence_gaps'):
                item.evidence_required = item_assessment['evidence_gaps']
            
            assessment_results.append({
                'item_id': item.id,
                'title': item.requirement_title,
                'status': item.compliance_status.value,
                'criticality': item.criticality_level.value,
                'assessment_score': item_assessment.get('score', 75),
                'gaps_identified': item_assessment.get('gaps', []),
                'recommendations': item_assessment.get('recommendations', [])
            })
            
            # Track critical issues
            if (item.compliance_status == ComplianceStatus.NON_COMPLIANT and 
                item.criticality_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]):
                critical_issues.append({
                    'item': item.requirement_title,
                    'criticality': item.criticality_level.value,
                    'issues': item_assessment.get('gaps', [])
                })
        
        # Calculate overall compliance score
        if assessment_results:
            overall_compliance_score = sum([r['assessment_score'] for r in assessment_results]) / len(assessment_results)
        
        self.db.commit()
        
        return {
            'contract_id': contract_id,
            'overall_compliance_score': round(overall_compliance_score, 1),
            'total_items_assessed': len(compliance_items),
            'compliant_items': len([r for r in assessment_results if r['status'] == 'compliant']),
            'non_compliant_items': len([r for r in assessment_results if r['status'] == 'non_compliant']),
            'critical_issues': critical_issues,
            'assessment_results': assessment_results,
            'recommendations': await self._generate_compliance_recommendations(assessment_results)
        }
    
    async def capture_lessons_learned(
        self,
        contract_id: int,
        user_id: int,
        lesson_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Capture lessons learned during contract execution"""
        
        contract = self.db.query(Contract).filter(
            Contract.id == contract_id,
            Contract.company_id == user_id
        ).first()
        
        if not contract:
            raise ValueError("Contract not found")
        
        # AI enhancement of lesson learned
        enhanced_lesson = await self._ai_enhance_lesson_learned(lesson_data)
        
        lesson = LessonsLearned(
            contract_id=contract_id,
            company_id=user_id,
            lesson_title=lesson_data['title'],
            lesson_category=lesson_data.get('category', 'general'),
            lesson_description=lesson_data['description'],
            situation_description=lesson_data.get('situation', ''),
            actions_taken=lesson_data.get('actions', ''),
            outcomes_achieved=lesson_data.get('outcomes', ''),
            what_worked_well=enhanced_lesson.get('what_worked_well'),
            what_could_improve=enhanced_lesson.get('what_could_improve'),
            root_cause_analysis=enhanced_lesson.get('root_cause'),
            recommendations=enhanced_lesson.get('recommendations', []),
            best_practices=enhanced_lesson.get('best_practices', []),
            applicable_situations=enhanced_lesson.get('applicable_situations', []),
            relevant_contract_types=enhanced_lesson.get('relevant_contract_types', []),
            estimated_value=enhanced_lesson.get('estimated_value'),
            captured_by=user_id,
            lesson_date=datetime.fromisoformat(lesson_data['lesson_date']) if lesson_data.get('lesson_date') else datetime.utcnow()
        )
        
        self.db.add(lesson)
        self.db.commit()
        self.db.refresh(lesson)
        
        return {
            'lesson_id': lesson.id,
            'title': lesson.lesson_title,
            'category': lesson.lesson_category,
            'recommendations': lesson.recommendations,
            'best_practices': lesson.best_practices,
            'estimated_value': lesson.estimated_value,
            'applicability': lesson.applicable_situations
        }
    
    def _get_default_deliverables(self) -> List[Dict[str, Any]]:
        """Get default deliverable structure"""
        return [
            {
                'title': 'Project Management Plan',
                'type': 'document',
                'description': 'Comprehensive project management plan',
                'due_date': (datetime.utcnow() + timedelta(days=30)).isoformat(),
                'risk_level': 'medium'
            },
            {
                'title': 'Monthly Progress Report',
                'type': 'report',
                'description': 'Monthly progress and status report',
                'due_date': (datetime.utcnow() + timedelta(days=30)).isoformat(),
                'risk_level': 'low'
            }
        ]
    
    def _get_transition_checklist(self, phase: TransitionPhase) -> List[Dict[str, Any]]:
        """Get checklist items for transition phase"""
        
        checklists = {
            TransitionPhase.PRE_AWARD: [
                {'item': 'Contract notification received', 'completed': False},
                {'item': 'Team notification completed', 'completed': False},
                {'item': 'Initial planning meeting scheduled', 'completed': False}
            ],
            TransitionPhase.KICK_OFF: [
                {'item': 'Kick-off meeting agenda prepared', 'completed': False},
                {'item': 'Government stakeholders identified', 'completed': False},
                {'item': 'Meeting logistics arranged', 'completed': False}
            ],
            TransitionPhase.MOBILIZATION: [
                {'item': 'Team members assigned', 'completed': False},
                {'item': 'Workspace established', 'completed': False},
                {'item': 'Equipment procured and installed', 'completed': False}
            ]
        }
        
        return checklists.get(phase, [])
    
    def _get_transition_success_criteria(self, phase: TransitionPhase) -> List[str]:
        """Get success criteria for transition phase"""
        
        criteria = {
            TransitionPhase.PRE_AWARD: [
                'All stakeholders notified within 24 hours',
                'Initial planning completed within 5 days'
            ],
            TransitionPhase.KICK_OFF: [
                'Successful kick-off meeting conducted',
                'Government approval received for project approach'
            ],
            TransitionPhase.MOBILIZATION: [
                'Team fully mobilized and operational',
                'All systems and processes established'
            ]
        }
        
        return criteria.get(phase, [])

    async def _ai_analyze_transition_requirements(
        self,
        contract: Contract,
        requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """AI analysis of transition requirements"""
        
        context = {
            'contract_details': {
                'type': contract.contract_type,
                'value': contract.contract_value,
                'duration': contract.base_period_months,
                'agency': contract.contracting_agency
            },
            'requirements': requirements
        }
        
        prompt = f"""Analyze contract transition requirements and create detailed transition plan:

CONTRACT CONTEXT: {json.dumps(context, indent=2)}

Provide:
1. Transition phases with timelines
2. Critical path activities
3. Resource requirements
4. Risk factors and mitigation
5. Success metrics

Format as structured JSON with specific, actionable recommendations."""

        try:
            response = await self.ai_service.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert government contract transition specialist."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            # Parse AI response
            return self._parse_transition_analysis(response.choices[0].message.content)
            
        except Exception as e:
            return self._generate_default_transition_analysis(contract)

    def _parse_transition_analysis(self, response: str) -> Dict[str, Any]:
        """Parse AI transition analysis response"""
        try:
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            else:
                json_str = response
            
            return json.loads(json_str)
        except:
            return {'estimated_duration': 45, 'phases': [], 'risks': []}

    def _generate_default_transition_analysis(self, contract: Contract) -> Dict[str, Any]:
        """Generate default transition analysis"""
        return {
            'estimated_duration': 45,
            'phases': [
                {'name': 'Pre-Award Setup', 'duration': 5, 'critical': True},
                {'name': 'Kick-off', 'duration': 10, 'critical': True},
                {'name': 'Mobilization', 'duration': 20, 'critical': True},
                {'name': 'Baseline', 'duration': 10, 'critical': False}
            ],
            'critical_path': ['Pre-Award Setup', 'Kick-off', 'Mobilization'],
            'resources': ['Program Manager', 'Technical Team', 'Administrative Support'],
            'risks': ['Delayed clearances', 'Resource availability', 'Government coordination']
        }

    async def _generate_transition_tasks(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate detailed transition tasks"""
        # Implementation for task generation
        return []

    async def _analyze_transition_risks(self, contract: Contract, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze transition risks"""
        # Implementation for risk analysis
        return {'high_risks': [], 'medium_risks': [], 'low_risks': []}

    async def _assess_deliverable_risks(self, deliverable: ContractDeliverable) -> List[Dict[str, Any]]:
        """Assess risks for specific deliverable"""
        risks = []
        
        # Schedule risk
        if deliverable.due_date and deliverable.due_date <= datetime.utcnow() + timedelta(days=7):
            risks.append({
                'type': 'schedule',
                'level': 'high',
                'description': 'Deliverable due within 7 days',
                'mitigation': 'Accelerate work or request extension'
            })
        
        # Completion risk
        if deliverable.completion_percentage < 50 and deliverable.due_date and deliverable.due_date <= datetime.utcnow() + timedelta(days=14):
            risks.append({
                'type': 'completion',
                'level': 'medium',
                'description': 'Low completion percentage with approaching deadline',
                'mitigation': 'Add resources or adjust scope'
            })
        
        return risks

    async def _ai_assess_compliance_item(self, item: ComplianceItem) -> Dict[str, Any]:
        """AI assessment of compliance item"""
        
        prompt = f"""Assess compliance status for this requirement:

REQUIREMENT: {item.requirement_title}
SOURCE: {item.requirement_source}
DESCRIPTION: {item.requirement_description}
CATEGORY: {item.compliance_category}
CRITICALITY: {item.criticality_level.value}

Current status: {item.compliance_status.value}
Last review: {item.last_review_date}

Provide:
1. Compliance assessment score (0-100)
2. Current status (compliant/non_compliant/needs_review)
3. Gaps identified
4. Evidence requirements
5. Recommendations

Format as JSON."""

        try:
            response = await self.ai_service.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a government contracts compliance specialist."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            return self._parse_compliance_assessment(response.choices[0].message.content)
            
        except Exception:
            return {
                'score': 75,
                'status': 'needs_review',
                'gaps': [],
                'recommendations': []
            }

    def _parse_compliance_assessment(self, response: str) -> Dict[str, Any]:
        """Parse AI compliance assessment response"""
        try:
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            else:
                json_str = response
            
            return json.loads(json_str)
        except:
            return {'score': 75, 'status': 'needs_review', 'gaps': [], 'recommendations': []}

    async def _generate_compliance_recommendations(self, assessment_results: List[Dict[str, Any]]) -> List[str]:
        """Generate overall compliance recommendations"""
        
        recommendations = []
        
        # Identify patterns in assessment results
        non_compliant_items = [r for r in assessment_results if r['status'] == 'non_compliant']
        high_risk_items = [r for r in assessment_results if r.get('criticality') in ['high', 'critical']]
        
        if non_compliant_items:
            recommendations.append(f"Immediate attention required for {len(non_compliant_items)} non-compliant items")
        
        if high_risk_items:
            recommendations.append(f"Prioritize review of {len(high_risk_items)} high-criticality items")
        
        # Add specific recommendations based on common gaps
        all_gaps = []
        for result in assessment_results:
            all_gaps.extend(result.get('gaps_identified', []))
        
        if 'documentation' in str(all_gaps).lower():
            recommendations.append("Improve documentation practices and evidence collection")
        
        if 'training' in str(all_gaps).lower():
            recommendations.append("Enhance staff training on compliance requirements")
        
        return recommendations

    async def _ai_enhance_lesson_learned(self, lesson_data: Dict[str, Any]) -> Dict[str, Any]:
        """AI enhancement of lessons learned"""
        
        prompt = f"""Enhance this lesson learned with deeper analysis:

LESSON: {lesson_data.get('title', '')}
DESCRIPTION: {lesson_data.get('description', '')}
SITUATION: {lesson_data.get('situation', '')}
ACTIONS: {lesson_data.get('actions', '')}
OUTCOMES: {lesson_data.get('outcomes', '')}

Provide:
1. Root cause analysis
2. What worked well
3. What could be improved
4. Specific recommendations
5. Best practices
6. Applicable situations
7. Estimated business value

Format as structured JSON."""

        try:
            response = await self.ai_service.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert in organizational learning and knowledge management."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            return self._parse_lesson_enhancement(response.choices[0].message.content)
            
        except Exception:
            return {
                'recommendations': ['Document process improvements'],
                'best_practices': ['Regular review and feedback'],
                'applicable_situations': ['Similar contract types']
            }

    def _parse_lesson_enhancement(self, response: str) -> Dict[str, Any]:
        """Parse AI lesson enhancement response"""
        try:
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            else:
                json_str = response
            
            return json.loads(json_str)
        except:
            return {'recommendations': [], 'best_practices': [], 'applicable_situations': []}