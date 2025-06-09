from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel

from database.connection import get_db
from models.financial import (
    FinancialProject, ProjectBudget, CashFlowProjection, 
    ProjectExpense, FinancialAlert, CompanyFinancials, ProjectStatus
)
from services.financial_analysis import FinancialAnalysisService
from routers.users import get_current_user
from models.user import User

router = APIRouter()

# Add copyright notice at top of router
"""
© 2025 Aliff Capital, Quartermasters FZC, and SkillvenzA. All rights reserved.

Syntraq AI - Financial API Router (FVMS Module)
A Joint Innovation by Aliff Capital, Quartermasters FZC, and SkillvenzA
"""

class ProjectCreateRequest(BaseModel):
    project_name: str
    opportunity_id: Optional[int] = None
    client_agency: str
    contract_type: str
    estimated_value: float
    performance_period: int
    contract_number: Optional[str] = None

class BudgetCreateRequest(BaseModel):
    direct_labor_hours: float
    direct_labor_rate: float
    indirect_labor_cost: Optional[float] = 0
    fringe_benefits_rate: float = 30.0
    materials_cost: float = 0
    equipment_cost: float = 0
    travel_cost: float = 0
    subcontractor_cost: float = 0
    other_direct_costs: float = 0
    overhead_rate: float = 100.0
    ga_rate: float = 15.0
    fee_percentage: float = 10.0
    performance_period: Optional[int] = 12

class ExpenseCreateRequest(BaseModel):
    description: str
    category: str
    amount: float
    expense_date: datetime
    billable: bool = True
    employee_name: Optional[str] = None
    task_code: Optional[str] = None

class ProjectResponse(BaseModel):
    id: int
    project_name: str
    project_code: str
    status: str
    client_agency: str
    estimated_value: float
    contract_value: Optional[float]
    gross_margin_percentage: Optional[float]
    created_at: datetime
    
    class Config:
        from_attributes = True

class BudgetResponse(BaseModel):
    id: int
    total_cost: float
    total_price: float
    gross_margin: float
    margin_percentage: float
    overhead_rate: float
    ga_rate: float
    is_approved: bool
    
    class Config:
        from_attributes = True

