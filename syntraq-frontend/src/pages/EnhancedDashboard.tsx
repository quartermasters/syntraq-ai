/**
 * © 2025 Aliff Capital, Quartermasters FZC, and SkillvenzA. All rights reserved.
 * 
 * Syntraq AI - Enhanced Dashboard with All Modules
 * A Joint Innovation by Aliff Capital, Quartermasters FZC, and SkillvenzA
 */

import { useState } from 'react'
import { useQuery } from 'react-query'
import { Link } from 'react-router-dom'
import { format } from 'date-fns'
import { opportunitiesAPI, decisionsAPI, artsAPI, fvmsAPI, pmeAPI, cahAPI } from '../services/api'
import { DashboardStats, FinancialMetrics, EngagementMetrics } from '../types'

const EnhancedDashboard = () => {
  const [selectedTimeframe, setSelectedTimeframe] = useState(30)

  // Existing dashboard data
  const { data: stats, isLoading: statsLoading } = useQuery<DashboardStats>(
    'dashboard-stats',
    opportunitiesAPI.getDashboardStats
  )

  const { data: decisionStats, isLoading: decisionStatsLoading } = useQuery(
    'decision-stats',
    () => decisionsAPI.getDecisionStats(selectedTimeframe)
  )

  // ARTS data
  const { data: artsAgents, isLoading: artsLoading } = useQuery(
    'arts-agents',
    () => artsAPI.getAgents()
  )

  const { data: artsTasks } = useQuery(
    'arts-tasks',
    () => artsAPI.getTasks({ status: 'active', limit: 10 })
  )

  // FVMS data
  const { data: financialDashboard, isLoading: financialLoading } = useQuery<FinancialMetrics>(
    'financial-dashboard',
    fvmsAPI.getFinancialDashboard
  )

  const { data: treasuryDashboard } = useQuery(
    'treasury-dashboard',
    fvmsAPI.getTreasuryDashboard
  )

  const { data: financialAlerts } = useQuery(
    'financial-alerts',
    () => fvmsAPI.getAlerts({ status: 'active', limit: 5 })
  )

  // PME data
  const { data: proposals, isLoading: proposalsLoading } = useQuery(
    'recent-proposals',
    () => pmeAPI.getProposals({ limit: 5 })
  )

  // CAH data
  const { data: communicationStats, isLoading: commStatsLoading } = useQuery<EngagementMetrics>(
    'communication-stats',
    () => cahAPI.getCommunicationStats(selectedTimeframe)
  )

  const { data: upcomingMeetings } = useQuery(
    'upcoming-meetings',
    () => cahAPI.getMeetings({ upcoming_only: true, limit: 5 })
  )

  const isLoading = statsLoading || decisionStatsLoading || artsLoading || 
                    financialLoading || proposalsLoading || commStatsLoading

  if (isLoading) {
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
          <h1 className="text-3xl font-bold text-gray-900">Syntraq AI Dashboard</h1>
          <p className="text-gray-600">AI-powered government contracting intelligence</p>
        </div>
        <div className="flex items-center space-x-4">
          <select
            value={selectedTimeframe}
            onChange={(e) => setSelectedTimeframe(Number(e.target.value))}
            className="border border-gray-300 rounded-md px-3 py-2 text-sm"
          >
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
          </select>
        </div>
      </div>

      {/* Main KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="card p-6 bg-gradient-to-r from-blue-500 to-blue-600 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-blue-100">Total Opportunities</p>
              <p className="text-3xl font-bold">{stats?.total_opportunities || 0}</p>
              <p className="text-blue-100 text-sm">AI Processed: {stats?.ai_processed_today || 0}</p>
            </div>
            <div className="text-4xl opacity-75">🎯</div>
          </div>
        </div>

        <div className="card p-6 bg-gradient-to-r from-green-500 to-green-600 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-green-100">Pipeline Value</p>
              <p className="text-3xl font-bold">
                ${financialDashboard?.portfolio_summary?.total_pipeline_value?.toLocaleString() || '0'}
              </p>
              <p className="text-green-100 text-sm">
                Active: ${financialDashboard?.portfolio_summary?.active_contract_value?.toLocaleString() || '0'}
              </p>
            </div>
            <div className="text-4xl opacity-75">💰</div>
          </div>
        </div>

        <div className="card p-6 bg-gradient-to-r from-purple-500 to-purple-600 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-purple-100">Active AI Agents</p>
              <p className="text-3xl font-bold">{artsAgents?.filter((a: any) => a.availability_status === 'available').length || 0}</p>
              <p className="text-purple-100 text-sm">
                Tasks: {artsTasks?.filter((t: any) => t.status === 'active').length || 0}
              </p>
            </div>
            <div className="text-4xl opacity-75">🤖</div>
          </div>
        </div>

        <div className="card p-6 bg-gradient-to-r from-orange-500 to-orange-600 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-orange-100">Communication Rate</p>
              <p className="text-3xl font-bold">{communicationStats?.engagement_metrics?.response_rate?.toFixed(1) || 0}%</p>
              <p className="text-orange-100 text-sm">
                Sent: {communicationStats?.engagement_metrics?.outbound_communications || 0}
              </p>
            </div>
            <div className="text-4xl opacity-75">💬</div>
          </div>
        </div>
      </div>

      {/* Module Overview Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        
        {/* ARTS Module */}
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">🤖 AI Team (ARTS)</h3>
            <Link to="/arts" className="text-blue-600 hover:text-blue-700 text-sm font-medium">
              View All →
            </Link>
          </div>
          <div className="space-y-3">
            {artsAgents?.slice(0, 3).map((agent: any) => (
              <div key={agent.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-900">{agent.agent_name}</p>
                  <p className="text-xs text-gray-500">{agent.specialization}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium text-green-600">{agent.performance_score}%</p>
                  <span className={`inline-flex px-2 py-1 text-xs rounded-full ${
                    agent.availability_status === 'available' 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-yellow-100 text-yellow-800'
                  }`}>
                    {agent.availability_status}
                  </span>
                </div>
              </div>
            ))}
            <div className="text-center pt-2">
              <button className="btn-secondary text-sm">Initialize New Team</button>
            </div>
          </div>
        </div>

        {/* FVMS Module */}
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">💰 Financial (FVMS)</h3>
            <Link to="/financial" className="text-blue-600 hover:text-blue-700 text-sm font-medium">
              View All →
            </Link>
          </div>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Cash Position</span>
              <span className="text-lg font-semibold text-green-600">
                ${treasuryDashboard?.treasury_overview?.current_cash_position?.toLocaleString() || '0'}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Working Capital</span>
              <span className="text-lg font-semibold text-blue-600">
                ${treasuryDashboard?.treasury_overview?.working_capital?.toLocaleString() || '0'}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Monthly Burn</span>
              <span className="text-lg font-semibold text-orange-600">
                ${treasuryDashboard?.treasury_overview?.burn_rate_monthly?.toLocaleString() || '0'}
              </span>
            </div>
            {financialAlerts && financialAlerts.length > 0 && (
              <div className="mt-4 p-3 bg-red-50 rounded-lg">
                <p className="text-sm font-medium text-red-800">
                  {financialAlerts.length} Active Alert{financialAlerts.length > 1 ? 's' : ''}
                </p>
                <p className="text-xs text-red-600">{financialAlerts[0]?.title}</p>
              </div>
            )}
          </div>
        </div>

        {/* PME Module */}
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">📄 Proposals (PME)</h3>
            <Link to="/proposals" className="text-blue-600 hover:text-blue-700 text-sm font-medium">
              View All →
            </Link>
          </div>
          <div className="space-y-3">
            {proposals?.slice(0, 3).map((proposal: any) => (
              <div key={proposal.id} className="p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-sm font-medium text-gray-900 truncate">{proposal.proposal_title}</p>
                  <span className={`inline-flex px-2 py-1 text-xs rounded-full ${
                    proposal.status === 'ready' 
                      ? 'bg-green-100 text-green-800'
                      : proposal.status === 'in_progress'
                      ? 'bg-blue-100 text-blue-800'
                      : 'bg-gray-100 text-gray-800'
                  }`}>
                    {proposal.status}
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-blue-600 h-2 rounded-full" 
                    style={{ width: `${proposal.overall_progress_percentage || 0}%` }}
                  />
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  {proposal.overall_progress_percentage || 0}% Complete
                </p>
              </div>
            ))}
            {(!proposals || proposals.length === 0) && (
              <div className="text-center py-4">
                <p className="text-gray-500 text-sm">No active proposals</p>
                <button className="btn-secondary text-sm mt-2">Create Proposal</button>
              </div>
            )}
          </div>
        </div>

        {/* CAH Module */}
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">💬 Communications (CAH)</h3>
            <Link to="/communications" className="text-blue-600 hover:text-blue-700 text-sm font-medium">
              View All →
            </Link>
          </div>
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center">
                <p className="text-2xl font-bold text-blue-600">
                  {communicationStats?.engagement_metrics?.total_communications || 0}
                </p>
                <p className="text-xs text-gray-600">Total Comms</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-green-600">
                  {communicationStats?.engagement_metrics?.response_rate?.toFixed(0) || 0}%
                </p>
                <p className="text-xs text-gray-600">Response Rate</p>
              </div>
            </div>
            {upcomingMeetings && upcomingMeetings.length > 0 && (
              <div className="mt-4">
                <p className="text-sm font-medium text-gray-900 mb-2">Upcoming Meetings</p>
                {upcomingMeetings.slice(0, 2).map((meeting: any) => (
                  <div key={meeting.id} className="p-2 bg-blue-50 rounded text-sm mb-2">
                    <p className="font-medium text-blue-900">{meeting.title}</p>
                    <p className="text-blue-700 text-xs">
                      {format(new Date(meeting.scheduled_date), 'MMM d, h:mm a')}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Decision Analytics */}
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">⚡ Decision Analytics</h3>
            <Link to="/opportunities" className="text-blue-600 hover:text-blue-700 text-sm font-medium">
              View All →
            </Link>
          </div>
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center">
                <p className="text-2xl font-bold text-green-600">{decisionStats?.go_decisions || 0}</p>
                <p className="text-xs text-gray-600">Go Decisions</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-red-600">{decisionStats?.no_go_decisions || 0}</p>
                <p className="text-xs text-gray-600">No-Go</p>
              </div>
            </div>
            <div className="flex justify-between items-center pt-3 border-t">
              <span className="text-sm text-gray-600">Go Rate</span>
              <span className="text-lg font-semibold text-purple-600">{decisionStats?.go_rate || 0}%</span>
            </div>
          </div>
        </div>

        {/* AI Insights */}
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">🧠 AI Insights</h3>
          </div>
          <div className="space-y-3">
            <div className="p-3 bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg">
              <p className="text-sm font-medium text-purple-900">Today's Recommendations</p>
              <ul className="text-xs text-purple-700 mt-2 space-y-1">
                <li>• {artsTasks?.filter((t: any) => t.status === 'active').length || 0} active AI tasks running</li>
                <li>• {financialAlerts?.filter((a: any) => a.severity === 'high').length || 0} high-priority financial alerts</li>
                <li>• {proposals?.filter((p: any) => p.status === 'ready').length || 0} proposals ready for submission</li>
              </ul>
            </div>
            <button className="w-full btn-primary text-sm">Generate AI Report</button>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="card p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">🚀 Quick Actions</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
          <Link to="/opportunities/sync" className="btn-primary text-center p-4 h-auto">
            <div className="text-lg mb-1">🔄</div>
            <div className="font-medium text-sm">Sync SAM.gov</div>
          </Link>
          
          <button className="btn-secondary text-center p-4 h-auto">
            <div className="text-lg mb-1">🤖</div>
            <div className="font-medium text-sm">Init AI Team</div>
          </button>
          
          <Link to="/financial/projects/new" className="btn-secondary text-center p-4 h-auto">
            <div className="text-lg mb-1">💰</div>
            <div className="font-medium text-sm">New Project</div>
          </Link>
          
          <Link to="/proposals/create" className="btn-secondary text-center p-4 h-auto">
            <div className="text-lg mb-1">📄</div>
            <div className="font-medium text-sm">Create Proposal</div>
          </Link>
          
          <Link to="/communications/compose" className="btn-secondary text-center p-4 h-auto">
            <div className="text-lg mb-1">💬</div>
            <div className="font-medium text-sm">Send Message</div>
          </Link>
          
          <Link to="/reports" className="btn-secondary text-center p-4 h-auto">
            <div className="text-lg mb-1">📊</div>
            <div className="font-medium text-sm">View Reports</div>
          </Link>
        </div>
      </div>
    </div>
  )
}

export default EnhancedDashboard