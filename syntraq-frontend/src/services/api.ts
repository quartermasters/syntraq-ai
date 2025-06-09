import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      console.error('401 Unauthorized error:', error)
      // Temporarily disable auto-redirect for debugging
      // localStorage.removeItem('auth_token')
      // window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Auth API
export const authAPI = {
  login: async (email: string, password: string) => {
    const response = await api.post('/api/users/login', { email, password })
    return response.data
  },
  
  register: async (userData: {
    email: string
    username: string
    password: string
    full_name: string
    company_name: string
  }) => {
    const response = await api.post('/api/users/register', userData)
    return response.data
  },
  
  getCurrentUser: async () => {
    const response = await api.get('/api/users/me')
    return response.data
  },
  
  updateProfile: async (profileData: any) => {
    const response = await api.put('/api/users/profile', profileData)
    return response.data
  },
  
  setupCompany: async (companyData: {
    naics_codes: string[]
    certifications: string[]
    capabilities: string[]
    contract_size_preference: string
  }) => {
    const response = await api.post('/api/users/setup-company', companyData)
    return response.data
  }
}

// Opportunities API
export const opportunitiesAPI = {
  getOpportunities: async (params?: {
    skip?: number
    limit?: number
    status?: string
    min_relevance?: number
  }) => {
    const response = await api.get('/api/opportunities/', { params })
    return response.data
  },
  
  getOpportunity: async (id: number) => {
    const response = await api.get(`/api/opportunities/${id}`)
    return response.data
  },
  
  syncSamGov: async (daysBack: number = 7) => {
    const response = await api.post(`/api/opportunities/sync-sam-gov?days_back=${daysBack}`)
    return response.data
  },
  
  processWithAI: async (opportunityId: number) => {
    const response = await api.post(`/api/opportunities/${opportunityId}/process-ai`)
    return response.data
  },
  
  getDashboardStats: async () => {
    const response = await api.get('/api/opportunities/dashboard/stats')
    return response.data
  }
}

// AI Summarizer API
export const aiAPI = {
  generateSummary: async (opportunityId: number, userProfile?: any) => {
    const response = await api.post('/api/ai/summarize', {
      opportunity_id: opportunityId,
      user_profile: userProfile
    })
    return response.data
  },
  
  batchSummarize: async (opportunityIds: number[], userProfile?: any) => {
    const response = await api.post('/api/ai/batch-summarize', {
      opportunity_ids: opportunityIds,
      user_profile: userProfile
    })
    return response.data
  },
  
  getRelevanceTrends: async (days: number = 30) => {
    const response = await api.get(`/api/ai/relevance-trends?days=${days}`)
    return response.data
  },
  
  submitFeedback: async (opportunityId: number, accuracyScore: number, notes?: string) => {
    const response = await api.post('/api/ai/feedback', {
      opportunity_id: opportunityId,
      accuracy_score: accuracyScore,
      feedback_notes: notes
    })
    return response.data
  }
}

// Decisions API
export const decisionsAPI = {
  makeDecision: async (decisionData: {
    opportunity_id: number
    decision: string
    reason?: string
    priority?: string
    assigned_to?: string
    tags?: string[]
    notes?: string
  }) => {
    const response = await api.post('/api/decisions/make-decision', decisionData)
    return response.data
  },
  
  bulkDecision: async (opportunityIds: number[], decision: string, reason?: string) => {
    const response = await api.get('/api/decisions/bulk-decision', {
      params: {
        opportunity_ids: opportunityIds,
        decision,
        reason
      }
    })
    return response.data
  },
  
  getDecisionStats: async (days?: number) => {
    const response = await api.get('/api/decisions/stats', {
      params: days ? { days } : {}
    })
    return response.data
  },
  
  getRecentDecisions: async (limit: number = 20) => {
    const response = await api.get(`/api/decisions/recent?limit=${limit}`)
    return response.data
  },
  
  updateDecision: async (opportunityId: number, decisionData: any) => {
    const response = await api.put(`/api/decisions/${opportunityId}/update-decision`, decisionData)
    return response.data
  }
}