@router.post("/projects", response_model=Dict[str, Any])
async def create_project(
    request: ProjectCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new financial project"""
    
    # Generate project code
    project_count = db.query(FinancialProject).filter(
        FinancialProject.created_by == current_user.id
    ).count()
    project_code = f"PROJ-{datetime.now().year}-{project_count + 1:04d}"
    
    project = FinancialProject(
        project_name=request.project_name,
        project_code=project_code,
        opportunity_id=request.opportunity_id,
        client_agency=request.client_agency,
        contract_type=request.contract_type,
        estimated_value=request.estimated_value,
        performance_period=request.performance_period,
        contract_number=request.contract_number,
        created_by=current_user.id
    )
    
    db.add(project)
    db.commit()
    db.refresh(project)
    
    return {
        "project_id": project.id,
        "project_code": project.project_code,
        "status": "success",
        "message": "Project created successfully"
    }

@router.get("/projects", response_model=List[ProjectResponse])
async def get_projects(
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's financial projects"""
    
    query = db.query(FinancialProject).filter(
        FinancialProject.created_by == current_user.id
    )
    
    if status:
        query = query.filter(FinancialProject.status == status)
    
    projects = query.order_by(FinancialProject.created_at.desc()).offset(skip).limit(limit).all()
    
    return [
        ProjectResponse(
            id=project.id,
            project_name=project.project_name,
            project_code=project.project_code,
            status=project.status.value,
            client_agency=project.client_agency,
            estimated_value=project.estimated_value,
            contract_value=project.contract_value,
            gross_margin_percentage=project.gross_margin_percentage,
            created_at=project.created_at
        )
        for project in projects
    ]

@router.get("/projects/{project_id}")
async def get_project_detail(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed project information"""
    
    project = db.query(FinancialProject).filter(
        FinancialProject.id == project_id,
        FinancialProject.created_by == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get latest budget
    latest_budget = db.query(ProjectBudget).filter(
        ProjectBudget.project_id == project_id
    ).order_by(ProjectBudget.created_at.desc()).first()
    
    # Get cash flow projection
    cash_flow = db.query(CashFlowProjection).filter(
        CashFlowProjection.project_id == project_id
    ).order_by(CashFlowProjection.created_at.desc()).first()
    
    # Get active alerts
    alerts = db.query(FinancialAlert).filter(
        FinancialAlert.project_id == project_id,
        FinancialAlert.status == 'active'
    ).all()
    
    return {
        "project": {
            "id": project.id,
            "project_name": project.project_name,
            "project_code": project.project_code,
            "status": project.status.value,
            "client_agency": project.client_agency,
            "contract_type": project.contract_type,
            "estimated_value": project.estimated_value,
            "contract_value": project.contract_value,
            "performance_period": project.performance_period,
            "gross_margin_percentage": project.gross_margin_percentage,
            "created_at": project.created_at.isoformat()
        },
        "budget": {
            "total_cost": latest_budget.total_cost if latest_budget else 0,
            "total_price": latest_budget.total_price if latest_budget else 0,
            "margin_percentage": ((latest_budget.total_price - latest_budget.total_cost) / latest_budget.total_price * 100) if latest_budget and latest_budget.total_price > 0 else 0,
            "overhead_rate": latest_budget.overhead_rate if latest_budget else 0,
            "ga_rate": latest_budget.ga_rate if latest_budget else 0,
            "is_approved": latest_budget.is_approved if latest_budget else False
        } if latest_budget else None,
        "cash_flow": {
            "peak_cash_requirement": cash_flow.peak_cash_requirement if cash_flow else 0,
            "payback_period": cash_flow.payback_period if cash_flow else None,
            "payment_terms": cash_flow.payment_terms if cash_flow else 30
        } if cash_flow else None,
        "alerts": [
            {
                "id": alert.id,
                "type": alert.alert_type,
                "severity": alert.severity,
                "title": alert.title,
                "message": alert.message,
                "created_at": alert.created_at.isoformat()
            }
            for alert in alerts
        ]
    }

@router.post("/projects/{project_id}/budget")
async def create_project_budget(
    project_id: int,
    request: BudgetCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create project budget with AI optimization"""
    
    # Verify project ownership
    project = db.query(FinancialProject).filter(
        FinancialProject.id == project_id,
        FinancialProject.created_by == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    service = FinancialAnalysisService(db)
    
    try:
        budget_data = request.dict()
        result = await service.create_project_budget(project_id, budget_data, current_user.id)
        
        return {
            "status": "success",
            "budget_id": result['budget_id'],
            "budget_summary": {
                "total_cost": result['total_cost'],
                "total_price": result['total_price'],
                "gross_margin": result['gross_margin'],
                "margin_percentage": result['margin_percentage']
            },
            "ai_recommendations": result['ai_recommendations']
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Budget creation failed: {str(e)}")

@router.get("/projects/{project_id}/roi-analysis")
async def get_project_roi_analysis(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive ROI analysis for project"""
    
    # Verify project ownership
    project = db.query(FinancialProject).filter(
        FinancialProject.id == project_id,
        FinancialProject.created_by == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    service = FinancialAnalysisService(db)
    
    try:
        roi_analysis = await service.calculate_project_roi(project_id)
        return roi_analysis
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ROI analysis failed: {str(e)}")

@router.get("/projects/{project_id}/cash-flow")
async def get_cash_flow_projection(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed cash flow projections"""
    
    # Verify project ownership
    project = db.query(FinancialProject).filter(
        FinancialProject.id == project_id,
        FinancialProject.created_by == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    cash_flow = db.query(CashFlowProjection).filter(
        CashFlowProjection.project_id == project_id
    ).order_by(CashFlowProjection.created_at.desc()).first()
    
    if not cash_flow:
        raise HTTPException(status_code=404, detail="No cash flow projection found")
    
    # Compile monthly data
    monthly_data = []
    
    # First 6 months from columns
    for month in range(1, 7):
        inflow = getattr(cash_flow, f'month_{month}_inflow', 0)
        outflow = getattr(cash_flow, f'month_{month}_outflow', 0)
        monthly_data.append({
            'month': month,
            'inflow': inflow,
            'outflow': outflow,
            'net_flow': inflow - outflow
        })
    
    # Extended months from JSON
    if cash_flow.extended_projections:
        monthly_data.extend(cash_flow.extended_projections)
    
    return {
        "project_id": project_id,
        "monthly_projections": monthly_data,
        "cumulative_cash_flow": cash_flow.cumulative_cash_flow,
        "peak_cash_requirement": cash_flow.peak_cash_requirement,
        "payback_period": cash_flow.payback_period,
        "payment_terms": cash_flow.payment_terms,
        "collection_period": cash_flow.collection_period,
        "projection_date": cash_flow.created_at.isoformat()
    }

@router.post("/projects/{project_id}/expenses")
async def add_project_expense(
    project_id: int,
    request: ExpenseCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add project expense"""
    
    # Verify project ownership
    project = db.query(FinancialProject).filter(
        FinancialProject.id == project_id,
        FinancialProject.created_by == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    expense = ProjectExpense(
        project_id=project_id,
        description=request.description,
        category=request.category,
        amount=request.amount,
        expense_date=request.expense_date,
        billable=request.billable,
        employee_name=request.employee_name,
        task_code=request.task_code,
        submitted_by=current_user.id
    )
    
    db.add(expense)
    db.commit()
    db.refresh(expense)
    
    return {
        "status": "success",
        "expense_id": expense.id,
        "message": "Expense added successfully"
    }

@router.get("/dashboard")
async def get_financial_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive financial dashboard"""
    
    service = FinancialAnalysisService(db)
    
    try:
        dashboard = await service.generate_financial_dashboard(current_user.id)
        return dashboard
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dashboard generation failed: {str(e)}")

@router.get("/treasury/dashboard")
async def get_treasury_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get treasury management dashboard with cash flow forecasting"""
    
    service = FinancialAnalysisService(db)
    
    try:
        treasury_dashboard = await service.generate_treasury_dashboard(current_user.id)
        return treasury_dashboard
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Treasury dashboard generation failed: {str(e)}")

@router.get("/alerts")
async def get_financial_alerts(
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None, description="active, acknowledged, resolved"),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get financial alerts for user's projects"""
    
    # Get user's projects
    user_projects = db.query(FinancialProject).filter(
        FinancialProject.created_by == current_user.id
    ).all()
    
    project_ids = [p.id for p in user_projects]
    
    # Query alerts
    query = db.query(FinancialAlert).filter(
        FinancialAlert.project_id.in_(project_ids)
    )
    
    if severity:
        query = query.filter(FinancialAlert.severity == severity)
    
    if status:
        query = query.filter(FinancialAlert.status == status)
    
    alerts = query.order_by(FinancialAlert.created_at.desc()).limit(limit).all()
    
    return [
        {
            "id": alert.id,
            "project_id": alert.project_id,
            "alert_type": alert.alert_type,
            "severity": alert.severity,
            "title": alert.title,
            "message": alert.message,
            "threshold_value": alert.threshold_value,
            "current_value": alert.current_value,
            "variance_percentage": alert.variance_percentage,
            "status": alert.status,
            "recommended_actions": alert.recommended_actions,
            "created_at": alert.created_at.isoformat(),
            "acknowledged_at": alert.acknowledged_at.isoformat() if alert.acknowledged_at else None
        }
        for alert in alerts
    ]

@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: int,
    action_taken: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Acknowledge financial alert"""
    
    alert = db.query(FinancialAlert).filter(FinancialAlert.id == alert_id).first()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    # Verify user owns the project
    project = db.query(FinancialProject).filter(
        FinancialProject.id == alert.project_id,
        FinancialProject.created_by == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Update alert
    alert.status = "acknowledged"
    alert.acknowledged_by = current_user.id
    alert.acknowledged_at = datetime.utcnow()
    if action_taken:
        alert.action_taken = action_taken
    
    db.commit()
    
    return {
        "status": "success",
        "message": "Alert acknowledged successfully"
    }

@router.get("/company/profile")
async def get_company_financials(
    fiscal_year: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get company financial profile"""
    
    year = fiscal_year or datetime.now().year
    
    company_financials = db.query(CompanyFinancials).filter(
        CompanyFinancials.user_id == current_user.id,
        CompanyFinancials.fiscal_year == year
    ).first()
    
    if not company_financials:
        # Return default structure
        return {
            "fiscal_year": year,
            "has_data": False,
            "message": "No financial data available for this year"
        }
    
    return {
        "fiscal_year": company_financials.fiscal_year,
        "has_data": True,
        "revenue": {
            "total_revenue": company_financials.total_revenue,
            "government_revenue": company_financials.government_revenue,
            "commercial_revenue": company_financials.commercial_revenue,
            "recurring_revenue": company_financials.recurring_revenue
        },
        "costs": {
            "total_costs": company_financials.total_costs,
            "direct_costs": company_financials.direct_costs,
            "indirect_costs": company_financials.indirect_costs,
            "overhead_costs": company_financials.overhead_costs,
            "ga_costs": company_financials.ga_costs
        },
        "profitability": {
            "gross_profit": company_financials.gross_profit,
            "net_profit": company_financials.net_profit,
            "ebitda": company_financials.ebitda,
            "gross_margin_percentage": company_financials.gross_margin_percentage,
            "net_margin_percentage": company_financials.net_margin_percentage
        },
        "cash_flow": {
            "operating_cash_flow": company_financials.operating_cash_flow,
            "free_cash_flow": company_financials.free_cash_flow,
            "cash_balance": company_financials.cash_balance,
            "accounts_receivable": company_financials.accounts_receivable
        },
        "rates": {
            "overhead_rate": company_financials.overhead_rate,
            "ga_rate": company_financials.ga_rate,
            "fringe_rate": company_financials.fringe_rate,
            "average_billing_rate": company_financials.average_billing_rate
        },
        "audit_info": {
            "is_audited": company_financials.is_audited,
            "audit_firm": company_financials.audit_firm,
            "data_source": company_financials.data_source
        },
        "last_updated": company_financials.updated_at.isoformat()
    }

class CompanyFinancialsUpdateRequest(BaseModel):
    fiscal_year: int
    total_revenue: float
    government_revenue: float
    commercial_revenue: Optional[float] = 0
    total_costs: float
    direct_costs: float
    indirect_costs: float
    overhead_rate: float
    ga_rate: float
    fringe_rate: float
    cash_balance: Optional[float] = None
    is_audited: bool = False
    audit_firm: Optional[str] = None

@router.post("/company/profile")
async def update_company_financials(
    request: CompanyFinancialsUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update company financial profile"""
    
    # Check if record exists
    existing = db.query(CompanyFinancials).filter(
        CompanyFinancials.user_id == current_user.id,
        CompanyFinancials.fiscal_year == request.fiscal_year
    ).first()
    
    if existing:
        # Update existing record
        for field, value in request.dict().items():
            setattr(existing, field, value)
        
        # Calculate derived fields
        existing.commercial_revenue = existing.total_revenue - existing.government_revenue
        existing.overhead_costs = existing.direct_costs * (existing.overhead_rate / 100)
        existing.ga_costs = (existing.direct_costs + existing.overhead_costs) * (existing.ga_rate / 100)
        existing.gross_profit = existing.total_revenue - existing.total_costs
        existing.net_profit = existing.gross_profit  # Simplified
        existing.gross_margin_percentage = (existing.gross_profit / existing.total_revenue * 100) if existing.total_revenue > 0 else 0
        existing.net_margin_percentage = (existing.net_profit / existing.total_revenue * 100) if existing.total_revenue > 0 else 0
        existing.updated_at = datetime.utcnow()
        
        company_financials = existing
    else:
        # Create new record
        data = request.dict()
        
        # Calculate derived fields
        commercial_revenue = data['total_revenue'] - data['government_revenue']
        overhead_costs = data['direct_costs'] * (data['overhead_rate'] / 100)
        ga_costs = (data['direct_costs'] + overhead_costs) * (data['ga_rate'] / 100)
        gross_profit = data['total_revenue'] - data['total_costs']
        net_profit = gross_profit  # Simplified
        gross_margin_percentage = (gross_profit / data['total_revenue'] * 100) if data['total_revenue'] > 0 else 0
        net_margin_percentage = (net_profit / data['total_revenue'] * 100) if data['total_revenue'] > 0 else 0
        
        company_financials = CompanyFinancials(
            user_id=current_user.id,
            commercial_revenue=commercial_revenue,
            overhead_costs=overhead_costs,
            ga_costs=ga_costs,
            gross_profit=gross_profit,
            net_profit=net_profit,
            gross_margin_percentage=gross_margin_percentage,
            net_margin_percentage=net_margin_percentage,
            **data
        )
        
        db.add(company_financials)
    
    db.commit()
    db.refresh(company_financials)
    
    return {
        "status": "success",
        "message": "Company financials updated successfully",
        "fiscal_year": company_financials.fiscal_year
    }
    
    return {
        "expense_id": expense.id,
        "status": "success",
        "message": "Expense added successfully"
    }

@router.get("/projects/{project_id}/expenses")
async def get_project_expenses(
    project_id: int,
    category: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get project expenses with filtering"""
    
    # Verify project ownership
    project = db.query(FinancialProject).filter(
        FinancialProject.id == project_id,
        FinancialProject.created_by == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    query = db.query(ProjectExpense).filter(ProjectExpense.project_id == project_id)
    
    if category:
        query = query.filter(ProjectExpense.category == category)
    
    if start_date:
        query = query.filter(ProjectExpense.expense_date >= start_date)
    
    if end_date:
        query = query.filter(ProjectExpense.expense_date <= end_date)
    
    expenses = query.order_by(ProjectExpense.expense_date.desc()).offset(skip).limit(limit).all()
    
    return [
        {
            "id": expense.id,
            "description": expense.description,
            "category": expense.category,
            "amount": expense.amount,
            "expense_date": expense.expense_date.isoformat(),
            "billable": expense.billable,
            "employee_name": expense.employee_name,
            "status": expense.status,
            "created_at": expense.created_at.isoformat()
        }
        for expense in expenses
    ]

@router.get("/dashboard")
async def get_financial_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive financial dashboard"""
    
    service = FinancialAnalysisService(db)
    
    try:
        dashboard = await service.generate_financial_dashboard(current_user.id)
        return dashboard
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dashboard generation failed: {str(e)}")

@router.get("/alerts")
async def get_financial_alerts(
    severity: Optional[str] = Query(None),
    project_id: Optional[int] = Query(None),
    status: str = Query("active"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get financial alerts"""
    
    # Get user's project IDs for filtering
    user_project_ids = [p.id for p in db.query(FinancialProject).filter(
        FinancialProject.created_by == current_user.id
    ).all()]
    
    query = db.query(FinancialAlert).filter(
        FinancialAlert.project_id.in_(user_project_ids),
        FinancialAlert.status == status
    )
    
    if severity:
        query = query.filter(FinancialAlert.severity == severity)
    
    if project_id:
        query = query.filter(FinancialAlert.project_id == project_id)
    
    alerts = query.order_by(FinancialAlert.created_at.desc()).offset(skip).limit(limit).all()
    
    return [
        {
            "id": alert.id,
            "project_id": alert.project_id,
            "alert_type": alert.alert_type,
            "severity": alert.severity,
            "title": alert.title,
            "message": alert.message,
            "threshold_value": alert.threshold_value,
            "current_value": alert.current_value,
            "recommended_actions": alert.recommended_actions,
            "created_at": alert.created_at.isoformat()
        }
        for alert in alerts
    ]

@router.put("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Acknowledge a financial alert"""
    
    alert = db.query(FinancialAlert).filter(FinancialAlert.id == alert_id).first()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    # Verify user owns the project
    project = db.query(FinancialProject).filter(
        FinancialProject.id == alert.project_id,
        FinancialProject.created_by == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=403, detail="Access denied")
    
    alert.status = "acknowledged"
    alert.acknowledged_by = current_user.id
    alert.acknowledged_at = datetime.utcnow()
    
    db.commit()
    
    return {"status": "success", "message": "Alert acknowledged"}

@router.post("/company-financials")
async def update_company_financials(
    fiscal_year: int,
    total_revenue: float,
    overhead_rate: float,
    ga_rate: float,
    fringe_rate: float,
    gross_margin_percentage: float,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update company financial information"""
    
    # Check if record exists
    existing = db.query(CompanyFinancials).filter(
        CompanyFinancials.user_id == current_user.id,
        CompanyFinancials.fiscal_year == fiscal_year
    ).first()
    
    if existing:
        # Update existing record
        existing.total_revenue = total_revenue
        existing.overhead_rate = overhead_rate
        existing.ga_rate = ga_rate
        existing.fringe_rate = fringe_rate
        existing.gross_margin_percentage = gross_margin_percentage
        existing.updated_at = datetime.utcnow()
    else:
        # Create new record
        financials = CompanyFinancials(
            user_id=current_user.id,
            fiscal_year=fiscal_year,
            total_revenue=total_revenue,
            overhead_rate=overhead_rate,
            ga_rate=ga_rate,
            fringe_rate=fringe_rate,
            gross_margin_percentage=gross_margin_percentage
        )
        db.add(financials)
    
    db.commit()
    
    return {"status": "success", "message": "Company financials updated"}

@router.get("/reporting/portfolio-analysis")
async def get_portfolio_analysis(
    months_back: int = Query(12, ge=1, le=36),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get portfolio analysis and trends"""
    
    start_date = datetime.now() - timedelta(days=30 * months_back)
    
    projects = db.query(FinancialProject).filter(
        FinancialProject.created_by == current_user.id,
        FinancialProject.created_at >= start_date
    ).all()
    
    # Calculate metrics
    total_value = sum(p.contract_value or p.estimated_value or 0 for p in projects)
    active_projects = [p for p in projects if p.status == ProjectStatus.ACTIVE]
    completed_projects = [p for p in projects if p.status == ProjectStatus.COMPLETED]
    
    # Win rate calculation
    total_bids = len([p for p in projects if p.status in [ProjectStatus.AWARDED, ProjectStatus.COMPLETED, ProjectStatus.CANCELLED]])
    wins = len([p for p in projects if p.status in [ProjectStatus.AWARDED, ProjectStatus.COMPLETED]])
    win_rate = (wins / total_bids * 100) if total_bids > 0 else 0
    
    # Average margins
    projects_with_budgets = []
    for project in projects:
        budget = db.query(ProjectBudget).filter(ProjectBudget.project_id == project.id).first()
        if budget:
            margin = ((budget.total_price - budget.total_cost) / budget.total_price * 100) if budget.total_price > 0 else 0
            projects_with_budgets.append({
                'project_name': project.project_name,
                'margin': margin,
                'total_value': budget.total_price
            })
    
    avg_margin = sum(p['margin'] for p in projects_with_budgets) / len(projects_with_budgets) if projects_with_budgets else 0
    
    return {
        "period_months": months_back,
        "portfolio_summary": {
            "total_projects": len(projects),
            "total_value": total_value,
            "active_projects": len(active_projects),
            "completed_projects": len(completed_projects),
            "win_rate": win_rate,
            "average_margin": avg_margin
        },
        "project_breakdown": [
            {
                "project_name": project.project_name,
                "status": project.status.value,
                "value": project.contract_value or project.estimated_value,
                "margin": next((p['margin'] for p in projects_with_budgets if p['project_name'] == project.project_name), None),
                "created_date": project.created_at.isoformat()
            }
            for project in projects
        ],
        "margin_analysis": projects_with_budgets
    }