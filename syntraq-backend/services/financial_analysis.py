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
    
    async def _calculate_portfolio_cash_flow(self, projects: List[FinancialProject]) -> Dict[str, Any]:
        """Calculate comprehensive portfolio cash flow analysis"""
        
        total_cash_flow_30 = 0
        total_cash_flow_90 = 0
        peak_cash_requirement = 0
        monthly_projections = {}
        
        for project in projects:
            cash_flow = self.db.query(CashFlowProjection).filter(
                CashFlowProjection.project_id == project.id
            ).first()
            
            if cash_flow:
                # 30-day projection
                total_cash_flow_30 += (cash_flow.month_1_inflow - cash_flow.month_1_outflow)
                
                # 90-day projection (first 3 months)
                total_cash_flow_90 += ((cash_flow.month_1_inflow - cash_flow.month_1_outflow) +
                                      (cash_flow.month_2_inflow - cash_flow.month_2_outflow) +
                                      (cash_flow.month_3_inflow - cash_flow.month_3_outflow))
                
                # Peak requirement
                if cash_flow.peak_cash_requirement < peak_cash_requirement:
                    peak_cash_requirement = cash_flow.peak_cash_requirement
                
                # Aggregate monthly projections for next 12 months
                for month in range(1, 13):
                    if month not in monthly_projections:
                        monthly_projections[month] = {'inflow': 0, 'outflow': 0}
                    
                    if month <= 6:
                        inflow = getattr(cash_flow, f'month_{month}_inflow', 0)
                        outflow = getattr(cash_flow, f'month_{month}_outflow', 0)
                    else:
                        # Get from extended projections
                        extended = cash_flow.extended_projections or []
                        if month - 7 < len(extended):
                            projection = extended[month - 7]
                            inflow = projection.get('inflow', 0)
                            outflow = projection.get('outflow', 0)
                        else:
                            inflow = outflow = 0
                    
                    monthly_projections[month]['inflow'] += inflow
                    monthly_projections[month]['outflow'] += outflow
        
        return {
            'next_30_days': total_cash_flow_30,
            'next_90_days': total_cash_flow_90,
            'peak_requirement': peak_cash_requirement,
            'monthly_projections': monthly_projections,
            'cash_flow_positive_months': len([m for m in monthly_projections.values() if m['inflow'] > m['outflow']]),
            'working_capital_needed': abs(peak_cash_requirement) if peak_cash_requirement < 0 else 0
        }
    
    async def _generate_ai_financial_insights(self, projects: List[FinancialProject], company_financials: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate AI-powered financial insights and recommendations"""
        
        # Prepare data for AI analysis
        portfolio_data = {
            'total_projects': len(projects),
            'total_pipeline': sum(p.estimated_value or 0 for p in projects if p.status == ProjectStatus.BIDDING),
            'active_contracts': sum(p.contract_value or 0 for p in projects if p.status in [ProjectStatus.AWARDED, ProjectStatus.ACTIVE]),
            'company_metrics': company_financials
        }
        
        prompt = f"""As a CFO advisor, analyze this government contracting company's financial position:
        
        PORTFOLIO: {json.dumps(portfolio_data, indent=2)}
        
        Provide 3-5 actionable insights covering:
        1. Cash flow optimization
        2. Profitability improvement
        3. Risk mitigation
        4. Growth opportunities
        5. Operational efficiency
        
        Format as JSON array of insights with title, category, priority, and recommendation."""
        
        try:
            response = await self.ai_service.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert CFO providing financial insights for government contractors."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            insights_text = response.choices[0].message.content
            
            # Parse AI response
            if "```json" in insights_text:
                json_start = insights_text.find("```json") + 7
                json_end = insights_text.find("```", json_start)
                json_str = insights_text[json_start:json_end].strip()
                return json.loads(json_str)
            else:
                return json.loads(insights_text)
        
        except Exception as e:
            # Fallback insights
            return [
                {
                    "title": "Regular Financial Review Recommended",
                    "category": "financial_health",
                    "priority": "medium",
                    "recommendation": "Schedule monthly financial reviews to track project profitability and cash flow"
                },
                {
                    "title": "Cash Flow Monitoring",
                    "category": "cash_management",
                    "priority": "high",
                    "recommendation": "Monitor cash flow closely and establish line of credit for working capital"
                },
                {
                    "title": "Margin Analysis",
                    "category": "profitability",
                    "priority": "medium",
                    "recommendation": "Review pricing strategies to ensure competitive but profitable margins"
                }
            ]
    
    async def generate_treasury_dashboard(self, user_id: int) -> Dict[str, Any]:
        """Generate treasury management dashboard with cash flow forecasting"""
        
        # Get all financial projects
        projects = self.db.query(FinancialProject).filter(
            FinancialProject.created_by == user_id
        ).all()
        
        # Calculate current cash position
        current_cash = await self._estimate_current_cash_position(user_id)
        
        # Cash flow forecasting for next 12 months
        cash_flow_forecast = await self._calculate_portfolio_cash_flow(projects)
        
        # Outstanding receivables
        outstanding_receivables = await self._calculate_outstanding_receivables(user_id)
        
        # Upcoming payables
        upcoming_payables = await self._calculate_upcoming_payables(user_id)
        
        # Working capital analysis
        working_capital = current_cash + outstanding_receivables - upcoming_payables
        
        # Cash burn rate
        burn_rate = await self._calculate_burn_rate(user_id)
        
        # Runway calculation
        runway_months = current_cash / burn_rate if burn_rate > 0 else float('inf')
        
        # Financial alerts
        cash_alerts = await self._generate_cash_flow_alerts(current_cash, cash_flow_forecast, burn_rate)
        
        return {
            'treasury_overview': {
                'current_cash_position': current_cash,
                'working_capital': working_capital,
                'burn_rate_monthly': burn_rate,
                'runway_months': min(runway_months, 999) if runway_months != float('inf') else None
            },
            'cash_flow_forecast': cash_flow_forecast,
            'receivables_payables': {
                'outstanding_receivables': outstanding_receivables,
                'upcoming_payables': upcoming_payables,
                'net_position': outstanding_receivables - upcoming_payables
            },
            'alerts': cash_alerts,
            'recommendations': await self._generate_treasury_recommendations(current_cash, cash_flow_forecast, burn_rate)
        }
    
    async def _estimate_current_cash_position(self, user_id: int) -> float:
        """Estimate current cash position from company financials"""
        
        company_financials = self.db.query(CompanyFinancials).filter(
            CompanyFinancials.user_id == user_id
        ).order_by(CompanyFinancials.fiscal_year.desc()).first()
        
        if company_financials and company_financials.cash_balance:
            return company_financials.cash_balance
        else:
            # Estimate based on recent revenue (30 days cash on hand)
            if company_financials and company_financials.total_revenue:
                return company_financials.total_revenue / 12  # 1 month of revenue
            return 50000  # Default assumption
    
    async def _calculate_outstanding_receivables(self, user_id: int) -> float:
        """Calculate outstanding receivables from unpaid invoices"""
        
        from models.financial import ProjectInvoice
        
        unpaid_invoices = self.db.query(ProjectInvoice).join(FinancialProject).filter(
            FinancialProject.created_by == user_id,
            ProjectInvoice.status.in_(['sent', 'overdue'])
        ).all()
        
        return sum(invoice.total_amount for invoice in unpaid_invoices)
    
    async def _calculate_upcoming_payables(self, user_id: int) -> float:
        """Calculate upcoming payables (next 90 days)"""
        
        # This would typically include:
        # - Payroll
        # - Subcontractor payments
        # - Operating expenses
        # - Loan payments
        
        # For now, estimate based on company size and burn rate
        company_financials = self.db.query(CompanyFinancials).filter(
            CompanyFinancials.user_id == user_id
        ).order_by(CompanyFinancials.fiscal_year.desc()).first()
        
        if company_financials:
            quarterly_costs = company_financials.total_costs / 4
            return quarterly_costs
        
        return 75000  # Default estimate
    
    async def _calculate_burn_rate(self, user_id: int) -> float:
        """Calculate monthly cash burn rate"""
        
        # Get expenses from last 3 months
        three_months_ago = datetime.now() - timedelta(days=90)
        
        recent_expenses = self.db.query(ProjectExpense).join(FinancialProject).filter(
            FinancialProject.created_by == user_id,
            ProjectExpense.expense_date >= three_months_ago,
            ProjectExpense.status == 'approved'
        ).all()
        
        total_expenses = sum(expense.amount for expense in recent_expenses)
        monthly_burn = total_expenses / 3 if total_expenses > 0 else 25000  # Default
        
        return monthly_burn
    
    async def _generate_cash_flow_alerts(self, current_cash: float, forecast: Dict[str, Any], burn_rate: float) -> List[Dict[str, Any]]:
        """Generate cash flow alerts and warnings"""
        
        alerts = []
        
        # Low cash warning
        if current_cash < burn_rate * 2:  # Less than 2 months runway
            alerts.append({
                'type': 'low_cash',
                'severity': 'critical',
                'title': 'Critical Cash Flow Warning',
                'message': f'Current cash (${current_cash:,.0f}) covers less than 2 months of expenses',
                'recommendation': 'Arrange immediate financing or accelerate collections'
            })
        elif current_cash < burn_rate * 6:  # Less than 6 months runway
            alerts.append({
                'type': 'cash_warning',
                'severity': 'medium',
                'title': 'Cash Flow Warning',
                'message': f'Current cash provides ${current_cash/burn_rate:.1f} months of runway',
                'recommendation': 'Plan for additional financing or cost reduction'
            })
        
        # Negative cash flow forecast
        if forecast.get('next_90_days', 0) < 0:
            alerts.append({
                'type': 'negative_forecast',
                'severity': 'high',
                'title': 'Negative Cash Flow Forecast',
                'message': f'Projected ${abs(forecast["next_90_days"]):,.0f} negative cash flow in next 90 days',
                'recommendation': 'Review payment terms and accelerate billing cycles'
            })
        
        # Working capital requirements
        working_capital_needed = forecast.get('working_capital_needed', 0)
        if working_capital_needed > current_cash:
            alerts.append({
                'type': 'working_capital',
                'severity': 'medium',
                'title': 'Working Capital Shortage',
                'message': f'Peak cash requirement (${working_capital_needed:,.0f}) exceeds current cash',
                'recommendation': 'Secure line of credit or adjust project timing'
            })
        
        return alerts
    
    async def _generate_treasury_recommendations(self, current_cash: float, forecast: Dict[str, Any], burn_rate: float) -> List[Dict[str, Any]]:
        """Generate AI-powered treasury management recommendations"""
        
        recommendations = []
        
        # Cash optimization
        if current_cash > burn_rate * 12:  # More than 12 months cash
            recommendations.append({
                'category': 'cash_optimization',
                'priority': 'low',
                'title': 'Consider Investment Options',
                'description': 'Excess cash could be invested in short-term instruments for better returns'
            })
        
        # Payment acceleration
        if forecast.get('next_30_days', 0) < 0:
            recommendations.append({
                'category': 'collections',
                'priority': 'high',
                'title': 'Accelerate Collections',
                'description': 'Implement faster invoicing and follow up on overdue accounts receivable'
            })
        
        # Cost management
        if burn_rate > current_cash / 6:
            recommendations.append({
                'category': 'cost_control',
                'priority': 'medium',
                'title': 'Review Operating Expenses',
                'description': 'Analyze and optimize operating expenses to improve cash runway'
            })
        
        # Financing recommendations
        working_capital_needed = forecast.get('working_capital_needed', 0)
        if working_capital_needed > 0:
            recommendations.append({
                'category': 'financing',
                'priority': 'medium',
                'title': 'Secure Line of Credit',
                'description': f'Establish ${working_capital_needed:,.0f} line of credit for working capital needs'
            })
        
        return recommendations