// ARTS (AI Role-Based Team Simulation) API
export const artsAPI = {
  initializeTeam: async (data: {
    project_id: number
    team_requirements: any
    opportunity_context?: any
  }) => {
    const response = await api.post('/api/arts/ai-team/initialize', data)
    return response.data
  },
  
  assignTask: async (data: {
    agent_id: number
    task_description: string
    priority?: string
    context?: any
  }) => {
    const response = await api.post('/api/arts/tasks/assign', data)
    return response.data
  },
  
  initiateCollaboration: async (data: {
    project_id: number
    collaboration_type: string
    participants: number[]
    context?: any
  }) => {
    const response = await api.post('/api/arts/collaboration/initiate', data)
    return response.data
  },
  
  getTeamPerformance: async (teamId: number) => {
    const response = await api.get(`/api/arts/team/${teamId}/performance`)
    return response.data
  },
  
  getAgents: async (teamId?: number) => {
    const params = teamId ? { team_id: teamId } : {}
    const response = await api.get('/api/arts/agents', { params })
    return response.data
  },
  
  getTasks: async (params?: { agent_id?: number; status?: string; limit?: number }) => {
    const response = await api.get('/api/arts/tasks', { params })
    return response.data
  },
  
  getCollaborations: async (projectId?: number) => {
    const params = projectId ? { project_id: projectId } : {}
    const response = await api.get('/api/arts/collaborations', { params })
    return response.data
  }
}

// FVMS (Financial Viability & Management System) API
export const fvmsAPI = {
  createProject: async (data: {
    project_name: string
    opportunity_id?: number
    client_agency: string
    contract_type: string
    estimated_value: number
    performance_period: number
    contract_number?: string
  }) => {
    const response = await api.post('/api/financial/projects', data)
    return response.data
  },
  
  getProjects: async (params?: { status?: string; skip?: number; limit?: number }) => {
    const response = await api.get('/api/financial/projects', { params })
    return response.data
  },
  
  getProject: async (projectId: number) => {
    const response = await api.get(`/api/financial/projects/${projectId}`)
    return response.data
  },
  
  createBudget: async (projectId: number, data: {
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
  }) => {
    const response = await api.post(`/api/financial/projects/${projectId}/budget`, data)
    return response.data
  },
  
  getROIAnalysis: async (projectId: number) => {
    const response = await api.get(`/api/financial/projects/${projectId}/roi-analysis`)
    return response.data
  },
  
  getCashFlow: async (projectId: number) => {
    const response = await api.get(`/api/financial/projects/${projectId}/cash-flow`)
    return response.data
  },
  
  getTreasuryDashboard: async () => {
    const response = await api.get('/api/financial/treasury/dashboard')
    return response.data
  },
  
  getFinancialDashboard: async () => {
    const response = await api.get('/api/financial/dashboard')
    return response.data
  },
  
  getAlerts: async (params?: { severity?: string; status?: string; limit?: number }) => {
    const response = await api.get('/api/financial/alerts', { params })
    return response.data
  },
  
  acknowledgeAlert: async (alertId: number, actionTaken?: string) => {
    const response = await api.post(`/api/financial/alerts/${alertId}/acknowledge`, {
      action_taken: actionTaken
    })
    return response.data
  },
  
  getCompanyFinancials: async (fiscalYear?: number) => {
    const params = fiscalYear ? { fiscal_year: fiscalYear } : {}
    const response = await api.get('/api/financial/company/profile', { params })
    return response.data
  },
  
  updateCompanyFinancials: async (data: {
    fiscal_year: number
    total_revenue: number
    government_revenue: number
    commercial_revenue?: number
    total_costs: number
    direct_costs: number
    indirect_costs: number
    overhead_rate: number
    ga_rate: number
    fringe_rate: number
    cash_balance?: number
    is_audited?: boolean
    audit_firm?: string
  }) => {
    const response = await api.post('/api/financial/company/profile', data)
    return response.data
  }
}

// PME (Proposal Management Engine) API
export const pmeAPI = {
  createFromOpportunity: async (data: {
    user_id: number
    opportunity_id: number
    project_id?: number
    delivery_plan_id?: number
  }) => {
    const response = await api.post('/api/proposals/create-from-opportunity', data)
    return response.data
  },
  
  getProposals: async (params?: { status?: string; skip?: number; limit?: number }) => {
    const response = await api.get('/api/proposals', { params })
    return response.data
  },
  
  getProposal: async (proposalId: number) => {
    const response = await api.get(`/api/proposals/${proposalId}`)
    return response.data
  },
  
  generateSectionContent: async (sectionId: number, context?: any) => {
    const response = await api.post(`/api/proposals/sections/${sectionId}/generate-content`, {
      context: context || {}
    })
    return response.data
  },
  
  checkCompliance: async (proposalId: number) => {
    const response = await api.post(`/api/proposals/${proposalId}/check-compliance`)
    return response.data
  },
  
  assessReadinessGates: async (proposalId: number) => {
    const response = await api.get(`/api/proposals/${proposalId}/readiness-gates`)
    return response.data
  },
  
  conductReview: async (proposalId: number, data: {
    review_type: string
    sections_to_review?: number[]
  }) => {
    const response = await api.post(`/api/proposals/${proposalId}/reviews`, data)
    return response.data
  },
  
  getReviews: async (proposalId: number) => {
    const response = await api.get(`/api/proposals/${proposalId}/reviews`)
    return response.data
  },
  
  updateProposal: async (proposalId: number, data: any) => {
    const response = await api.put(`/api/proposals/${proposalId}`, data)
    return response.data
  }
}

