from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import json
import re

from models.proposals import (
    Proposal, ProposalVolume, ProposalSection, ProposalReview, 
    ProposalSubmission, ProposalTemplate, ProposalLibrary,
    ProposalStatus, VolumeType, ComplianceStatus, ReadinessGate
)
from models.opportunity import Opportunity
from models.financial import FinancialProject
from models.resources import DeliveryPlan
from services.ai_service import AIService

class ProposalManagementEngine:
    """AI-powered proposal management and creation engine"""
    
    def __init__(self, db: Session):
        self.db = db
        self.ai_service = AIService()
    
    async def create_proposal_from_opportunity(
        self,
        user_id: int,
        opportunity_id: int,
        project_id: Optional[int] = None,
        delivery_plan_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Create comprehensive proposal structure from opportunity"""
        
        opportunity = self.db.query(Opportunity).filter(Opportunity.id == opportunity_id).first()
        if not opportunity:
            raise ValueError("Opportunity not found")
        
        # Generate proposal number
        proposal_count = self.db.query(Proposal).filter(
            Proposal.created_by == user_id
        ).count()
        proposal_number = f"PROP-{datetime.now().year}-{proposal_count + 1:04d}"
        
        # AI analysis of RFP for proposal structure
        proposal_structure = await self._ai_analyze_rfp_structure(opportunity)
        
        # Create proposal
        proposal = Proposal(
            opportunity_id=opportunity_id,
            project_id=project_id,
            delivery_plan_id=delivery_plan_id,
            proposal_number=proposal_number,
            proposal_title=f"Proposal for {opportunity.title}",
            solicitation_number=opportunity.solicitation_number,
            submission_deadline=opportunity.response_deadline,
            proposal_sections=proposal_structure['sections'],
            compliance_matrix=proposal_structure['compliance_matrix'],
            evaluation_criteria=proposal_structure['evaluation_criteria'],
            proposal_manager=user_id,
            readiness_gates_status=self._initialize_readiness_gates(),
            ai_recommendations=proposal_structure.get('ai_recommendations', []),
            created_by=user_id
        )
        
        self.db.add(proposal)
        self.db.commit()
        self.db.refresh(proposal)
        
        # Create proposal volumes and sections
        volumes_created = await self._create_proposal_volumes(proposal.id, proposal_structure)
        sections_created = await self._create_proposal_sections(proposal.id, proposal_structure)
        
        # Initial readiness gate assessment
        readiness_assessment = await self._assess_readiness_gates(proposal.id)
        
        return {
            'proposal_id': proposal.id,
            'proposal_number': proposal.proposal_number,
            'volumes_created': len(volumes_created),
            'sections_created': len(sections_created),
            'readiness_gates': readiness_assessment,
            'ai_insights': proposal_structure.get('ai_recommendations', [])
        }
    
    async def _ai_analyze_rfp_structure(self, opportunity: Opportunity) -> Dict[str, Any]:
        """AI analysis of RFP to determine proposal structure"""
        
        context = {
            'opportunity_details': {
                'title': opportunity.title,
                'description': opportunity.description[:2000],  # Limit for token efficiency
                'agency': opportunity.agency,
                'naics_code': opportunity.naics_code,
                'solicitation_number': opportunity.solicitation_number
            }
        }
        
        prompt = self._create_rfp_analysis_prompt(context)
        
        try:
            response = await self.ai_service.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": self._get_proposal_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2500
            )
            
            ai_analysis = self._parse_ai_proposal_response(response.choices[0].message.content)
            return ai_analysis
            
        except Exception as e:
            print(f"AI RFP analysis failed: {e}")
            return self._generate_default_proposal_structure(opportunity)
    
    async def _create_proposal_volumes(self, proposal_id: int, structure: Dict[str, Any]) -> List[ProposalVolume]:
        """Create proposal volumes based on RFP requirements"""
        
        volumes = []
        volume_specs = structure.get('volumes', self._get_default_volumes())
        
        for i, vol_spec in enumerate(volume_specs):
            volume = ProposalVolume(
                proposal_id=proposal_id,
                volume_name=vol_spec['name'],
                volume_type=VolumeType(vol_spec['type']),
                volume_number=i + 1,
                description=vol_spec.get('description'),
                page_limit=vol_spec.get('page_limit'),
                word_limit=vol_spec.get('word_limit'),
                required_sections=vol_spec.get('required_sections', []),
                optional_sections=vol_spec.get('optional_sections', [])
            )
            
            self.db.add(volume)
            volumes.append(volume)
        
        self.db.commit()
        return volumes
    
    async def _create_proposal_sections(self, proposal_id: int, structure: Dict[str, Any]) -> List[ProposalSection]:
        """Create proposal sections based on RFP requirements"""
        
        sections = []
        section_specs = structure.get('sections', self._get_default_sections())
        
        for section_spec in section_specs:
            section = ProposalSection(
                proposal_id=proposal_id,
                section_number=section_spec['number'],
                section_title=section_spec['title'],
                section_type=section_spec.get('type', 'content'),
                content_outline=section_spec.get('outline', {}),
                requirements=section_spec.get('requirements', []),
                depends_on_sections=section_spec.get('dependencies', [])
            )
            
            self.db.add(section)
            sections.append(section)
        
        self.db.commit()
        return sections
    
    async def generate_section_content(
        self,
        section_id: int,
        user_id: int,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate AI-powered content for proposal section"""
        
        section = self.db.query(ProposalSection).filter(ProposalSection.id == section_id).first()
        if not section:
            raise ValueError("Section not found")
        
        proposal = self.db.query(Proposal).filter(Proposal.id == section.proposal_id).first()
        opportunity = self.db.query(Opportunity).filter(Opportunity.id == proposal.opportunity_id).first()
        
        # Get relevant library content
        library_content = await self._get_relevant_library_content(section, user_id)
        
        # Build context for AI content generation
        ai_context = {
            'section_details': {
                'title': section.section_title,
                'type': section.section_type,
                'requirements': section.requirements or [],
                'outline': section.content_outline or {}
            },
            'opportunity_context': {
                'title': opportunity.title,
                'agency': opportunity.agency,
                'description': opportunity.description[:1500]
            },
            'proposal_context': {
                'win_strategy': proposal.win_strategy,
                'value_proposition': proposal.value_proposition,
                'discriminators': proposal.discriminators or []
            },
            'library_content': library_content,
            'additional_context': context or {}
        }
        
        # Generate content using AI
        content_result = await self._ai_generate_section_content(ai_context)
        
        # Update section with generated content
        section.content = content_result['content']
        section.ai_generated_content = True
        section.ai_suggestions = content_result.get('suggestions', [])
        section.completion_percentage = content_result.get('completion_percentage', 75.0)
        section.word_count = len(content_result['content'].split()) if content_result['content'] else 0
        
        self.db.commit()
        
        return {
            'section_id': section_id,
            'content': content_result['content'],
            'word_count': section.word_count,
            'completion_percentage': section.completion_percentage,
            'ai_suggestions': content_result.get('suggestions', []),
            'quality_score': content_result.get('quality_score', 80.0)
        }
    
    async def check_compliance(self, proposal_id: int, user_id: int) -> Dict[str, Any]:
        """Comprehensive compliance check for proposal"""
        
        proposal = self.db.query(Proposal).filter(
            Proposal.id == proposal_id,
            Proposal.created_by == user_id
        ).first()
        
        if not proposal:
            raise ValueError("Proposal not found")
        
        opportunity = self.db.query(Opportunity).filter(Opportunity.id == proposal.opportunity_id).first()
        sections = self.db.query(ProposalSection).filter(ProposalSection.proposal_id == proposal_id).all()
        
        # AI compliance analysis
        compliance_result = await self._ai_compliance_analysis(proposal, opportunity, sections)
        
        # Update compliance status for each section
        compliance_issues = []
        for section in sections:
            section_compliance = compliance_result.get('sections', {}).get(str(section.id), {})
            section.compliance_status = ComplianceStatus(section_compliance.get('status', 'needs_review'))
            section.compliance_notes = section_compliance.get('notes', '')
            
            if section.compliance_status == ComplianceStatus.NON_COMPLIANT:
                compliance_issues.append({
                    'section_id': section.id,
                    'section_title': section.section_title,
                    'issues': section_compliance.get('issues', [])
                })
        
        # Update overall compliance score
        proposal.compliance_score = compliance_result.get('overall_score', 75.0)
        
        self.db.commit()
        
        return {
            'proposal_id': proposal_id,
            'overall_compliance_score': proposal.compliance_score,
            'compliant_sections': len([s for s in sections if s.compliance_status == ComplianceStatus.COMPLIANT]),
            'non_compliant_sections': len([s for s in sections if s.compliance_status == ComplianceStatus.NON_COMPLIANT]),
            'compliance_issues': compliance_issues,
            'recommendations': compliance_result.get('recommendations', [])
        }
    
    async def assess_readiness_gates(self, proposal_id: int, user_id: int) -> Dict[str, Any]:
        """Assess proposal readiness gates"""
        
        proposal = self.db.query(Proposal).filter(
            Proposal.id == proposal_id,
            Proposal.created_by == user_id
        ).first()
        
        if not proposal:
            raise ValueError("Proposal not found")
        
        # Check each readiness gate
        gate_assessments = {}
        
        # Opportunity Analysis Gate
        gate_assessments['opportunity_analysis'] = await self._check_opportunity_analysis_gate(proposal)
        
        # Financial Approval Gate
        gate_assessments['financial_approval'] = await self._check_financial_approval_gate(proposal)
        
        # Resource Allocation Gate
        gate_assessments['resource_allocation'] = await self._check_resource_allocation_gate(proposal)
        
        # Teaming Confirmed Gate
        gate_assessments['teaming_confirmed'] = await self._check_teaming_confirmed_gate(proposal)
        
        # Compliance Verified Gate
        gate_assessments['compliance_verified'] = await self._check_compliance_verified_gate(proposal)
        
        # Content Complete Gate
        gate_assessments['content_complete'] = await self._check_content_complete_gate(proposal)
        
        # Quality Reviewed Gate
        gate_assessments['quality_reviewed'] = await self._check_quality_reviewed_gate(proposal)
        
        # Executive Approved Gate
        gate_assessments['executive_approved'] = await self._check_executive_approved_gate(proposal)
        
        # Update proposal readiness status
        proposal.readiness_gates_status = gate_assessments
        
        # Calculate overall readiness
        passed_gates = len([g for g in gate_assessments.values() if g.get('passed', False)])
        total_gates = len(gate_assessments)
        readiness_percentage = (passed_gates / total_gates * 100) if total_gates > 0 else 0
        
        # Determine if proposal is ready for submission
        ready_for_submission = all(g.get('passed', False) for g in gate_assessments.values())
        
        self.db.commit()
        
        return {
            'proposal_id': proposal_id,
            'readiness_percentage': readiness_percentage,
            'passed_gates': passed_gates,
            'total_gates': total_gates,
            'ready_for_submission': ready_for_submission,
            'gate_assessments': gate_assessments,
            'blocking_issues': [g['issues'] for g in gate_assessments.values() if not g.get('passed', False)]
        }
    
    async def conduct_proposal_review(
        self,
        proposal_id: int,
        review_type: str,
        reviewer_id: int,
        sections_to_review: List[int] = None
    ) -> Dict[str, Any]:
        """Conduct structured proposal review"""
        
        proposal = self.db.query(Proposal).filter(Proposal.id == proposal_id).first()
        if not proposal:
            raise ValueError("Proposal not found")
        
        # Get sections to review
        if sections_to_review:
            sections = self.db.query(ProposalSection).filter(
                ProposalSection.id.in_(sections_to_review)
            ).all()
        else:
            sections = self.db.query(ProposalSection).filter(
                ProposalSection.proposal_id == proposal_id
            ).all()
        
        # AI-powered review
        review_result = await self._ai_conduct_review(proposal, sections, review_type)
        
        # Create review record
        review = ProposalReview(
            proposal_id=proposal_id,
            review_type=review_type,
            review_name=f"{review_type.title()} Review - {datetime.now().strftime('%Y-%m-%d')}",
            review_date=datetime.utcnow(),
            reviewer_id=reviewer_id,
            reviewer_role="internal",
            sections_reviewed=[s.id for s in sections],
            review_criteria=review_result.get('criteria', []),
            overall_score=review_result.get('overall_score', 7.0),
            strengths=review_result.get('strengths', []),
            weaknesses=review_result.get('weaknesses', []),
            recommendations=review_result.get('recommendations', []),
            technical_score=review_result.get('technical_score'),
            management_score=review_result.get('management_score'),
            pricing_score=review_result.get('pricing_score'),
            compliance_score=review_result.get('compliance_score'),
            general_comments=review_result.get('general_comments'),
            critical_issues=review_result.get('critical_issues', []),
            action_items=review_result.get('action_items', [])
        )
        
        self.db.add(review)
        self.db.commit()
        self.db.refresh(review)
        
        return {
            'review_id': review.id,
            'overall_score': review.overall_score,
            'sections_reviewed': len(sections),
            'strengths': review.strengths,
            'weaknesses': review.weaknesses,
            'critical_issues': review.critical_issues,
            'action_items': review.action_items,
            'recommendations': review.recommendations
        }
    
    def _initialize_readiness_gates(self) -> Dict[str, Dict[str, Any]]:
        """Initialize readiness gates status"""
        return {
            gate.value: {
                'passed': False,
                'checked_date': None,
                'issues': [],
                'notes': ''
            }
            for gate in ReadinessGate
        }
    
    def _get_proposal_system_prompt(self) -> str:
        """System prompt for proposal AI analysis"""
        return """You are an expert government contracting proposal analyst and writer.

Analyze RFPs and create proposal structures that:
1. Ensure complete compliance with all requirements
2. Address evaluation criteria effectively
3. Structure content for maximum impact
4. Include all necessary volumes and sections
5. Identify potential risks and opportunities

Respond in JSON format with detailed proposal structure and recommendations."""
    
    def _create_rfp_analysis_prompt(self, context: Dict) -> str:
        """Create RFP analysis prompt"""
        return f"""Analyze this government RFP and create a comprehensive proposal structure:

OPPORTUNITY: {json.dumps(context['opportunity_details'], indent=2)}

Provide:
1. Required volumes and their specifications
2. Detailed section structure with requirements
3. Compliance matrix identifying all requirements
4. Evaluation criteria analysis
5. Recommendations for competitive positioning

Focus on creating a winning proposal structure that addresses all RFP requirements and maximizes evaluation scores."""
    
    def _parse_ai_proposal_response(self, response: str) -> Dict[str, Any]:
        """Parse AI proposal analysis response"""
        try:
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
            else:
                json_str = response
            
            return json.loads(json_str)
        except:
            return self._generate_default_proposal_structure()
    
    def _generate_default_proposal_structure(self, opportunity: Optional[Opportunity] = None) -> Dict[str, Any]:
        """Generate default proposal structure when AI fails"""
        return {
            'volumes': [
                {
                    'name': 'Technical Volume',
                    'type': 'technical',
                    'description': 'Technical approach and solution',
                    'page_limit': 50
                },
                {
                    'name': 'Management Volume',
                    'type': 'management',
                    'description': 'Management approach and team',
                    'page_limit': 25
                },
                {
                    'name': 'Past Performance Volume',
                    'type': 'past_performance',
                    'description': 'Past performance examples',
                    'page_limit': 15
                },
                {
                    'name': 'Pricing Volume',
                    'type': 'pricing',
                    'description': 'Cost proposal and pricing',
                    'page_limit': 10
                }
            ],
            'sections': [
                {'number': '1.0', 'title': 'Executive Summary', 'type': 'executive_summary'},
                {'number': '2.0', 'title': 'Technical Approach', 'type': 'technical'},
                {'number': '3.0', 'title': 'Management Approach', 'type': 'management'},
                {'number': '4.0', 'title': 'Past Performance', 'type': 'past_performance'},
                {'number': '5.0', 'title': 'Pricing', 'type': 'pricing'}
            ],
            'compliance_matrix': [],
            'evaluation_criteria': [],
            'ai_recommendations': ['Manual proposal structure review recommended']
        }
    
    def _get_default_volumes(self) -> List[Dict[str, Any]]:
        """Get default volume structure"""
        return [
            {'name': 'Technical Volume', 'type': 'technical', 'page_limit': 50},
            {'name': 'Management Volume', 'type': 'management', 'page_limit': 25},
            {'name': 'Past Performance', 'type': 'past_performance', 'page_limit': 15},
            {'name': 'Pricing Volume', 'type': 'pricing', 'page_limit': 10}
        ]
    
    def _get_default_sections(self) -> List[Dict[str, Any]]:
        """Get default section structure"""
        return [
            {'number': '1.0', 'title': 'Executive Summary', 'type': 'executive_summary'},
            {'number': '2.0', 'title': 'Technical Approach', 'type': 'technical'},
            {'number': '3.0', 'title': 'Management Approach', 'type': 'management'},
            {'number': '4.0', 'title': 'Past Performance', 'type': 'past_performance'},
            {'number': '5.0', 'title': 'Pricing Summary', 'type': 'pricing'}
        ]