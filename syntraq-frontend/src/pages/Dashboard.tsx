import { useQuery } from 'react-query'
import { opportunitiesAPI, decisionsAPI } from '../services/api'
import { format } from 'date-fns'

const Dashboard = () => {
  const { data: stats, isLoading: statsLoading } = useQuery(
    'dashboard-stats',
    opportunitiesAPI.getDashboardStats
  )

  const { data: decisionStats, isLoading: decisionStatsLoading } = useQuery(
    'decision-stats',
    () => decisionsAPI.getDecisionStats(30)
  )

  const { data: recentDecisions, isLoading: recentLoading } = useQuery(
    'recent-decisions',
    () => decisionsAPI.getRecentDecisions(10)
  )

  if (statsLoading || decisionStatsLoading || recentLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600">Overview of your opportunity pipeline</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="card p-6">
          <div className="flex items-center">
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-600">Total Opportunities</p>
              <p className="text-2xl font-bold text-gray-900">{stats?.total_opportunities || 0}</p>
            </div>
            <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
              📋
            </div>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center">
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-600">New Opportunities</p>
              <p className="text-2xl font-bold text-blue-600">{stats?.new_opportunities || 0}</p>
            </div>
            <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
              ✨
            </div>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center">
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-600">High Relevance</p>
              <p className="text-2xl font-bold text-green-600">{stats?.high_relevance_opportunities || 0}</p>
            </div>
            <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
              🎯
            </div>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center">
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-600">Decision Rate</p>
              <p className="text-2xl font-bold text-purple-600">{stats?.decision_rate?.toFixed(1) || 0}%</p>
            </div>
            <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center">
              ⚡
            </div>
          </div>
        </div>
      </div>

      {/* Decision Analytics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Decision Breakdown (30 days)</h3>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-green-600 font-medium">Go Decisions</span>
              <span className="text-2xl font-bold text-green-600">{decisionStats?.go_decisions || 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-red-600 font-medium">No-Go Decisions</span>
              <span className="text-2xl font-bold text-red-600">{decisionStats?.no_go_decisions || 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-yellow-600 font-medium">Bookmarked</span>
              <span className="text-2xl font-bold text-yellow-600">{decisionStats?.bookmark_decisions || 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-blue-600 font-medium">Under Review</span>
              <span className="text-2xl font-bold text-blue-600">{decisionStats?.validate_decisions || 0}</span>
            </div>
          </div>
          <div className="mt-4 pt-4 border-t border-gray-200">
            <div className="flex justify-between items-center">
              <span className="text-gray-600 font-medium">Go Rate</span>
              <span className="text-xl font-bold text-gray-900">{decisionStats?.go_rate || 0}%</span>
            </div>
          </div>
        </div>

        <div className="card p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Decisions</h3>
          <div className="space-y-3">
            {recentDecisions?.slice(0, 5).map((decision: any, index: number) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {decision.title}
                  </p>
                  <p className="text-xs text-gray-500">
                    {decision.agency} • {format(new Date(decision.decision_date), 'MMM d')}
                  </p>
                </div>
                <div className="ml-4">
                  <span className={`
                    inline-flex px-2 py-1 text-xs font-medium rounded-full
                    ${decision.decision === 'go' 
                      ? 'bg-green-100 text-green-800' 
                      : decision.decision === 'no-go'
                      ? 'bg-red-100 text-red-800'
                      : decision.decision === 'bookmark'
                      ? 'bg-yellow-100 text-yellow-800'
                      : 'bg-blue-100 text-blue-800'
                    }
                  `}>
                    {decision.decision}
                  </span>
                </div>
              </div>
            ))}
            {(!recentDecisions || recentDecisions.length === 0) && (
              <p className="text-gray-500 text-center py-4">No recent decisions</p>
            )}
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="card p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button className="btn-primary text-left p-4 h-auto">
            <div className="text-lg mb-1">🔄</div>
            <div className="font-medium">Sync SAM.gov</div>
            <div className="text-sm opacity-90">Fetch latest opportunities</div>
          </button>
          
          <button className="btn-secondary text-left p-4 h-auto">
            <div className="text-lg mb-1">🤖</div>
            <div className="font-medium text-gray-800">Process with AI</div>
            <div className="text-sm text-gray-600">Analyze pending opportunities</div>
          </button>
          
          <button className="btn-secondary text-left p-4 h-auto">
            <div className="text-lg mb-1">📊</div>
            <div className="font-medium text-gray-800">View Reports</div>
            <div className="text-sm text-gray-600">Detailed analytics</div>
          </button>
        </div>
      </div>
    </div>
  )
}

export default Dashboard