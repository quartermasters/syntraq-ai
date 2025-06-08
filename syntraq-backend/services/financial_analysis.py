from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import numpy as np
import json

from models.financial import (
    FinancialProject, ProjectBudget, CashFlowProjection, 
    ProjectExpense, FinancialAlert, CompanyFinancials, ProjectStatus
)
from models.opportunity import Opportunity
from services.ai_service import AIService

class FinancialAnalysisService:
    """AI-powered financial analysis and CFO advisory service"""
    
    def __init__(self, db: Session):
        self.db = db
        self.ai_service = AIService()
    
    async def create_project_budget(
        self, 
        project_id: int, 
        budget_data: Dict[str, Any],
        user_id: int
    ) -> Dict[str, Any]:
        """Create comprehensive project budget with AI optimization"""
        
        project = self.db.query(FinancialProject).filter(FinancialProject.id == project_id).first()
        if not project:
            raise ValueError("Project not found")
        
        # Get company financial context
        company_financials = await self._get_company_context(user_id)
        
        # AI budget optimization
        optimized_budget = await self._ai_optimize_budget(budget_data, company_financials, project)
        
        # Calculate all financial metrics
        budget_calculations = self._calculate_budget_metrics(optimized_budget)
        
        # Create budget record
        budget = ProjectBudget(
            project_id=project_id,
            **budget_calculations
        )
        
        self.db.add(budget)
        self.db.commit()
        self.db.refresh(budget)
        
        # Generate cash flow projections
        await self._generate_cash_flow_projections(project_id, budget_calculations)
        
        # Check for financial risks
        await self._assess_financial_risks(project_id, budget_calculations)
        
        return {
            'budget_id': budget.id,
            'total_cost': budget.total_cost,
            'total_price': budget.total_price,
            'gross_margin': budget.total_price - budget.total_cost,
            'margin_percentage': ((budget.total_price - budget.total_cost) / budget.total_price * 100) if budget.total_price > 0 else 0,
            'ai_recommendations': optimized_budget.get('recommendations', [])
        }
    
    async def _ai_optimize_budget(
        self, 
        budget_data: Dict[str, Any], 
        company_context: Dict[str, Any],
        project: FinancialProject
    ) -> Dict[str, Any]:
        """AI-powered budget optimization and recommendations"""
        
        context = {
            'project_details': {
                'name': project.project_name,
                'estimated_value': project.estimated_value,
                'performance_period': project.performance_period,
                'contract_type': project.contract_type,
                'client_agency': project.client_agency
            },
            'proposed_budget': budget_data,
            'company_context': company_context,
            'industry_benchmarks': await self._get_industry_benchmarks(project)
        }
        
        prompt = self._create_budget_optimization_prompt(context)
        
        try:
            response = await self.ai_service.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": self._get_cfo_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            ai_analysis = self._parse_ai_budget_response(response.choices[0].message.content)
            
            # Apply AI recommendations to budget
            optimized_budget = budget_data.copy()
            optimized_budget.update(ai_analysis.get('optimizations', {}))
            optimized_budget['recommendations'] = ai_analysis.get('recommendations', [])
            optimized_budget['risk_factors'] = ai_analysis.get('risk_factors', [])
            
            return optimized_budget
            
        except Exception as e:
            print(f"AI budget optimization failed: {e}")
            return {
                **budget_data,
                'recommendations': ['Manual budget review recommended'],
                'risk_factors': ['AI analysis unavailable']
            }
    
    def _calculate_budget_metrics(self, budget_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate comprehensive budget metrics"""
        
        # Labor calculations
        direct_labor_cost = budget_data.get('direct_labor_hours', 0) * budget_data.get('direct_labor_rate', 0)
        fringe_rate = budget_data.get('fringe_benefits_rate', 30.0) / 100
        fringe_cost = direct_labor_cost * fringe_rate
        
        # Direct costs
        total_labor_cost = direct_labor_cost + fringe_cost + budget_data.get('indirect_labor_cost', 0)
        materials_cost = budget_data.get('materials_cost', 0)
        equipment_cost = budget_data.get('equipment_cost', 0)
        travel_cost = budget_data.get('travel_cost', 0)
        subcontractor_cost = budget_data.get('subcontractor_cost', 0)
        other_direct_costs = budget_data.get('other_direct_costs', 0)
        
        total_direct_cost = (total_labor_cost + materials_cost + equipment_cost + 
                            travel_cost + subcontractor_cost + other_direct_costs)
        
        # Indirect costs
        overhead_rate = budget_data.get('overhead_rate', 100.0) / 100
        overhead_cost = total_direct_cost * overhead_rate
        
        ga_rate = budget_data.get('ga_rate', 15.0) / 100
        ga_cost = (total_direct_cost + overhead_cost) * ga_rate
        
        total_indirect_cost = overhead_cost + ga_cost
        total_cost = total_direct_cost + total_indirect_cost
        
        # Fee calculation
        fee_percentage = budget_data.get('fee_percentage', 10.0)
        fee_amount = total_cost * (fee_percentage / 100)
        total_price = total_cost + fee_amount
        
        return {
            'direct_labor_hours': budget_data.get('direct_labor_hours', 0),
            'direct_labor_rate': budget_data.get('direct_labor_rate', 0),
            'direct_labor_cost': direct_labor_cost,
            'indirect_labor_cost': budget_data.get('indirect_labor_cost', 0),
            'fringe_benefits_rate': budget_data.get('fringe_benefits_rate', 30.0),
            'fringe_benefits_cost': fringe_cost,
            'materials_cost': materials_cost,
            'equipment_cost': equipment_cost,
            'travel_cost': travel_cost,
            'subcontractor_cost': subcontractor_cost,
            'other_direct_costs': other_direct_costs,
            'overhead_rate': budget_data.get('overhead_rate', 100.0),
            'overhead_cost': overhead_cost,
            'ga_rate': budget_data.get('ga_rate', 15.0),
            'ga_cost': ga_cost,
            'total_direct_cost': total_direct_cost,
            'total_indirect_cost': total_indirect_cost,
            'total_cost': total_cost,
            'fee_percentage': fee_percentage,
            'fee_amount': fee_amount,
            'total_price': total_price,
            'cost_by_month': self._distribute_costs_by_month(total_cost, budget_data.get('performance_period', 12)),
            'cost_by_task': budget_data.get('cost_by_task', {})
        }
    
    async def _generate_cash_flow_projections(self, project_id: int, budget_data: Dict[str, Any]) -> None:
        """Generate detailed cash flow projections"""
        
        project = self.db.query(FinancialProject).filter(FinancialProject.id == project_id).first()
        if not project:
            return
        
        # Payment assumptions
        payment_terms = 30  # days
        collection_period = 45  # days
        invoice_frequency = "monthly"
        
        # Monthly cost distribution
        monthly_costs = budget_data.get('cost_by_month', {})
        performance_period = project.performance_period or 12
        
        # Calculate monthly inflows and outflows
        monthly_projections = []
        cumulative_cash_flow = 0
        
        for month in range(1, min(performance_period + 1, 25)):  # Up to 24 months
            # Outflows (costs incurred)
            outflow = monthly_costs.get(str(month), budget_data['total_cost'] / performance_period)
            
            # Inflows (payments received with delay)
            if invoice_frequency == "monthly" and month > 2:  # 2-month payment delay
                inflow = outflow * 1.1  # Include fee/margin
            else:
                inflow = 0
            
            net_flow = inflow - outflow
            cumulative_cash_flow += net_flow
            
            monthly_projections.append({
                'month': month,
                'inflow': inflow,
                'outflow': outflow,
                'net_flow': net_flow,
                'cumulative': cumulative_cash_flow
            })
        
        # Store projections for first 6 months in columns, rest in JSON
        cash_flow = CashFlowProjection(
            project_id=project_id,
            month_1_inflow=monthly_projections[0]['inflow'] if len(monthly_projections) > 0 else 0,
            month_1_outflow=monthly_projections[0]['outflow'] if len(monthly_projections) > 0 else 0,
            month_2_inflow=monthly_projections[1]['inflow'] if len(monthly_projections) > 1 else 0,
            month_2_outflow=monthly_projections[1]['outflow'] if len(monthly_projections) > 1 else 0,
            month_3_inflow=monthly_projections[2]['inflow'] if len(monthly_projections) > 2 else 0,
            month_3_outflow=monthly_projections[2]['outflow'] if len(monthly_projections) > 2 else 0,
            month_4_inflow=monthly_projections[3]['inflow'] if len(monthly_projections) > 3 else 0,
            month_4_outflow=monthly_projections[3]['outflow'] if len(monthly_projections) > 3 else 0,
            month_5_inflow=monthly_projections[4]['inflow'] if len(monthly_projections) > 4 else 0,
            month_5_outflow=monthly_projections[4]['outflow'] if len(monthly_projections) > 4 else 0,
            month_6_inflow=monthly_projections[5]['inflow'] if len(monthly_projections) > 5 else 0,
            month_6_outflow=monthly_projections[5]['outflow'] if len(monthly_projections) > 5 else 0,
            extended_projections=monthly_projections[6:] if len(monthly_projections) > 6 else [],
            cumulative_cash_flow=[p['cumulative'] for p in monthly_projections],
            peak_cash_requirement=min([p['cumulative'] for p in monthly_projections]),
            payment_terms=payment_terms,
            collection_period=collection_period
        )
        
        self.db.add(cash_flow)
        self.db.commit()
    
    async def _assess_financial_risks(self, project_id: int, budget_data: Dict[str, Any]) -> None:
        """Assess financial risks and generate alerts"""
        
        project = self.db.query(FinancialProject).filter(FinancialProject.id == project_id).first()
        if not project:
            return
        
        alerts = []
        
        # Margin analysis
        margin_percentage = ((budget_data['total_price'] - budget_data['total_cost']) / 
                           budget_data['total_price'] * 100) if budget_data['total_price'] > 0 else 0
        
        if margin_percentage < 5:
            alerts.append({
                'alert_type': 'low_margin',
                'severity': 'high',
                'title': 'Low Profit Margin Warning',
                'message': f'Project margin is only {margin_percentage:.1f}%, below recommended 15% minimum',
                'threshold_value': 15.0,
                'current_value': margin_percentage,
                'recommended_actions': [
                    'Review labor rates for competitiveness',
                    'Consider reducing indirect cost rates',
                    'Evaluate scope for potential reductions'
                ]
            })
        
        # Cash flow analysis
        cash_flow = self.db.query(CashFlowProjection).filter(
            CashFlowProjection.project_id == project_id
        ).first()
        
        if cash_flow and cash_flow.peak_cash_requirement < -100000:  # $100k negative
            alerts.append({
                'alert_type': 'negative_cash_flow',
                'severity': 'medium',
                'title': 'Negative Cash Flow Alert',
                'message': f'Peak cash requirement: ${abs(cash_flow.peak_cash_requirement):,.0f}',
                'threshold_value': -100000,
                'current_value': cash_flow.peak_cash_requirement,
                'recommended_actions': [
                    'Arrange line of credit for cash flow gaps',
                    'Negotiate faster payment terms',
                    'Consider milestone-based payments'
                ]
            })
        
        # Save alerts
        for alert_data in alerts:
            alert = FinancialAlert(
                project_id=project_id,
                **alert_data
            )
            self.db.add(alert)
        
        if alerts:
            self.db.commit()
    
    async def calculate_project_roi(self, project_id: int) -> Dict[str, Any]:
        """Calculate comprehensive ROI analysis"""
        
        project = self.db.query(FinancialProject).filter(FinancialProject.id == project_id).first()
        if not project:
            raise ValueError("Project not found")
        
        budget = self.db.query(ProjectBudget).filter(
            ProjectBudget.project_id == project_id
        ).order_by(ProjectBudget.created_at.desc()).first()
        
        if not budget:
            raise ValueError("No budget found for project")
        
        # Basic ROI calculations
        investment = budget.total_cost
        revenue = budget.total_price
        gross_profit = revenue - investment
        roi_percentage = (gross_profit / investment * 100) if investment > 0 else 0
        
        # Time-adjusted metrics
        performance_period = project.performance_period or 12
        annualized_roi = roi_percentage * (12 / performance_period) if performance_period > 0 else 0
        
        # Risk-adjusted ROI
        risk_factor = self._calculate_risk_factor(project)
        risk_adjusted_roi = roi_percentage * (1 - risk_factor)
        
        # Cash flow metrics
        cash_flow = self.db.query(CashFlowProjection).filter(
            CashFlowProjection.project_id == project_id
        ).first()
        
        npv, irr = None, None
        if cash_flow:
            npv, irr = self._calculate_npv_irr(cash_flow)
        
        # Opportunity cost analysis
        opportunity_cost = await self._calculate_opportunity_cost(project, budget)
        
        return {
            'gross_profit': gross_profit,
            'roi_percentage': roi_percentage,
            'annualized_roi': annualized_roi,
            'risk_adjusted_roi': risk_adjusted_roi,
            'npv': npv,
            'irr': irr,
            'payback_period': cash_flow.payback_period if cash_flow else None,
            'opportunity_cost': opportunity_cost,
            'risk_factor': risk_factor,
            'performance_period_months': performance_period,
            'margin_percentage': (gross_profit / revenue * 100) if revenue > 0 else 0
        }
    
    async def generate_financial_dashboard(self, user_id: int) -> Dict[str, Any]:
        """Generate comprehensive financial dashboard"""
        
        # Get all active projects
        projects = self.db.query(FinancialProject).filter(
            FinancialProject.created_by == user_id,
            FinancialProject.status.in_([ProjectStatus.ACTIVE, ProjectStatus.BIDDING, ProjectStatus.AWARDED])
        ).all()
        
        # Portfolio metrics
        total_pipeline_value = sum(p.estimated_value or 0 for p in projects if p.status == ProjectStatus.BIDDING)
        active_contract_value = sum(p.contract_value or 0 for p in projects if p.status in [ProjectStatus.AWARDED, ProjectStatus.ACTIVE])
        
        # Cash flow analysis
        total_cash_flow = await self._calculate_portfolio_cash_flow(projects)
        
        # Alerts summary
        active_alerts = self.db.query(FinancialAlert).filter(
            FinancialAlert.status == 'active'
        ).count()
        
        # Performance metrics
        company_financials = await self._get_company_context(user_id)
        
        # AI financial insights
        ai_insights = await self._generate_ai_financial_insights(projects, company_financials)
        
        return {
            'portfolio_summary': {
                'total_pipeline_value': total_pipeline_value,
                'active_contract_value': active_contract_value,
                'project_count': len(projects),
                'active_projects': len([p for p in projects if p.status == ProjectStatus.ACTIVE])
            },
            'cash_flow_summary': total_cash_flow,
            'alerts': {
                'active_count': active_alerts,
                'critical_count': self.db.query(FinancialAlert).filter(
                    FinancialAlert.status == 'active',
                    FinancialAlert.severity == 'critical'
                ).count()
            },
            'performance_metrics': {
                'average_margin': company_financials.get('gross_margin_percentage', 0),
                'overhead_rate': company_financials.get('overhead_rate', 0),
                'revenue_ytd': company_financials.get('total_revenue', 0)
            },
            'ai_insights': ai_insights
        }
    
    def _distribute_costs_by_month(self, total_cost: float, performance_period: int) -> Dict[str, float]:
        """Distribute costs across project timeline"""
        
        if performance_period <= 0:
            return {"1": total_cost}
        
        # S-curve distribution (more costs in middle months)
        monthly_costs = {}
        
        for month in range(1, performance_period + 1):
            # S-curve factor (higher in middle months)
            progress = month / performance_period
            if progress <= 0.5:
                factor = 2 * progress * progress
            else:
                factor = 1 - 2 * (1 - progress) * (1 - progress)
            
            monthly_percentage = factor / performance_period
            monthly_costs[str(month)] = total_cost * monthly_percentage
        
        return monthly_costs
    
    def _calculate_risk_factor(self, project: FinancialProject) -> float:
        """Calculate project risk factor (0-1)"""
        
        base_risk = 0.1  # 10% base risk
        
        # Contract type risk
        if project.contract_type == 'FFP':
            base_risk += 0.05
        elif project.contract_type == 'T&M':
            base_risk -= 0.05
        
        # Performance period risk
        if project.performance_period and project.performance_period > 24:
            base_risk += 0.1  # Long projects are riskier
        
        # Project size risk
        if project.estimated_value and project.estimated_value > 5000000:
            base_risk += 0.05  # Large projects are riskier
        
        return min(base_risk, 0.5)  # Cap at 50%
    
    def _calculate_npv_irr(self, cash_flow: CashFlowProjection) -> Tuple[Optional[float], Optional[float]]:
        """Calculate Net Present Value and Internal Rate of Return"""
        
        try:
            # Get cash flow data
            monthly_flows = []
            
            # First 6 months from columns
            for month in range(1, 7):
                inflow = getattr(cash_flow, f'month_{month}_inflow', 0)
                outflow = getattr(cash_flow, f'month_{month}_outflow', 0)
                monthly_flows.append(inflow - outflow)
            
            # Extended months from JSON
            if cash_flow.extended_projections:
                for proj in cash_flow.extended_projections:
                    monthly_flows.append(proj.get('inflow', 0) - proj.get('outflow', 0))
            
            if not monthly_flows:
                return None, None
            
            # NPV calculation (10% annual discount rate)
            discount_rate = 0.10 / 12  # Monthly rate
            npv = sum(cf / (1 + discount_rate) ** month for month, cf in enumerate(monthly_flows))
            
            # IRR calculation (simplified)
            # This is a basic approximation - real IRR would need iterative solution
            total_inflow = sum(cf for cf in monthly_flows if cf > 0)
            total_outflow = abs(sum(cf for cf in monthly_flows if cf < 0))
            
            if total_outflow > 0:
                irr = ((total_inflow / total_outflow) ** (1 / len(monthly_flows)) - 1) * 12
            else:
                irr = None
            
            return npv, irr
            
        except Exception:
            return None, None
    
    async def _calculate_opportunity_cost(self, project: FinancialProject, budget: ProjectBudget) -> float:
        """Calculate opportunity cost of pursuing this project"""
        
        # Simplified opportunity cost based on average company margins
        company_avg_margin = 0.15  # 15% default
        
        # Resources tied up (primarily labor)
        resource_cost = budget.direct_labor_cost + budget.indirect_labor_cost
        
        # Time opportunity cost
        time_months = project.performance_period or 12
        
        # Calculate alternative return
        opportunity_cost = resource_cost * company_avg_margin * (time_months / 12)
        
        return opportunity_cost
    
    async def _get_company_context(self, user_id: int) -> Dict[str, Any]:
        """Get company financial context"""
        
        current_year = datetime.now().year
        company_financials = self.db.query(CompanyFinancials).filter(
            CompanyFinancials.user_id == user_id,
            CompanyFinancials.fiscal_year == current_year
        ).first()
        
        if company_financials:
            return {
                'overhead_rate': company_financials.overhead_rate,
                'ga_rate': company_financials.ga_rate,
                'fringe_rate': company_financials.fringe_rate,
                'gross_margin_percentage': company_financials.gross_margin_percentage,
                'total_revenue': company_financials.total_revenue,
                'average_billing_rate': company_financials.average_billing_rate
            }
        else:
            # Default values for new companies
            return {
                'overhead_rate': 100.0,
                'ga_rate': 15.0,
                'fringe_rate': 30.0,
                'gross_margin_percentage': 15.0,
                'total_revenue': 0,
                'average_billing_rate': 100.0
            }
    
    async def _get_industry_benchmarks(self, project: FinancialProject) -> Dict[str, Any]:
        """Get industry benchmarks for comparison"""
        
        # This would typically pull from external data sources
        # For now, using static benchmarks
        return {
            'average_overhead_rate': 120.0,
            'average_ga_rate': 18.0,
            'average_margin': 12.0,
            'typical_billing_rates': {
                'junior': 85,
                'mid': 125,
                'senior': 175,
                'principal': 225
            }
        }
    
    def _get_cfo_system_prompt(self) -> str:
        """System prompt for AI CFO analysis"""
        return """You are an expert CFO specializing in government contracting financials. 

Analyze budgets for:
1. Cost competitiveness 
2. Margin optimization
3. Risk mitigation
4. Cash flow implications
5. Compliance with government contracting standards

Provide actionable recommendations in JSON format:
{
    "optimizations": {
        "overhead_rate": 95.0,
        "ga_rate": 12.0,
        "fee_percentage": 8.5
    },
    "recommendations": [
        "Specific recommendation 1",
        "Specific recommendation 2"
    ],
    "risk_factors": [
        "Risk factor 1",
        "Risk factor 2"
    ],
    "confidence_score": 85
}"""
    
    def _create_budget_optimization_prompt(self, context: Dict) -> str:
        """Create prompt for budget optimization"""
        return f"""Analyze this government contract budget for optimization:

PROJECT: {json.dumps(context['project_details'], indent=2)}

PROPOSED BUDGET: {json.dumps(context['proposed_budget'], indent=2)}

COMPANY CONTEXT: {json.dumps(context['company_context'], indent=2)}

BENCHMARKS: {json.dumps(context['industry_benchmarks'], indent=2)}

Focus on cost competitiveness, margin optimization, and risk mitigation while ensuring compliance with government contracting standards."""
    
    def _parse_ai_budget_response(self, response: str) -> Dict[str, Any]:
        """Parse AI budget optimization response"""
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
                'recommendations': ['Manual budget review recommended'],
                'risk_factors': [],
                'confidence_score': 30
            }