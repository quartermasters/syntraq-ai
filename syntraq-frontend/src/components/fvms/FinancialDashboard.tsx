/**
 * © 2025 Aliff Capital, Quartermasters FZC, and SkillvenzA. All rights reserved.
 * 
 * Syntraq AI - FVMS (Financial Viability & Management System) Dashboard
 * A Joint Innovation by Aliff Capital, Quartermasters FZC, and SkillvenzA
 */

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { fvmsAPI } from '../../services/api'
import { FinancialProject, FinancialAlert } from '../../types'
import { format } from 'date-fns'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'

const FinancialDashboard = () => {
  const [selectedTab, setSelectedTab] = useState<'overview' | 'projects' | 'treasury' | 'alerts'>('overview')
  const [showCreateProjectModal, setShowCreateProjectModal] = useState(false)
  const [selectedProject, setSelectedProject] = useState<FinancialProject | null>(null)
  const queryClient = useQueryClient()

  // Fetch data
  const { data: financialDashboard, isLoading: dashboardLoading } = useQuery(
    'financial-dashboard',
    fvmsAPI.getFinancialDashboard
  )

  const { data: treasuryDashboard } = useQuery(
    'treasury-dashboard',
    fvmsAPI.getTreasuryDashboard
  )

  const { data: projects, isLoading: projectsLoading } = useQuery<FinancialProject[]>(
    'financial-projects',
    () => fvmsAPI.getProjects({ limit: 50 })
  )

  const { data: alerts } = useQuery<FinancialAlert[]>(
    'financial-alerts',
    () => fvmsAPI.getAlerts({ status: 'active', limit: 20 })
  )

  // Mutations
  const createProjectMutation = useMutation(fvmsAPI.createProject, {
    onSuccess: () => {
      queryClient.invalidateQueries('financial-projects')
      setShowCreateProjectModal(false)
    }
  })

  const acknowledgeAlertMutation = useMutation(fvmsAPI.acknowledgeAlert, {
    onSuccess: () => {
      queryClient.invalidateQueries('financial-alerts')
    }
  })

  const handleCreateProject = (formData: any) => {
    createProjectMutation.mutate(formData)
  }

  const handleAcknowledgeAlert = (alertId: number) => {
    acknowledgeAlertMutation.mutate(alertId)
  }

  const getAlertSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'bg-red-100 text-red-800 border-red-200'
      case 'high': return 'bg-orange-100 text-orange-800 border-orange-200'
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200'
      case 'low': return 'bg-blue-100 text-blue-800 border-blue-200'
      default: return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  const getProjectStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800'
      case 'awarded': return 'bg-blue-100 text-blue-800'
      case 'bidding': return 'bg-yellow-100 text-yellow-800'
      case 'completed': return 'bg-gray-100 text-gray-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  // Chart colors
  const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6']

  if (dashboardLoading || projectsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">💰 Financial Management (FVMS)</h1>
          <p className="text-gray-600">AI-powered financial planning and treasury management</p>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={() => setShowCreateProjectModal(true)}
            className="btn-primary"
          >
            Create Project
          </button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="card p-6 bg-gradient-to-r from-blue-500 to-blue-600 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-blue-100">Pipeline Value</p>
              <p className="text-2xl font-bold">
                ${financialDashboard?.portfolio_summary?.total_pipeline_value?.toLocaleString() || '0'}
              </p>
              <p className="text-blue-100 text-sm">
                {financialDashboard?.portfolio_summary?.project_count || 0} projects
              </p>
            </div>
            <div className="text-3xl opacity-75">💰</div>
          </div>
        </div>

        <div className="card p-6 bg-gradient-to-r from-green-500 to-green-600 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-green-100">Active Contracts</p>
              <p className="text-2xl font-bold">
                ${financialDashboard?.portfolio_summary?.active_contract_value?.toLocaleString() || '0'}
              </p>
              <p className="text-green-100 text-sm">
                {financialDashboard?.portfolio_summary?.active_projects || 0} active
              </p>
            </div>
            <div className="text-3xl opacity-75">📊</div>
          </div>
        </div>

        <div className="card p-6 bg-gradient-to-r from-purple-500 to-purple-600 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-purple-100">Cash Position</p>
              <p className="text-2xl font-bold">
                ${treasuryDashboard?.treasury_overview?.current_cash_position?.toLocaleString() || '0'}
              </p>
              <p className="text-purple-100 text-sm">
                {treasuryDashboard?.treasury_overview?.runway_months || 0} months runway
              </p>
            </div>
            <div className="text-3xl opacity-75">💵</div>
          </div>
        </div>

        <div className="card p-6 bg-gradient-to-r from-orange-500 to-orange-600 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-orange-100">Avg Margin</p>
              <p className="text-2xl font-bold">
                {financialDashboard?.performance_metrics?.average_margin?.toFixed(1) || '0'}%
              </p>
              <p className="text-orange-100 text-sm">
                {alerts?.filter(a => a.severity === 'high' || a.severity === 'critical').length || 0} alerts
              </p>
            </div>
            <div className="text-3xl opacity-75">📈</div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setSelectedTab('overview')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              selectedTab === 'overview'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Overview
          </button>
          <button
            onClick={() => setSelectedTab('projects')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              selectedTab === 'projects'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Projects ({projects?.length || 0})
          </button>
          <button
            onClick={() => setSelectedTab('treasury')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              selectedTab === 'treasury'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Treasury
          </button>
          <button
            onClick={() => setSelectedTab('alerts')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              selectedTab === 'alerts'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Alerts ({alerts?.length || 0})
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      {selectedTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Cash Flow Chart */}
          <div className="card p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Cash Flow Forecast</h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={treasuryDashboard?.cash_flow_forecast?.monthly_projections ? 
                  Object.entries(treasuryDashboard.cash_flow_forecast.monthly_projections).map(([month, data]: any) => ({
                    month: `Month ${month}`,
                    inflow: data.inflow,
                    outflow: data.outflow,
                    net: data.inflow - data.outflow
                  })) : []}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis />
                  <Tooltip formatter={(value: any) => [`$${value.toLocaleString()}`, '']} />
                  <Line type="monotone" dataKey="inflow" stroke="#10B981" strokeWidth={2} name="Inflow" />
                  <Line type="monotone" dataKey="outflow" stroke="#EF4444" strokeWidth={2} name="Outflow" />
                  <Line type="monotone" dataKey="net" stroke="#3B82F6" strokeWidth={2} name="Net Flow" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Project Status Distribution */}
          <div className="card p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Projects by Status</h3>
            <div className="h-64">
              {projects && projects.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={projects.reduce((acc: any[], project) => {
                        const existing = acc.find(item => item.status === project.status)
                        if (existing) {
                          existing.count += 1
                          existing.value += project.estimated_value || 0
                        } else {
                          acc.push({
                            status: project.status,
                            count: 1,
                            value: project.estimated_value || 0
                          })
                        }
                        return acc
                      }, [])}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ status, count }) => `${status} (${count})`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {projects.reduce((acc: any[], project) => {
                        const existing = acc.find(item => item.status === project.status)
                        if (!existing) {
                          acc.push({ status: project.status })
                        }
                        return acc
                      }, []).map((_, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value: any) => [`$${value.toLocaleString()}`, 'Value']} />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <div className="flex items-center justify-center h-full text-gray-500">
                  No projects to display
                </div>
              )}
            </div>
          </div>

          {/* AI Insights */}
          <div className="card p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">🧠 AI Financial Insights</h3>
            <div className="space-y-3">
              {financialDashboard?.ai_insights?.map((insight: any, index: number) => (
                <div key={index} className="p-3 bg-blue-50 rounded-lg">
                  <p className="text-sm font-medium text-blue-900">{insight.title}</p>
                  <p className="text-xs text-blue-700">{insight.recommendation}</p>
                  <span className={`inline-flex px-2 py-1 text-xs rounded-full mt-2 ${
                    insight.priority === 'high' ? 'bg-red-100 text-red-800' :
                    insight.priority === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-green-100 text-green-800'
                  }`}>
                    {insight.priority} priority
                  </span>
                </div>
              )) || (
                <div className="text-center py-8 text-gray-500">
                  <div className="text-4xl mb-2">🤖</div>
                  <p>AI insights will appear here based on your financial data</p>
                </div>
              )}
            </div>
          </div>

          {/* Quick Stats */}
          <div className="card p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Stats</h3>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Total Projects</span>
                <span className="text-lg font-semibold">{projects?.length || 0}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Active Projects</span>
                <span className="text-lg font-semibold text-green-600">
                  {projects?.filter(p => p.status === 'active').length || 0}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Bidding</span>
                <span className="text-lg font-semibold text-yellow-600">
                  {projects?.filter(p => p.status === 'bidding').length || 0}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Completed</span>
                <span className="text-lg font-semibold text-gray-600">
                  {projects?.filter(p => p.status === 'completed').length || 0}
                </span>
              </div>
              <div className="pt-3 border-t border-gray-200">
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Win Rate</span>
                  <span className="text-lg font-semibold text-purple-600">
                    {projects && projects.length > 0 ? 
                      Math.round((projects.filter(p => p.status === 'awarded' || p.status === 'active' || p.status === 'completed').length / projects.length) * 100) : 0}%
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {selectedTab === 'projects' && (
        <div className="space-y-4">
          {projects?.map(project => (
            <div key={project.id} className="card p-6 hover:shadow-lg transition-shadow cursor-pointer"
                 onClick={() => setSelectedProject(project)}>
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    <h3 className="text-lg font-medium text-gray-900">{project.project_name}</h3>
                    <span className="text-sm font-medium text-gray-500">#{project.project_code}</span>
                    <span className={`inline-flex px-2 py-1 text-xs rounded-full ${getProjectStatusColor(project.status)}`}>
                      {project.status}
                    </span>
                  </div>
                  
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <span className="text-gray-600">Client:</span>
                      <span className="ml-1 font-medium">{project.client_agency}</span>
                    </div>
                    <div>
                      <span className="text-gray-600">Type:</span>
                      <span className="ml-1 font-medium">{project.contract_type}</span>
                    </div>
                    <div>
                      <span className="text-gray-600">Value:</span>
                      <span className="ml-1 font-medium">${project.estimated_value?.toLocaleString()}</span>
                    </div>
                    <div>
                      <span className="text-gray-600">Period:</span>
                      <span className="ml-1 font-medium">{project.performance_period} months</span>
                    </div>
                  </div>
                  
                  {project.gross_margin_percentage && (
                    <div className="mt-2 text-sm">
                      <span className="text-gray-600">Margin:</span>
                      <span className="ml-1 font-medium text-green-600">{project.gross_margin_percentage.toFixed(1)}%</span>
                    </div>
                  )}
                </div>
                
                <div className="ml-4 text-right">
                  <div className="text-gray-600 text-sm">Created</div>
                  <div className="font-medium">{format(new Date(project.created_at), 'MMM d, yyyy')}</div>
                </div>
              </div>
            </div>
          ))}
          
          {(!projects || projects.length === 0) && (
            <div className="text-center py-12">
              <div className="text-6xl mb-4">💼</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Projects Yet</h3>
              <p className="text-gray-600 mb-4">Create your first financial project to get started</p>
              <button
                onClick={() => setShowCreateProjectModal(true)}
                className="btn-primary"
              >
                Create Project
              </button>
            </div>
          )}
        </div>
      )}

      {selectedTab === 'treasury' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="card p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Treasury Overview</h3>
            <div className="space-y-4">
              <div className="flex justify-between items-center p-3 bg-blue-50 rounded-lg">
                <span className="text-blue-900 font-medium">Current Cash Position</span>
                <span className="text-xl font-bold text-blue-600">
                  ${treasuryDashboard?.treasury_overview?.current_cash_position?.toLocaleString() || '0'}
                </span>
              </div>
              
              <div className="flex justify-between items-center p-3 bg-green-50 rounded-lg">
                <span className="text-green-900 font-medium">Working Capital</span>
                <span className="text-xl font-bold text-green-600">
                  ${treasuryDashboard?.treasury_overview?.working_capital?.toLocaleString() || '0'}
                </span>
              </div>
              
              <div className="flex justify-between items-center p-3 bg-orange-50 rounded-lg">
                <span className="text-orange-900 font-medium">Monthly Burn Rate</span>
                <span className="text-xl font-bold text-orange-600">
                  ${treasuryDashboard?.treasury_overview?.burn_rate_monthly?.toLocaleString() || '0'}
                </span>
              </div>
              
              <div className="flex justify-between items-center p-3 bg-purple-50 rounded-lg">
                <span className="text-purple-900 font-medium">Runway</span>
                <span className="text-xl font-bold text-purple-600">
                  {treasuryDashboard?.treasury_overview?.runway_months || 0} months
                </span>
              </div>
            </div>
          </div>

          <div className="card p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Receivables & Payables</h3>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Outstanding Receivables</span>
                <span className="text-lg font-semibold text-green-600">
                  ${treasuryDashboard?.receivables_payables?.outstanding_receivables?.toLocaleString() || '0'}
                </span>
              </div>
              
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Upcoming Payables</span>
                <span className="text-lg font-semibold text-red-600">
                  ${treasuryDashboard?.receivables_payables?.upcoming_payables?.toLocaleString() || '0'}
                </span>
              </div>
              
              <div className="flex justify-between items-center pt-3 border-t border-gray-200">
                <span className="text-gray-900 font-medium">Net Position</span>
                <span className={`text-lg font-bold ${
                  (treasuryDashboard?.receivables_payables?.net_position || 0) >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  ${treasuryDashboard?.receivables_payables?.net_position?.toLocaleString() || '0'}
                </span>
              </div>
            </div>
          </div>

          <div className="lg:col-span-2">
            <div className="card p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Treasury Recommendations</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {treasuryDashboard?.recommendations?.map((rec: any, index: number) => (
                  <div key={index} className="p-4 border rounded-lg">
                    <div className="flex items-start space-x-3">
                      <span className={`inline-flex px-2 py-1 text-xs rounded-full ${
                        rec.priority === 'high' ? 'bg-red-100 text-red-800' :
                        rec.priority === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-green-100 text-green-800'
                      }`}>
                        {rec.priority}
                      </span>
                      <div className="flex-1">
                        <p className="font-medium text-gray-900">{rec.title}</p>
                        <p className="text-sm text-gray-600 mt-1">{rec.description}</p>
                      </div>
                    </div>
                  </div>
                )) || (
                  <div className="col-span-2 text-center py-8 text-gray-500">
                    <div className="text-4xl mb-2">💡</div>
                    <p>Treasury recommendations will appear here</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {selectedTab === 'alerts' && (
        <div className="space-y-4">
          {alerts?.map(alert => (
            <div key={alert.id} className={`card p-6 border-l-4 ${getAlertSeverityColor(alert.severity)}`}>
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    <h3 className="text-lg font-medium text-gray-900">{alert.title}</h3>
                    <span className={`inline-flex px-2 py-1 text-xs rounded-full ${getAlertSeverityColor(alert.severity)}`}>
                      {alert.severity}
                    </span>
                  </div>
                  
                  <p className="text-gray-700 mb-3">{alert.message}</p>
                  
                  {alert.threshold_value && alert.current_value && (
                    <div className="text-sm text-gray-600 mb-3">
                      <span>Threshold: {alert.threshold_value}</span>
                      <span className="mx-2">•</span>
                      <span>Current: {alert.current_value}</span>
                    </div>
                  )}
                  
                  {alert.recommended_actions && alert.recommended_actions.length > 0 && (
                    <div className="mt-3">
                      <p className="text-sm font-medium text-gray-900 mb-2">Recommended Actions:</p>
                      <ul className="text-sm text-gray-700 space-y-1">
                        {alert.recommended_actions.map((action, index) => (
                          <li key={index} className="flex items-start">
                            <span className="text-blue-600 mr-2">•</span>
                            {action}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
                
                <div className="ml-4 flex flex-col space-y-2">
                  <button
                    onClick={() => handleAcknowledgeAlert(alert.id)}
                    className="btn-outline text-sm"
                    disabled={acknowledgeAlertMutation.isLoading}
                  >
                    Acknowledge
                  </button>
                  <div className="text-xs text-gray-500 text-right">
                    {format(new Date(alert.created_at), 'MMM d, h:mm a')}
                  </div>
                </div>
              </div>
            </div>
          ))}
          
          {(!alerts || alerts.length === 0) && (
            <div className="text-center py-12">
              <div className="text-6xl mb-4">✅</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Active Alerts</h3>
              <p className="text-gray-600">Your financial health looks good!</p>
            </div>
          )}
        </div>
      )}

      {/* Create Project Modal */}
      {showCreateProjectModal && (
        <CreateProjectModal
          onClose={() => setShowCreateProjectModal(false)}
          onSubmit={handleCreateProject}
          isLoading={createProjectMutation.isLoading}
        />
      )}

      {/* Project Detail Modal */}
      {selectedProject && (
        <ProjectDetailModal
          project={selectedProject}
          onClose={() => setSelectedProject(null)}
        />
      )}
    </div>
  )
}

// Create Project Modal Component
const CreateProjectModal = ({ onClose, onSubmit, isLoading }: any) => {
  const [formData, setFormData] = useState({
    project_name: '',
    opportunity_id: '',
    client_agency: '',
    contract_type: '',
    estimated_value: '',
    performance_period: '12',
    contract_number: ''
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit({
      ...formData,
      estimated_value: Number(formData.estimated_value),
      performance_period: Number(formData.performance_period),
      opportunity_id: formData.opportunity_id ? Number(formData.opportunity_id) : undefined
    })
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Create Financial Project</h2>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Project Name *
            </label>
            <input
              type="text"
              value={formData.project_name}
              onChange={(e) => setFormData({ ...formData, project_name: e.target.value })}
              className="w-full border border-gray-300 rounded-md px-3 py-2"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Client Agency *
            </label>
            <input
              type="text"
              value={formData.client_agency}
              onChange={(e) => setFormData({ ...formData, client_agency: e.target.value })}
              className="w-full border border-gray-300 rounded-md px-3 py-2"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Contract Type *
            </label>
            <select
              value={formData.contract_type}
              onChange={(e) => setFormData({ ...formData, contract_type: e.target.value })}
              className="w-full border border-gray-300 rounded-md px-3 py-2"
              required
            >
              <option value="">Select type</option>
              <option value="FFP">Firm Fixed Price (FFP)</option>
              <option value="T&M">Time & Materials (T&M)</option>
              <option value="CPFF">Cost Plus Fixed Fee (CPFF)</option>
              <option value="CPIF">Cost Plus Incentive Fee (CPIF)</option>
              <option value="IDIQ">Indefinite Delivery/Indefinite Quantity (IDIQ)</option>
            </select>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Estimated Value *
              </label>
              <input
                type="number"
                value={formData.estimated_value}
                onChange={(e) => setFormData({ ...formData, estimated_value: e.target.value })}
                className="w-full border border-gray-300 rounded-md px-3 py-2"
                placeholder="0"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Performance Period (months) *
              </label>
              <input
                type="number"
                value={formData.performance_period}
                onChange={(e) => setFormData({ ...formData, performance_period: e.target.value })}
                className="w-full border border-gray-300 rounded-md px-3 py-2"
                required
              />
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Opportunity ID
            </label>
            <input
              type="number"
              value={formData.opportunity_id}
              onChange={(e) => setFormData({ ...formData, opportunity_id: e.target.value })}
              className="w-full border border-gray-300 rounded-md px-3 py-2"
              placeholder="Optional"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Contract Number
            </label>
            <input
              type="text"
              value={formData.contract_number}
              onChange={(e) => setFormData({ ...formData, contract_number: e.target.value })}
              className="w-full border border-gray-300 rounded-md px-3 py-2"
              placeholder="Optional"
            />
          </div>
          
          <div className="flex space-x-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 btn-outline"
              disabled={isLoading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex-1 btn-primary"
              disabled={isLoading}
            >
              {isLoading ? 'Creating...' : 'Create Project'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// Project Detail Modal Component
const ProjectDetailModal = ({ project, onClose }: any) => {
  const { data: projectDetail, isLoading } = useQuery(
    ['project-detail', project.id],
    () => fvmsAPI.getProject(project.id),
    { enabled: !!project.id }
  )

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-bold text-gray-900">{project.project_name}</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            ✕
          </button>
        </div>
        
        {isLoading ? (
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Project Info */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-gray-600">Project Code</label>
                <p className="text-lg font-semibold">{project.project_code}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-600">Status</label>
                <p className="text-lg font-semibold capitalize">{project.status}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-600">Client Agency</label>
                <p className="text-lg">{project.client_agency}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-600">Contract Type</label>
                <p className="text-lg">{project.contract_type}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-600">Estimated Value</label>
                <p className="text-lg font-semibold text-green-600">
                  ${project.estimated_value?.toLocaleString()}
                </p>
              </div>
              <div>
                <label className="text-sm font-medium text-gray-600">Performance Period</label>
                <p className="text-lg">{project.performance_period} months</p>
              </div>
            </div>
            
            {/* Budget Summary */}
            {projectDetail?.budget && (
              <div className="border-t pt-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Budget Summary</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium text-gray-600">Total Cost</label>
                    <p className="text-lg font-semibold">${projectDetail.budget.total_cost?.toLocaleString()}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-600">Total Price</label>
                    <p className="text-lg font-semibold text-green-600">
                      ${projectDetail.budget.total_price?.toLocaleString()}
                    </p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-600">Margin</label>
                    <p className="text-lg font-semibold text-blue-600">
                      {projectDetail.budget.margin_percentage?.toFixed(1)}%
                    </p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-600">Approved</label>
                    <p className={`text-lg font-semibold ${
                      projectDetail.budget.is_approved ? 'text-green-600' : 'text-yellow-600'
                    }`}>
                      {projectDetail.budget.is_approved ? 'Yes' : 'Pending'}
                    </p>
                  </div>
                </div>
              </div>
            )}
            
            {/* Actions */}
            <div className="border-t pt-6 flex space-x-3">
              <button className="btn-primary flex-1">Create Budget</button>
              <button className="btn-secondary flex-1">View Cash Flow</button>
              <button className="btn-outline flex-1">ROI Analysis</button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default FinancialDashboard