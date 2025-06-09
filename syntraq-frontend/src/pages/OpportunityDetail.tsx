import { useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { opportunitiesAPI, aiAPI, decisionsAPI } from '../services/api'
import { format } from 'date-fns'
import toast from 'react-hot-toast'

const OpportunityDetail = () => {
  const { id } = useParams<{ id: string }>()
  const queryClient = useQueryClient()

  const { data: opportunity, isLoading } = useQuery(
    ['opportunity', id],
    () => opportunitiesAPI.getOpportunity(parseInt(id!)),
    { enabled: !!id }
  )

  const aiProcessMutation = useMutation(
    () => aiAPI.generateSummary(parseInt(id!)),
    {
      onSuccess: () => {
        toast.success('AI analysis completed')
        queryClient.invalidateQueries(['opportunity', id])
      },
      onError: () => {
        toast.error('AI analysis failed')
      }
    }
  )

  const makeDecisionMutation = useMutation(decisionsAPI.makeDecision, {
    onSuccess: () => {
      toast.success('Decision recorded')
      queryClient.invalidateQueries(['opportunity', id])
    },
    onError: () => {
      toast.error('Failed to record decision')
    }
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (!opportunity) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Opportunity not found</p>
      </div>
    )
  }

  const getRelevanceClass = (score: number | null) => {
    if (!score) return 'bg-gray-100 text-gray-800'
    if (score >= 70) return 'bg-green-100 text-green-800'
    if (score >= 50) return 'bg-yellow-100 text-yellow-800'
    return 'bg-red-100 text-red-800'
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-gray-900">{opportunity.title}</h1>
          <p className="text-gray-600 mt-1">
            {opportunity.agency} • {opportunity.notice_id}
          </p>
        </div>
        
        <div className="flex items-center space-x-2">
          {!opportunity.ai_summary && (
            <button
              onClick={() => aiProcessMutation.mutate()}
              disabled={aiProcessMutation.isLoading}
              className="btn-primary"
            >
              {aiProcessMutation.isLoading ? 'Processing...' : '🤖 Analyze with AI'}
            </button>
          )}
          
          {opportunity.relevance_score && (
            <span className={`
              px-3 py-1 text-sm font-medium rounded-full
              ${getRelevanceClass(opportunity.relevance_score)}
            `}>
              {opportunity.relevance_score}% Relevance
            </span>
          )}
        </div>
      </div>

      {/* AI Summary Card */}
      {opportunity.ai_summary && (
        <div className="card p-6 bg-blue-50 border-blue-200">
          <h3 className="text-lg font-semibold text-blue-900 mb-3">🤖 AI Executive Summary</h3>
          <p className="text-blue-800 mb-4">{opportunity.ai_summary}</p>
          
          {opportunity.key_requirements && opportunity.key_requirements.length > 0 && (
            <div className="mb-4">
              <h4 className="font-medium text-blue-900 mb-2">Key Requirements:</h4>
              <ul className="list-disc list-inside text-blue-800 space-y-1">
                {opportunity.key_requirements.map((req: string, index: number) => (
                  <li key={index}>{req}</li>
                ))}
              </ul>
            </div>
          )}
          
          {opportunity.decision_factors && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
              {opportunity.decision_factors.pros && (
                <div>
                  <h4 className="font-medium text-green-700 mb-1">✅ Pros</h4>
                  <p className="text-sm text-green-600">{opportunity.decision_factors.pros}</p>
                </div>
              )}
              {opportunity.decision_factors.cons && (
                <div>
                  <h4 className="font-medium text-red-700 mb-1">⚠️ Cons</h4>
                  <p className="text-sm text-red-600">{opportunity.decision_factors.cons}</p>
                </div>
              )}
              {opportunity.decision_factors.competition && (
                <div>
                  <h4 className="font-medium text-orange-700 mb-1">🏆 Competition</h4>
                  <p className="text-sm text-orange-600">{opportunity.decision_factors.competition}</p>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Decision Section */}
      {!opportunity.user_decision && (
        <div className="card p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Make Decision</h3>
          <div className="flex space-x-3">
            <button
              onClick={() => makeDecisionMutation.mutate({
                opportunity_id: opportunity.id,
                decision: 'go',
                reason: 'Approved from detail view'
              })}
              className="btn-success"
            >
              ✅ Go Decision
            </button>
            <button
              onClick={() => makeDecisionMutation.mutate({
                opportunity_id: opportunity.id,
                decision: 'no-go',
                reason: 'Rejected from detail view'
              })}
              className="btn-danger"
            >
              ❌ No-Go Decision
            </button>
            <button
              onClick={() => makeDecisionMutation.mutate({
                opportunity_id: opportunity.id,
                decision: 'bookmark',
                reason: 'Bookmarked for later review'
              })}
              className="btn-secondary"
            >
              🔖 Bookmark
            </button>
            <button
              onClick={() => makeDecisionMutation.mutate({
                opportunity_id: opportunity.id,
                decision: 'validate',
                reason: 'Needs further validation'
              })}
              className="btn-secondary"
            >
              🔍 Needs Validation
            </button>
          </div>
        </div>
      )}

      {/* Current Decision */}
      {opportunity.user_decision && (
        <div className="card p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Current Decision</h3>
          <div className="flex items-center space-x-4">
            <span className={`
              px-3 py-1 text-sm font-medium rounded-full
              ${opportunity.user_decision === 'go' ? 'bg-green-100 text-green-800' :
                opportunity.user_decision === 'no-go' ? 'bg-red-100 text-red-800' :
                'bg-yellow-100 text-yellow-800'
              }
            `}>
              {opportunity.user_decision}
            </span>
            {opportunity.decision_reason && (
              <span className="text-gray-600">{opportunity.decision_reason}</span>
            )}
            {opportunity.decision_date && (
              <span className="text-gray-500 text-sm">
                {format(new Date(opportunity.decision_date), 'MMM d, yyyy')}
              </span>
            )}
          </div>
        </div>
      )}

      {/* Opportunity Details */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Opportunity Details</h3>
          <dl className="space-y-3">
            <div>
              <dt className="text-sm font-medium text-gray-500">Posted Date</dt>
              <dd className="text-sm text-gray-900">{format(new Date(opportunity.posted_date), 'MMM d, yyyy')}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Response Deadline</dt>
              <dd className="text-sm text-gray-900">{format(new Date(opportunity.response_deadline), 'MMM d, yyyy')}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">NAICS Code</dt>
              <dd className="text-sm text-gray-900">{opportunity.naics_code} - {opportunity.naics_description}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">PSC Code</dt>
              <dd className="text-sm text-gray-900">{opportunity.psc_code}</dd>
            </div>
            {opportunity.set_aside && (
              <div>
                <dt className="text-sm font-medium text-gray-500">Set Aside</dt>
                <dd className="text-sm text-gray-900">{opportunity.set_aside}</dd>
              </div>
            )}
            <div>
              <dt className="text-sm font-medium text-gray-500">Place of Performance</dt>
              <dd className="text-sm text-gray-900">{opportunity.place_of_performance || 'Not specified'}</dd>
            </div>
          </dl>
        </div>

        <div className="card p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Contact Information</h3>
          {opportunity.contact_info && Object.keys(opportunity.contact_info).length > 0 ? (
            <div className="space-y-3">
              {Object.entries(opportunity.contact_info).map(([type, contact]: [string, any]) => (
                <div key={type}>
                  <dt className="text-sm font-medium text-gray-500 capitalize">{type}</dt>
                  <dd className="text-sm text-gray-900">
                    {contact.name && <div>{contact.name}</div>}
                    {contact.email && <div>{contact.email}</div>}
                    {contact.phone && <div>{contact.phone}</div>}
                  </dd>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500">No contact information available</p>
          )}
        </div>
      </div>

      {/* Description */}
      <div className="card p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Description</h3>
        <div className="prose max-w-none">
          <p className="text-gray-700 whitespace-pre-wrap">{opportunity.description}</p>
        </div>
      </div>

      {/* Attachments */}
      {opportunity.attachments && opportunity.attachments.length > 0 && (
        <div className="card p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Attachments</h3>
          <div className="space-y-2">
            {opportunity.attachments.map((attachment: any, index: number) => (
              <div key={index} className="flex items-center space-x-3">
                <span className="text-blue-600">📎</span>
                <a
                  href={attachment.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:text-blue-500 underline"
                >
                  {attachment.description || `Attachment ${index + 1}`}
                </a>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default OpportunityDetail