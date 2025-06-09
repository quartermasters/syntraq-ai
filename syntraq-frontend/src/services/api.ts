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