// CAH (Communication & Arrangement Hub) API
export const cahAPI = {
  // Contacts
  createContact: async (data: {
    first_name: string
    last_name: string
    email: string
    organization: string
    contact_type: string
    title?: string
    phone?: string
  }) => {
    const response = await api.post('/api/communications/contacts', data)
    return response.data
  },
  
  getContacts: async (params?: {
    contact_type?: string
    organization?: string
    skip?: number
    limit?: number
  }) => {
    const response = await api.get('/api/communications/contacts', { params })
    return response.data
  },
  
  // Communications
  generateAICommunication: async (data: {
    contact_id: number
    communication_type: string
    context: any
    template_id?: number
  }) => {
    const response = await api.post('/api/communications/ai-generate', data)
    return response.data
  },
  
  getCommunications: async (params?: {
    contact_id?: number
    communication_type?: string
    status?: string
    start_date?: string
    end_date?: string
    skip?: number
    limit?: number
  }) => {
    const response = await api.get('/api/communications', { params })
    return response.data
  },
  
  getCommunication: async (commId: number) => {
    const response = await api.get(`/api/communications/${commId}`)
    return response.data
  },
  
  sendCommunication: async (commId: number) => {
    const response = await api.put(`/api/communications/${commId}/send`)
    return response.data
  },
  
  analyzeCommunication: async (commId: number) => {
    const response = await api.post(`/api/communications/${commId}/analyze`)
    return response.data
  },
  
  // Documents
  generateNDA: async (contactId: number, context: any) => {
    const response = await api.post('/api/communications/documents/nda', { contact_id: contactId, context })
    return response.data
  },
  
  getDocuments: async (params?: {
    contact_id?: number
    document_type?: string
    status?: string
    skip?: number
    limit?: number
  }) => {
    const response = await api.get('/api/communications/documents', { params })
    return response.data
  },
  
  markDocumentSigned: async (docId: number, signedBy: string) => {
    const response = await api.put(`/api/communications/documents/${docId}/sign`, { signed_by: signedBy })
    return response.data
  },
  
  // Teaming
  requestTeamingConfirmation: async (data: {
    partner_contact_id: number
    opportunity_id: number
    teaming_details: any
  }) => {
    const response = await api.post('/api/communications/teaming/request-confirmation', data)
    return response.data
  },
  
  // Quotes
  requestQuote: async (data: {
    vendor_contact_id: number
    quote_requirements: any
  }) => {
    const response = await api.post('/api/communications/quotes/request', data)
    return response.data
  },
  
  // Meetings
  scheduleMeeting: async (data: {
    contact_ids: number[]
    title: string
    scheduled_date: string
    duration_minutes?: number
    meeting_type?: string
    description?: string
    agenda_items?: string[]
  }) => {
    const response = await api.post('/api/communications/meetings/schedule', data)
    return response.data
  },
  
  getMeetings: async (params?: { upcoming_only?: boolean; skip?: number; limit?: number }) => {
    const response = await api.get('/api/communications/meetings', { params })
    return response.data
  },
  
  // Follow-up
  generateFollowUpSequence: async (data: {
    contact_id: number
    opportunity_id?: number
    sequence_type?: string
  }) => {
    const response = await api.post('/api/communications/follow-up/generate', data)
    return response.data
  },
  
  // Analytics
  getCommunicationStats: async (daysBack: number = 30) => {
    const response = await api.get(`/api/communications/dashboard/communication-stats?days_back=${daysBack}`)
    return response.data
  },
  
  getEngagementAnalytics: async (params?: { contact_id?: number; days_back?: number }) => {
    const response = await api.get('/api/communications/analytics/engagement', { params })
    return response.data
  },
  
  // Templates
  getTemplates: async (params?: { template_type?: string; category?: string }) => {
    const response = await api.get('/api/communications/templates', { params })
    return response.data
  },
  
  createTemplate: async (data: {
    template_name: string
    template_type: string
    category: string
    subject_template: string
    content_template: string
    use_case?: string
    target_audience?: string
    tone?: string
    variables?: string[]
  }) => {
    const response = await api.post('/api/communications/templates', data)
    return response.data
  }
}