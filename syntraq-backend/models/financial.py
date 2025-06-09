"""
© 2025 Aliff Capital, Quartermasters FZC, and SkillvenzA. All rights reserved.

Syntraq AI - FVMS (Financial Viability & Management System) Models
A Joint Innovation by Aliff Capital, Quartermasters FZC, and SkillvenzA
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, JSON, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()

class ProjectStatus(enum.Enum):
    PROSPECT = "prospect"
    BIDDING = "bidding"
    AWARDED = "awarded"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class FinancialProject(Base):
    __tablename__ = "financial_projects"
    
    id = Column(Integer, primary_key=True, index=True)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"), nullable=True)
    project_name = Column(String, index=True)
    project_code = Column(String, unique=True, index=True)
    
    # Project details
    status = Column(Enum(ProjectStatus), default=ProjectStatus.PROSPECT)
    client_agency = Column(String)
    contract_type = Column(String)  # FFP, T&M, CPFF, etc.
    contract_number = Column(String, nullable=True)
    
    # Financial overview
    estimated_value = Column(Float)  # Initial estimate
    contract_value = Column(Float, nullable=True)  # Actual awarded value
    base_period_value = Column(Float)
    option_periods_value = Column(Float, nullable=True)
    
    # Timeline
    bid_submission_date = Column(DateTime, nullable=True)
    project_start_date = Column(DateTime, nullable=True)
    project_end_date = Column(DateTime, nullable=True)
    performance_period = Column(Integer)  # months
    
    # Financial metrics
    gross_margin_percentage = Column(Float)
    net_margin_percentage = Column(Float)
    roi_percentage = Column(Float, nullable=True)
    break_even_point = Column(Integer, nullable=True)  # months
    
    # Risk assessment
    risk_level = Column(String, default="medium")  # low, medium, high
    risk_factors = Column(JSON)  # List of identified risks
    contingency_percentage = Column(Float, default=10.0)
    
    # Team and resources
    project_manager = Column(String, nullable=True)
    team_size = Column(Integer, nullable=True)
    key_personnel = Column(JSON)  # List of key team members
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    budgets = relationship("ProjectBudget", back_populates="project", cascade="all, delete-orphan")
    cash_flows = relationship("CashFlowProjection", back_populates="project", cascade="all, delete-orphan")
    expenses = relationship("ProjectExpense", back_populates="project", cascade="all, delete-orphan")
    invoices = relationship("ProjectInvoice", back_populates="project", cascade="all, delete-orphan")

class ProjectBudget(Base):
    __tablename__ = "project_budgets"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("financial_projects.id"))
    budget_version = Column(String, default="1.0")
    
    # Labor costs
    direct_labor_hours = Column(Float)
    direct_labor_rate = Column(Float)
    direct_labor_cost = Column(Float)
    
    indirect_labor_cost = Column(Float, nullable=True)
    fringe_benefits_rate = Column(Float, default=30.0)  # percentage
    fringe_benefits_cost = Column(Float)
    
    # Other direct costs
    materials_cost = Column(Float, default=0.0)
    equipment_cost = Column(Float, default=0.0)
    travel_cost = Column(Float, default=0.0)
    subcontractor_cost = Column(Float, default=0.0)
    other_direct_costs = Column(Float, default=0.0)
    
    # Indirect costs
    overhead_rate = Column(Float)  # percentage
    overhead_cost = Column(Float)
    ga_rate = Column(Float)  # General & Administrative percentage
    ga_cost = Column(Float)
    
    # Total calculations
    total_direct_cost = Column(Float)
    total_indirect_cost = Column(Float)
    total_cost = Column(Float)
    fee_percentage = Column(Float, nullable=True)
    fee_amount = Column(Float, nullable=True)
    total_price = Column(Float)
    
    # Cost breakdown by period
    cost_by_month = Column(JSON)  # Monthly cost distribution
    cost_by_task = Column(JSON)  # Cost by work breakdown structure
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    is_approved = Column(Boolean, default=False)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    
    # Relationships
    project = relationship("FinancialProject", back_populates="budgets")

class CashFlowProjection(Base):
    __tablename__ = "cash_flow_projections"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("financial_projects.id"))
    projection_date = Column(DateTime, default=datetime.utcnow)
    
    # Monthly projections (24 months)
    month_1_inflow = Column(Float, default=0.0)
    month_1_outflow = Column(Float, default=0.0)
    month_2_inflow = Column(Float, default=0.0)
    month_2_outflow = Column(Float, default=0.0)
    month_3_inflow = Column(Float, default=0.0)
    month_3_outflow = Column(Float, default=0.0)
    month_4_inflow = Column(Float, default=0.0)
    month_4_outflow = Column(Float, default=0.0)
    month_5_inflow = Column(Float, default=0.0)
    month_5_outflow = Column(Float, default=0.0)
    month_6_inflow = Column(Float, default=0.0)
    month_6_outflow = Column(Float, default=0.0)
    
    # Extended projections stored as JSON for flexibility
    extended_projections = Column(JSON)  # Months 7-24
    
    # Cash flow metrics
    cumulative_cash_flow = Column(JSON)  # Monthly cumulative
    peak_cash_requirement = Column(Float)  # Maximum negative cash flow
    payback_period = Column(Integer, nullable=True)  # months
    
    # Assumptions
    payment_terms = Column(Integer, default=30)  # days
    invoice_frequency = Column(String, default="monthly")  # monthly, milestone, etc.
    collection_period = Column(Integer, default=45)  # average days to collect
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    scenario = Column(String, default="base")  # base, optimistic, pessimistic
    
    # Relationships
    project = relationship("FinancialProject", back_populates="cash_flows")

class ProjectExpense(Base):
    __tablename__ = "project_expenses"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("financial_projects.id"))
    
    # Expense details
    expense_date = Column(DateTime)
    description = Column(String)
    category = Column(String)  # labor, materials, travel, etc.
    subcategory = Column(String, nullable=True)
    
    # Financial
    amount = Column(Float)
    billable = Column(Boolean, default=True)
    reimbursable = Column(Boolean, default=False)
    
    # Assignment
    employee_name = Column(String, nullable=True)
    task_code = Column(String, nullable=True)
    billing_rate = Column(Float, nullable=True)
    
    # Approval workflow
    status = Column(String, default="pending")  # pending, approved, rejected
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    
    # Documentation
    receipt_url = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    submitted_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    project = relationship("FinancialProject", back_populates="expenses")

class ProjectInvoice(Base):
    __tablename__ = "project_invoices"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("financial_projects.id"))
    
    # Invoice details
    invoice_number = Column(String, unique=True, index=True)
    invoice_date = Column(DateTime)
    period_start = Column(DateTime)
    period_end = Column(DateTime)
    
    # Financial
    labor_amount = Column(Float, default=0.0)
    materials_amount = Column(Float, default=0.0)
    travel_amount = Column(Float, default=0.0)
    other_costs = Column(Float, default=0.0)
    subtotal = Column(Float)
    tax_amount = Column(Float, default=0.0)
    total_amount = Column(Float)
    
    # Payment tracking
    status = Column(String, default="draft")  # draft, sent, paid, overdue
    sent_date = Column(DateTime, nullable=True)
    due_date = Column(DateTime, nullable=True)
    paid_date = Column(DateTime, nullable=True)
    paid_amount = Column(Float, nullable=True)
    
    # Details
    line_items = Column(JSON)  # Detailed breakdown
    payment_terms = Column(String, default="Net 30")
    notes = Column(Text, nullable=True)
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    project = relationship("FinancialProject", back_populates="invoices")

class FinancialAlert(Base):
    __tablename__ = "financial_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("financial_projects.id"), nullable=True)
    
    # Alert details
    alert_type = Column(String)  # budget_overrun, cash_flow_negative, invoice_overdue, etc.
    severity = Column(String)  # low, medium, high, critical
    title = Column(String)
    message = Column(Text)
    
    # Threshold values
    threshold_value = Column(Float, nullable=True)
    current_value = Column(Float, nullable=True)
    variance_percentage = Column(Float, nullable=True)
    
    # Status
    status = Column(String, default="active")  # active, acknowledged, resolved
    acknowledged_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    
    # Actions
    recommended_actions = Column(JSON)  # List of suggested actions
    action_taken = Column(Text, nullable=True)
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CompanyFinancials(Base):
    __tablename__ = "company_financials"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    fiscal_year = Column(Integer)
    
    # Revenue
    total_revenue = Column(Float)
    government_revenue = Column(Float)
    commercial_revenue = Column(Float)
    recurring_revenue = Column(Float, nullable=True)
    
    # Costs
    total_costs = Column(Float)
    direct_costs = Column(Float)
    indirect_costs = Column(Float)
    overhead_costs = Column(Float)
    ga_costs = Column(Float)
    
    # Profitability
    gross_profit = Column(Float)
    net_profit = Column(Float)
    ebitda = Column(Float, nullable=True)
    gross_margin_percentage = Column(Float)
    net_margin_percentage = Column(Float)
    
    # Cash flow
    operating_cash_flow = Column(Float, nullable=True)
    free_cash_flow = Column(Float, nullable=True)
    cash_balance = Column(Float, nullable=True)
    accounts_receivable = Column(Float, nullable=True)
    
    # Rates and factors
    overhead_rate = Column(Float)
    ga_rate = Column(Float)
    fringe_rate = Column(Float)
    average_billing_rate = Column(Float, nullable=True)
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Data validation
    is_audited = Column(Boolean, default=False)
    audit_firm = Column(String, nullable=True)
    data_source = Column(String, default="manual")  # manual, quickbooks, etc.