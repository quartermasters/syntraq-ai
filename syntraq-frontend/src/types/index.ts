/**
 * © 2025 Aliff Capital, Quartermasters FZC, and SkillvenzA. All rights reserved.
 * 
 * Syntraq AI - Frontend Type Definitions
 * A Joint Innovation by Aliff Capital, Quartermasters FZC, and SkillvenzA
 */

// Base types
export interface BaseEntity {
  id: number
  created_at: string
  updated_at: string
}

// User and Auth types
export interface User extends BaseEntity {
  email: string
  username: string
  full_name: string
  company_name: string
  is_active: boolean
  profile_complete: boolean
}

export interface UserProfile {
  naics_codes: string[]
  certifications: string[]
  capabilities: string[]
  contract_size_preference: string
}

// Opportunity types
export interface Opportunity extends BaseEntity {
  notice_id: string
  title: string
  description: string
  agency: string
  naics_code: string
  set_aside_type?: string
  place_of_performance?: string
  response_deadline?: string
  estimated_value?: number
  ai_summary?: string
  relevance_score?: number
  decision?: string
  decision_reason?: string
  status: string
}

// ARTS (AI Team Simulation) types
export interface AIAgent extends BaseEntity {
  agent_name: string
  agent_type: string
  specialization: string
  expertise_level: string
  performance_score: number
  current_workload: number
  availability_status: string
  personality_traits: string[]
  communication_style: string
}

export interface AgentTask extends BaseEntity {
  agent_id: number
  task_description: string
  task_type: string
  priority: string
  status: string
  assigned_date: string
  due_date?: string
  completion_date?: string
  estimated_hours: number
  actual_hours?: number
  complexity_score: number
  ai_analysis: any
}

export interface TeamCollaboration extends BaseEntity {
  project_id: number
  collaboration_type: string
  participants: number[]
  objective: string
  status: string
  conversation_log: any[]
  decisions_made: any[]
  deliverables: any[]
  performance_metrics: any
}

// FVMS (Financial Management) types
export interface FinancialProject extends BaseEntity {
  project_name: string
  project_code: string
  opportunity_id?: number
  status: string
  client_agency: string
  contract_type: string
  estimated_value: number
  contract_value?: number
  performance_period: number
  gross_margin_percentage?: number
  roi_percentage?: number
}

export interface ProjectBudget extends BaseEntity {
  project_id: number
  direct_labor_hours: number
  direct_labor_rate: number
  direct_labor_cost: number
  total_cost: number
  total_price: number
  overhead_rate: number
  ga_rate: number
  fee_percentage?: number
  is_approved: boolean
}

export interface CashFlowProjection extends BaseEntity {
  project_id: number
  monthly_projections: Array<{
    month: number
    inflow: number
    outflow: number
    net_flow: number
    cumulative: number
  }>
  peak_cash_requirement: number
  payback_period?: number
  payment_terms: number
}

export interface FinancialAlert extends BaseEntity {
  project_id?: number
  alert_type: string
  severity: string
  title: string
  message: string
  threshold_value?: number
  current_value?: number
  status: string
  recommended_actions: string[]
}

// PME (Proposal Management) types
export interface Proposal extends BaseEntity {
  opportunity_id: number
  project_id?: number
  proposal_number: string
  proposal_title: string
  status: string
  submission_deadline?: string
  overall_progress_percentage: number
  proposal_manager: number
  compliance_score?: number
  readiness_gates_status: any
  ai_recommendations: string[]
}

export interface ProposalSection extends BaseEntity {
  proposal_id: number
  section_number: string
  section_title: string
  section_type: string
  content?: string
  completion_percentage: number
  compliance_status: string
  word_count: number
  ai_generated_content: boolean
  ai_suggestions: string[]
}

export interface ProposalReview extends BaseEntity {
  proposal_id: number
  review_type: string
  review_name: string
  review_date: string
  reviewer_id: number
  overall_score?: number
  strengths: string[]
  weaknesses: string[]
  recommendations: string[]
  critical_issues: string[]
  action_items: string[]
}

// CAH (Communication Hub) types
export interface Contact extends BaseEntity {
  first_name: string
  last_name: string
  full_name: string
  email: string
  phone?: string
  title?: string
  organization: string
  contact_type: string
  relationship_level: string
  last_contact_date?: string
  last_interaction_date?: string
  engagement_score: number
  response_rate?: number
  nda_signed: boolean
  status: string
  department?: string
  address?: string
}

