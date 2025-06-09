import { useState } from 'react'
import { useQuery, useMutation } from 'react-query'
import { Link } from 'react-router-dom'
import { opportunitiesAPI, aiAPI, decisionsAPI } from '../services/api'
import { format } from 'date-fns'
import toast from 'react-hot-toast'

const Opportunities = () => {
  const [filters, setFilters] = useState({
    status: '',
    min_relevance: ''
  })
  const [selectedOpportunities, setSelectedOpportunities] = useState<number[]>([])
  // const queryClient = useQueryClient() // Unused for now

  const { data: opportunities, isLoading, refetch } = useQuery(
    ['opportunities', filters],
    () => opportunitiesAPI.getOpportunities({
      status: filters.status || undefined,
      min_relevance: filters.min_relevance ? parseFloat(filters.min_relevance) : undefined
    })
  )

  const syncMutation = useMutation(opportunitiesAPI.syncSamGov, {
    onSuccess: (data) => {
      toast.success(`Synced ${data.new_opportunities} new opportunities`)
      refetch()
    },
    onError: () => {
      toast.error('Sync failed')
    }
  })

  const batchAIMutation = useMutation(
    (opportunityIds: number[]) => aiAPI.batchSummarize(opportunityIds),
    {
      onSuccess: () => {
        toast.success('AI processing completed')
        refetch()
        setSelectedOpportunities([])
      },
      onError: () => {
        toast.error('AI processing failed')
      }
    }
  )

  const makeDecisionMutation = useMutation(decisionsAPI.makeDecision, {
    onSuccess: () => {
      toast.success('Decision recorded')
      refetch()
    },
    onError: () => {
      toast.error('Failed to record decision')
    }
  })

  const handleSelectAll = () => {
    if (selectedOpportunities.length === opportunities?.length) {
      setSelectedOpportunities([])
    } else {
      setSelectedOpportunities(opportunities?.map((opp: any) => opp.id) || [])
    }
  }

  const handleSelectOpportunity = (id: number) => {
    setSelectedOpportunities(prev => 
      prev.includes(id) 
        ? prev.filter(oppId => oppId !== id)
        : [...prev, id]
    )
  }

  const getRelevanceClass = (score: number | null) => {
    if (!score) return 'bg-gray-100 text-gray-800'
    if (score >= 70) return 'relevance-high'
    if (score >= 50) return 'relevance-medium'
    return 'relevance-low'
  }

  const getRelevanceLabel = (score: number | null) => {
    if (!score) return 'Not Scored'
    if (score >= 70) return 'High'
    if (score >= 50) return 'Medium'
    return 'Low'
  }

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
          <h1 className="text-2xl font-bold text-gray-900">Opportunities</h1>
          <p className="text-gray-600">Manage your government contracting opportunities</p>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={() => syncMutation.mutate(7)}
            disabled={syncMutation.isLoading}
            className="btn-primary"
          >
            {syncMutation.isLoading ? 'Syncing...' : '🔄 Sync SAM.gov'}
          </button>
          {selectedOpportunities.length > 0 && (
            <button
              onClick={() => batchAIMutation.mutate(selectedOpportunities)}
              disabled={batchAIMutation.isLoading}
              className="btn-secondary"
            >
              {batchAIMutation.isLoading ? 'Processing...' : '🤖 Process Selected'}
            </button>
          )}
        </div>
      </div>

      {/* Filters */}
      <div className="card p-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
            <select
              value={filters.status}
              onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
              className="input-field"
            >
              <option value="">All Statuses</option>
              <option value="new">New</option>
              <option value="reviewed">Reviewed</option>
              <option value="decided">Decided</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Min Relevance</label>
            <select
              value={filters.min_relevance}
              onChange={(e) => setFilters(prev => ({ ...prev, min_relevance: e.target.value }))}
              className="input-field"
            >
              <option value="">Any Relevance</option>
              <option value="70">High (70%+)</option>
              <option value="50">Medium (50%+)</option>
              <option value="30">Low (30%+)</option>
            </select>
          </div>
          <div className="flex items-end">
            <button
              onClick={() => setFilters({ status: '', min_relevance: '' })}
              className="btn-secondary w-full"
            >
              Clear Filters
            </button>
          </div>
        </div>
      </div>

      {/* Opportunities List */}
      <div className="card">
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={selectedOpportunities.length === opportunities?.length && opportunities?.length > 0}
                onChange={handleSelectAll}
                className="rounded"
              />
              <span className="text-sm text-gray-600">
                {selectedOpportunities.length > 0 
                  ? `${selectedOpportunities.length} selected`
                  : `${opportunities?.length || 0} opportunities`
                }
              </span>
            </div>
            <div className="text-sm text-gray-500">
              Last updated: {format(new Date(), 'MMM d, h:mm a')}
            </div>
          </div>
        </div>

        <div className="divide-y divide-gray-200">
          {opportunities?.map((opportunity: any) => (
            <div key={opportunity.id} className="p-4 hover:bg-gray-50">
              <div className="flex items-start space-x-3">
                <input
                  type="checkbox"
                  checked={selectedOpportunities.includes(opportunity.id)}
                  onChange={() => handleSelectOpportunity(opportunity.id)}
                  className="mt-1 rounded"
                />
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <Link 
                        to={`/opportunities/${opportunity.id}`}
                        className="text-sm font-medium text-blue-600 hover:text-blue-500"
                      >
                        {opportunity.title}
                      </Link>
                      <p className="text-sm text-gray-500 mt-1">
                        {opportunity.agency} • {opportunity.notice_id}
                      </p>
                      <p className="text-sm text-gray-700 mt-2 line-clamp-2">
                        {opportunity.ai_summary || opportunity.description?.substring(0, 200) + '...'}
                      </p>
                    </div>
                    
                    <div className="ml-4 flex-shrink-0">
                      {opportunity.relevance_score && (
                        <span className={`
                          inline-flex px-2 py-1 text-xs font-medium rounded-full
                          ${getRelevanceClass(opportunity.relevance_score)}
                        `}>
                          {getRelevanceLabel(opportunity.relevance_score)} ({opportunity.relevance_score}%)
                        </span>
                      )}
                    </div>
                  </div>
                  
                  <div className="mt-3 flex items-center justify-between">
                    <div className="flex items-center space-x-4 text-xs text-gray-500">
                      <span>📅 Due: {format(new Date(opportunity.response_deadline), 'MMM d')}</span>
                      <span>🏢 {opportunity.naics_code}</span>
                      {opportunity.set_aside && <span>🎯 {opportunity.set_aside}</span>}
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      {!opportunity.user_decision ? (
                        <>
                          <button
                            onClick={() => makeDecisionMutation.mutate({
                              opportunity_id: opportunity.id,
                              decision: 'go'
                            })}
                            className="text-xs btn-success px-3 py-1"
                          >
                            Go
                          </button>
                          <button
                            onClick={() => makeDecisionMutation.mutate({
                              opportunity_id: opportunity.id,
                              decision: 'no-go'
                            })}
                            className="text-xs btn-danger px-3 py-1"
                          >
                            No-Go
                          </button>
                          <button
                            onClick={() => makeDecisionMutation.mutate({
                              opportunity_id: opportunity.id,
                              decision: 'bookmark'
                            })}
                            className="text-xs btn-secondary px-3 py-1"
                          >
                            Bookmark
                          </button>
                        </>
                      ) : (
                        <span className={`
                          text-xs px-3 py-1 rounded-full font-medium
                          ${opportunity.user_decision === 'go' ? 'bg-green-100 text-green-800' :
                            opportunity.user_decision === 'no-go' ? 'bg-red-100 text-red-800' :
                            'bg-yellow-100 text-yellow-800'
                          }
                        `}>
                          {opportunity.user_decision}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
          
          {(!opportunities || opportunities.length === 0) && (
            <div className="p-8 text-center text-gray-500">
              <p>No opportunities found. Try syncing with SAM.gov to fetch latest opportunities.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default Opportunities