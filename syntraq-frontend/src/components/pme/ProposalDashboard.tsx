/**
 * © 2025 Aliff Capital, Quartermasters FZC, and SkillvenzA. All rights reserved.
 * 
 * Syntraq AI - PME (Proposal Management Engine) Dashboard
 * A Joint Innovation by Aliff Capital, Quartermasters FZC, and SkillvenzA
 */

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { pmeAPI, opportunitiesAPI } from '../../services/api'
import { Proposal, ProposalSection, ProposalReview } from '../../types'
import { format } from 'date-fns'

const ProposalDashboard = () => {
  const [selectedTab, setSelectedTab] = useState<'proposals' | 'sections' | 'reviews'>('proposals')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [selectedProposal, setSelectedProposal] = useState<Proposal | null>(null)
  const queryClient = useQueryClient()

  // Fetch data
  const { data: proposals, isLoading: proposalsLoading } = useQuery<Proposal[]>(
    'proposals',
    () => pmeAPI.getProposals({ limit: 50 })
  )

  const { data: opportunities } = useQuery(
    'opportunities-for-proposals',
    () => opportunitiesAPI.getOpportunities({ status: 'go', limit: 20 })
  )

  // Mutations
  const createProposalMutation = useMutation(pmeAPI.createFromOpportunity, {
    onSuccess: () => {
      queryClient.invalidateQueries('proposals')
      setShowCreateModal(false)
    }
  })

  const generateContentMutation = useMutation(pmeAPI.generateSectionContent, {
    onSuccess: () => {
      queryClient.invalidateQueries(['proposal-detail', selectedProposal?.id])
    }
  })

  const checkComplianceMutation = useMutation(pmeAPI.checkCompliance, {
    onSuccess: () => {
      queryClient.invalidateQueries(['proposal-detail', selectedProposal?.id])
    }
  })

  const conductReviewMutation = useMutation(
    (data: { proposalId: number; reviewData: any }) => pmeAPI.conductReview(data.proposalId, data.reviewData),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['proposal-reviews', selectedProposal?.id])
      }
    }
  )

  const handleCreateProposal = (formData: any) => {
    createProposalMutation.mutate({
      user_id: 1, // This should come from auth context
      opportunity_id: formData.opportunityId,
      project_id: formData.projectId || undefined,
      delivery_plan_id: formData.deliveryPlanId || undefined
    })
  }

  const handleGenerateContent = (sectionId: number, context?: any) => {
    generateContentMutation.mutate(sectionId, context)
  }

  const getProposalStatusColor = (status: string) => {
    switch (status) {
      case 'ready': return 'bg-green-100 text-green-800'
      case 'in_progress': return 'bg-blue-100 text-blue-800'
      case 'review': return 'bg-yellow-100 text-yellow-800'
      case 'submitted': return 'bg-purple-100 text-purple-800'
      case 'awarded': return 'bg-green-100 text-green-800 font-bold'
      case 'not_awarded': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getReadinessGateColor = (passed: boolean) => {
    return passed ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
  }

  const getComplianceColor = (score: number) => {
    if (score >= 90) return 'text-green-600'
    if (score >= 70) return 'text-yellow-600'
    return 'text-red-600'
  }

  if (proposalsLoading) {
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
          <h1 className="text-3xl font-bold text-gray-900">📄 Proposal Management (PME)</h1>
          <p className="text-gray-600">AI-powered proposal creation and management</p>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={() => setShowCreateModal(true)}
            className="btn-primary"
          >
            Create Proposal
          </button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="card p-6">
          <div className="flex items-center">
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-600">Total Proposals</p>
              <p className="text-2xl font-bold text-gray-900">{proposals?.length || 0}</p>
            </div>
            <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
              📄
            </div>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center">
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-600">In Progress</p>
              <p className="text-2xl font-bold text-blue-600">
                {proposals?.filter(p => p.status === 'in_progress').length || 0}
              </p>
            </div>
            <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
              ⚡
            </div>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center">
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-600">Ready to Submit</p>
              <p className="text-2xl font-bold text-green-600">
                {proposals?.filter(p => p.status === 'ready').length || 0}
              </p>
            </div>
            <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
              ✅
            </div>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center">
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-600">Win Rate</p>
              <p className="text-2xl font-bold text-purple-600">
                {proposals && proposals.length > 0 ? 
                  Math.round((proposals.filter(p => p.status === 'awarded').length / 
                             proposals.filter(p => p.status === 'submitted' || p.status === 'awarded' || p.status === 'not_awarded').length) * 100) || 0 : 0}%
              </p>
            </div>
            <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center">
              🏆
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setSelectedTab('proposals')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              selectedTab === 'proposals'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Proposals ({proposals?.length || 0})
          </button>
          <button
            onClick={() => setSelectedTab('sections')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              selectedTab === 'sections'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Section Editor
          </button>
          <button
            onClick={() => setSelectedTab('reviews')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              selectedTab === 'reviews'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Reviews
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      {selectedTab === 'proposals' && (
        <div className="space-y-6">
          {proposals?.map(proposal => (
            <div key={proposal.id} className="card p-6 hover:shadow-lg transition-shadow cursor-pointer"
                 onClick={() => setSelectedProposal(proposal)}>
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-3">
                    <h3 className="text-lg font-medium text-gray-900">{proposal.proposal_title}</h3>
                    <span className="text-sm font-medium text-gray-500">#{proposal.proposal_number}</span>
                    <span className={`inline-flex px-2 py-1 text-xs rounded-full ${getProposalStatusColor(proposal.status)}`}>
                      {proposal.status.replace('_', ' ')}
                    </span>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                    <div>
                      <span className="text-sm text-gray-600">Progress:</span>
                      <div className="mt-1 w-full bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-blue-600 h-2 rounded-full" 
                          style={{ width: `${proposal.overall_progress_percentage || 0}%` }}
                        />
                      </div>
                      <span className="text-xs text-gray-500 mt-1">
                        {proposal.overall_progress_percentage || 0}% Complete
                      </span>
                    </div>
                    
                    <div>
                      <span className="text-sm text-gray-600">Compliance Score:</span>
                      <div className={`text-lg font-semibold ${getComplianceColor(proposal.compliance_score || 0)}`}>
                        {proposal.compliance_score?.toFixed(1) || 'N/A'}%
                      </div>
                    </div>
                    
                    <div>
                      <span className="text-sm text-gray-600">Deadline:</span>
                      <div className="text-sm font-medium">
                        {proposal.submission_deadline ? 
                          format(new Date(proposal.submission_deadline), 'MMM d, yyyy') : 'TBD'}
                      </div>
                    </div>
                  </div>
                  
                  {/* Readiness Gates */}
                  <div className="mb-4">
                    <span className="text-sm text-gray-600 block mb-2">Readiness Gates:</span>
                    <div className="flex flex-wrap gap-2">
                      {proposal.readiness_gates_status && Object.entries(proposal.readiness_gates_status).map(([gate, status]: any) => (
                        <span key={gate} className={`inline-flex px-2 py-1 text-xs rounded-full ${getReadinessGateColor(status.passed)}`}>
                          {gate.replace('_', ' ')}
                        </span>
                      ))}
                    </div>
                  </div>
                  
                  {/* AI Recommendations */}
                  {proposal.ai_recommendations && proposal.ai_recommendations.length > 0 && (
                    <div className="mt-3 p-3 bg-blue-50 rounded-lg">
                      <p className="text-sm font-medium text-blue-900">AI Recommendations:</p>
                      <ul className="text-xs text-blue-700 mt-1 space-y-1">
                        {proposal.ai_recommendations.slice(0, 2).map((rec, index) => (
                          <li key={index}>• {rec}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
                
                <div className="ml-4 text-right">
                  <div className="text-gray-600 text-sm">Created</div>
                  <div className="font-medium">{format(new Date(proposal.created_at), 'MMM d')}</div>
                  <div className="mt-3 space-y-2">
                    <button 
                      onClick={(e) => {
                        e.stopPropagation()
                        checkComplianceMutation.mutate(proposal.id)
                      }}
                      className="btn-outline text-xs block w-full"
                      disabled={checkComplianceMutation.isLoading}
                    >
                      Check Compliance
                    </button>
                    <button 
                      onClick={(e) => {
                        e.stopPropagation()
                        // Open review modal
                      }}
                      className="btn-secondary text-xs block w-full"
                    >
                      Start Review
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
          
          {(!proposals || proposals.length === 0) && (
            <div className="text-center py-12">
              <div className="text-6xl mb-4">📄</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Proposals Yet</h3>
              <p className="text-gray-600 mb-4">Create your first proposal from an opportunity</p>
              <button
                onClick={() => setShowCreateModal(true)}
                className="btn-primary"
              >
                Create Proposal
              </button>
            </div>
          )}
        </div>
      )}

      {selectedTab === 'sections' && (
        <div className="space-y-6">
          {selectedProposal ? (
            <ProposalSectionEditor 
              proposal={selectedProposal}
              onGenerateContent={handleGenerateContent}
              isGenerating={generateContentMutation.isLoading}
            />
          ) : (
            <div className="text-center py-12">
              <div className="text-6xl mb-4">📝</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">Select a Proposal</h3>
              <p className="text-gray-600">Choose a proposal from the Proposals tab to edit sections</p>
            </div>
          )}
        </div>
      )}

      {selectedTab === 'reviews' && (
        <div className="space-y-6">
          {selectedProposal ? (
            <ProposalReviewPanel 
              proposal={selectedProposal}
              onConductReview={(reviewData: any) => conductReviewMutation.mutate({ proposalId: selectedProposal.id, reviewData })}
              isReviewing={conductReviewMutation.isLoading}
            />
          ) : (
            <div className="text-center py-12">
              <div className="text-6xl mb-4">🔍</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">Select a Proposal</h3>
              <p className="text-gray-600">Choose a proposal from the Proposals tab to view reviews</p>
            </div>
          )}
        </div>
      )}

      {/* Create Proposal Modal */}
      {showCreateModal && (
        <CreateProposalModal
          opportunities={opportunities || []}
          onClose={() => setShowCreateModal(false)}
          onSubmit={handleCreateProposal}
          isLoading={createProposalMutation.isLoading}
        />
      )}

      {/* Proposal Detail Modal */}
      {selectedProposal && selectedTab === 'proposals' && (
        <ProposalDetailModal
          proposal={selectedProposal}
          onClose={() => setSelectedProposal(null)}
        />
      )}
    </div>
  )
}

// Proposal Section Editor Component
const ProposalSectionEditor = ({ proposal, onGenerateContent, isGenerating }: any) => {
  const { data: proposalDetail, isLoading } = useQuery(
    ['proposal-detail', proposal.id],
    () => pmeAPI.getProposal(proposal.id),
    { enabled: !!proposal.id }
  )

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-32">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="card p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Editing: {proposal.proposal_title}
        </h3>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {proposalDetail?.sections?.map((section: ProposalSection) => (
            <div key={section.id} className="border rounded-lg p-4">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h4 className="font-medium text-gray-900">{section.section_title}</h4>
                  <p className="text-sm text-gray-600">Section {section.section_number}</p>
                </div>
                <span className={`inline-flex px-2 py-1 text-xs rounded-full ${
                  section.compliance_status === 'compliant' ? 'bg-green-100 text-green-800' :
                  section.compliance_status === 'non_compliant' ? 'bg-red-100 text-red-800' :
                  'bg-yellow-100 text-yellow-800'
                }`}>
                  {section.compliance_status}
                </span>
              </div>
              
              <div className="space-y-3">
                <div>
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-sm text-gray-600">Completion</span>
                    <span className="text-sm font-medium">{section.completion_percentage}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-blue-600 h-2 rounded-full" 
                      style={{ width: `${section.completion_percentage}%` }}
                    />
                  </div>
                </div>
                
                <div className="flex justify-between items-center text-sm">
                  <span className="text-gray-600">Words:</span>
                  <span className="font-medium">{section.word_count}</span>
                </div>
                
                {section.ai_generated_content && (
                  <div className="text-xs text-blue-600 flex items-center">
                    <span className="mr-1">🤖</span>
                    AI Generated
                  </div>
                )}
                
                <div className="pt-3 border-t space-y-2">
                  <button
                    onClick={() => onGenerateContent(section.id)}
                    className="btn-primary text-xs w-full"
                    disabled={isGenerating}
                  >
                    {isGenerating ? 'Generating...' : 'Generate Content'}
                  </button>
                  <button className="btn-outline text-xs w-full">
                    Edit Manually
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

// Proposal Review Panel Component
const ProposalReviewPanel = ({ proposal, onConductReview, isReviewing }: any) => {
  const [selectedReviewType, setSelectedReviewType] = useState('compliance')

  const { data: reviews, isLoading } = useQuery(
    ['proposal-reviews', proposal.id],
    () => pmeAPI.getReviews(proposal.id),
    { enabled: !!proposal.id }
  )

  const handleStartReview = () => {
    onConductReview({
      review_type: selectedReviewType,
      sections_to_review: [] // Review all sections
    })
  }

  const getReviewScoreColor = (score: number) => {
    if (score >= 8) return 'text-green-600'
    if (score >= 6) return 'text-yellow-600'
    return 'text-red-600'
  }

  return (
    <div className="space-y-6">
      <div className="card p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-gray-900">
            Reviews for: {proposal.proposal_title}
          </h3>
          <div className="flex items-center space-x-3">
            <select
              value={selectedReviewType}
              onChange={(e) => setSelectedReviewType(e.target.value)}
              className="border border-gray-300 rounded-md px-3 py-2 text-sm"
            >
              <option value="compliance">Compliance Review</option>
              <option value="technical">Technical Review</option>
              <option value="pricing">Pricing Review</option>
              <option value="executive">Executive Review</option>
              <option value="pink_team">Pink Team Review</option>
              <option value="red_team">Red Team Review</option>
              <option value="gold_team">Gold Team Review</option>
            </select>
            <button
              onClick={handleStartReview}
              className="btn-primary"
              disabled={isReviewing}
            >
              {isReviewing ? 'Reviewing...' : 'Start Review'}
            </button>
          </div>
        </div>
        
        {isLoading ? (
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        ) : (
          <div className="space-y-4">
            {reviews?.map((review: ProposalReview) => (
              <div key={review.id} className="border rounded-lg p-4">
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h4 className="font-medium text-gray-900">{review.review_name}</h4>
                    <p className="text-sm text-gray-600 capitalize">{review.review_type.replace('_', ' ')}</p>
                  </div>
                  <div className="text-right">
                    <div className={`text-2xl font-bold ${getReviewScoreColor(review.overall_score || 0)}`}>
                      {review.overall_score?.toFixed(1) || 'N/A'}
                    </div>
                    <div className="text-xs text-gray-500">Overall Score</div>
                  </div>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                  <div>
                    <p className="text-sm font-medium text-green-900 mb-2">Strengths:</p>
                    <ul className="text-sm text-green-700 space-y-1">
                      {review.strengths?.slice(0, 3).map((strength, index) => (
                        <li key={index} className="flex items-start">
                          <span className="text-green-600 mr-2">•</span>
                          {strength}
                        </li>
                      ))}
                    </ul>
                  </div>
                  
                  <div>
                    <p className="text-sm font-medium text-red-900 mb-2">Weaknesses:</p>
                    <ul className="text-sm text-red-700 space-y-1">
                      {review.weaknesses?.slice(0, 3).map((weakness, index) => (
                        <li key={index} className="flex items-start">
                          <span className="text-red-600 mr-2">•</span>
                          {weakness}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
                
                {review.critical_issues && review.critical_issues.length > 0 && (
                  <div className="mt-4 p-3 bg-red-50 rounded-lg">
                    <p className="text-sm font-medium text-red-900 mb-2">Critical Issues:</p>
                    <ul className="text-sm text-red-700 space-y-1">
                      {review.critical_issues.map((issue, index) => (
                        <li key={index} className="flex items-start">
                          <span className="text-red-600 mr-2">⚠</span>
                          {issue}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                
                <div className="mt-4 text-xs text-gray-500">
                  Reviewed on {format(new Date(review.review_date), 'MMM d, yyyy')}
                </div>
              </div>
            ))}
            
            {(!reviews || reviews.length === 0) && (
              <div className="text-center py-8">
                <div className="text-4xl mb-2">🔍</div>
                <p className="text-gray-500">No reviews yet for this proposal</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

// Create Proposal Modal Component
const CreateProposalModal = ({ opportunities, onClose, onSubmit, isLoading }: any) => {
  const [formData, setFormData] = useState({
    opportunityId: '',
    projectId: '',
    deliveryPlanId: ''
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit({
      opportunityId: Number(formData.opportunityId),
      projectId: formData.projectId ? Number(formData.projectId) : undefined,
      deliveryPlanId: formData.deliveryPlanId ? Number(formData.deliveryPlanId) : undefined
    })
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Create Proposal</h2>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Opportunity *
            </label>
            <select
              value={formData.opportunityId}
              onChange={(e) => setFormData({ ...formData, opportunityId: e.target.value })}
              className="w-full border border-gray-300 rounded-md px-3 py-2"
              required
            >
              <option value="">Select opportunity</option>
              {opportunities.map((opp: any) => (
                <option key={opp.id} value={opp.id}>
                  {opp.title} - {opp.agency}
                </option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Financial Project ID
            </label>
            <input
              type="number"
              value={formData.projectId}
              onChange={(e) => setFormData({ ...formData, projectId: e.target.value })}
              className="w-full border border-gray-300 rounded-md px-3 py-2"
              placeholder="Optional"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Delivery Plan ID
            </label>
            <input
              type="number"
              value={formData.deliveryPlanId}
              onChange={(e) => setFormData({ ...formData, deliveryPlanId: e.target.value })}
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
              {isLoading ? 'Creating...' : 'Create Proposal'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// Proposal Detail Modal Component
const ProposalDetailModal = ({ proposal, onClose }: any) => {
  const getComplianceColor = (score: number) => {
    if (score >= 90) return 'text-green-600'
    if (score >= 70) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getReadinessGateColor = (passed: boolean) => {
    return passed ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
  }
  const { data: readinessGates, isLoading: gatesLoading } = useQuery(
    ['readiness-gates', proposal.id],
    () => pmeAPI.assessReadinessGates(proposal.id),
    { enabled: !!proposal.id }
  )

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-bold text-gray-900">{proposal.proposal_title}</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            ✕
          </button>
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Proposal Info */}
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium text-gray-600">Proposal Number</label>
              <p className="text-lg font-semibold">{proposal.proposal_number}</p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-600">Status</label>
              <p className="text-lg font-semibold capitalize">{proposal.status.replace('_', ' ')}</p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-600">Progress</label>
              <div className="mt-1 w-full bg-gray-200 rounded-full h-3">
                <div 
                  className="bg-blue-600 h-3 rounded-full" 
                  style={{ width: `${proposal.overall_progress_percentage || 0}%` }}
                />
              </div>
              <p className="text-sm text-gray-600 mt-1">{proposal.overall_progress_percentage || 0}% Complete</p>
            </div>
            <div>
              <label className="text-sm font-medium text-gray-600">Compliance Score</label>
              <p className={`text-2xl font-bold ${getComplianceColor(proposal.compliance_score || 0)}`}>
                {proposal.compliance_score?.toFixed(1) || 'N/A'}%
              </p>
            </div>
            {proposal.submission_deadline && (
              <div>
                <label className="text-sm font-medium text-gray-600">Submission Deadline</label>
                <p className="text-lg font-semibold text-red-600">
                  {format(new Date(proposal.submission_deadline), 'MMM d, yyyy h:mm a')}
                </p>
              </div>
            )}
          </div>
          
          {/* Readiness Gates */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Readiness Gates</h3>
            {gatesLoading ? (
              <div className="flex items-center justify-center h-32">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
              </div>
            ) : (
              <div className="space-y-3">
                {readinessGates?.gate_assessments && Object.entries(readinessGates.gate_assessments).map(([gate, status]: any) => (
                  <div key={gate} className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex-1">
                      <p className="font-medium text-gray-900 capitalize">{gate.replace('_', ' ')}</p>
                      {status.issues && status.issues.length > 0 && (
                        <p className="text-sm text-red-600 mt-1">{status.issues[0]}</p>
                      )}
                    </div>
                    <span className={`inline-flex px-2 py-1 text-xs rounded-full ${getReadinessGateColor(status.passed)}`}>
                      {status.passed ? 'Passed' : 'Failed'}
                    </span>
                  </div>
                ))}
                
                <div className="mt-4 p-4 bg-blue-50 rounded-lg">
                  <div className="flex justify-between items-center">
                    <span className="font-medium text-blue-900">Overall Readiness</span>
                    <span className="text-lg font-bold text-blue-600">
                      {readinessGates?.readiness_percentage || 0}%
                    </span>
                  </div>
                  <div className="mt-2">
                    <span className={`inline-flex px-3 py-1 text-sm rounded-full ${
                      readinessGates?.ready_for_submission ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    }`}>
                      {readinessGates?.ready_for_submission ? 'Ready for Submission' : 'Not Ready'}
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default ProposalDashboard