export interface Communication extends BaseEntity {
  contact_id: number
  communication_type: string
  subject: string
  content: string
  direction: string
  status: string
  priority: string
  sent_date?: string
  communication_date: string
  ai_generated: boolean
  ai_confidence_score?: number
  sentiment_score?: number
  key_topics: string[]
  action_items: string[]
  requires_response: boolean
}

export interface Meeting extends BaseEntity {
  title: string
  scheduled_date: string
  duration_minutes: number
  meeting_type: string
  status: string
  agenda?: string
  location?: string
  participants?: number[]
  meeting_notes?: string
  action_items?: string[]
  recording_url?: string
}

export interface CommunicationTemplate extends BaseEntity {
  template_name: string
  template_type: string
  subject?: string
  content: string
  description?: string
  usage_count?: number
  variables: string[]
  category: string
}

export interface CommunicationDocument extends BaseEntity {
  contact_id?: number
  document_name: string
  document_type: string
  status: string
  requires_signature: boolean
  signed_date?: string
  signed_by?: string
  expiry_date?: string
  confidentiality_level: string
}

export interface MeetingSchedule extends BaseEntity {
  title: string
  description?: string
  scheduled_date: string
  duration_minutes: number
  meeting_type: string
  location?: string
  meeting_url?: string
  participants: Array<{
    contact_id: number
    name: string
    email: string
    role: string
  }>
  agenda_items: string[]
  status: string
}

// Dashboard and Analytics types
export interface DashboardStats {
  total_opportunities: number
  active_projects: number
  pending_decisions: number
  ai_processed_today: number
  response_rate: number
  pipeline_value: number
}

export interface EngagementMetrics {
  engagement_metrics: {
    total_communications: number
    outbound_communications: number
    inbound_communications: number
    response_rate: number
    avg_response_time_hours: number
    avg_sentiment_score: number
  }
}

export interface FinancialMetrics {
  portfolio_summary: {
    total_pipeline_value: number
    active_contract_value: number
    project_count: number
    active_projects: number
  }
  performance_metrics: {
    average_margin: number
    cash_flow_30_days: number
    working_capital: number
  }
  ai_insights?: Array<{
    title: string
    recommendation: string
    priority: string
  }>
}

// API Response types
export interface ApiResponse<T = any> {
  status: string
  message?: string
  data?: T
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  limit: number
  has_next: boolean
}

// Form types
export interface CreateContactForm {
  first_name: string
  last_name: string
  email: string
  organization: string
  contact_type: string
  title?: string
  phone?: string
}

export interface CreateProjectForm {
  project_name: string
  opportunity_id?: number
  client_agency: string
  contract_type: string
  estimated_value: number
  performance_period: number
  contract_number?: string
}

export interface CreateBudgetForm {
  direct_labor_hours: number
  direct_labor_rate: number
  indirect_labor_cost?: number
  fringe_benefits_rate?: number
  materials_cost?: number
  equipment_cost?: number
  travel_cost?: number
  subcontractor_cost?: number
  other_direct_costs?: number
  overhead_rate?: number
  ga_rate?: number
  fee_percentage?: number
  performance_period?: number
}

export interface GenerateCommunicationForm {
  contact_id: number
  communication_type: string
  context: any
  template_id?: number
}

export interface ScheduleMeetingForm {
  contact_ids: number[]
  title: string
  scheduled_date: string
  duration_minutes?: number
  meeting_type?: string
  description?: string
  agenda_items?: string[]
}

// Enums
export enum ProjectStatus {
  PROSPECT = 'prospect',
  BIDDING = 'bidding',
  AWARDED = 'awarded',
  ACTIVE = 'active',
  COMPLETED = 'completed',
  CANCELLED = 'cancelled'
}

export enum ProposalStatus {
  DRAFT = 'draft',
  IN_PROGRESS = 'in_progress',
  REVIEW = 'review',
  READY = 'ready',
  SUBMITTED = 'submitted',
  AWARDED = 'awarded',
  NOT_AWARDED = 'not_awarded',
  CANCELLED = 'cancelled'
}

export enum CommunicationType {
  EMAIL = 'email',
  PHONE_CALL = 'phone_call',
  MEETING = 'meeting',
  DOCUMENT = 'document',
  QUOTE_REQUEST = 'quote_request',
  NDA_REQUEST = 'nda_request',
  TEAM_CONFIRMATION = 'team_confirmation'
}

export enum ContactType {
  CLIENT = 'client',
  PARTNER = 'partner',
  SUBCONTRACTOR = 'subcontractor',
  VENDOR = 'vendor',
  TEAM_MEMBER = 'team_member',
  GOVERNMENT_OFFICIAL = 'government_official'
}

export enum AlertSeverity {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical'
}