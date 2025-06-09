/**
 * © 2025 Aliff Capital, Quartermasters FZC, and SkillvenzA. All rights reserved.
 * 
 * Syntraq AI - ARTS (AI Role-Based Team Simulation) Dashboard
 * A Joint Innovation by Aliff Capital, Quartermasters FZC, and SkillvenzA
 */

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { artsAPI } from '../../services/api'
import { AIAgent, AgentTask, TeamCollaboration } from '../../types'
import { format } from 'date-fns'

const ARTSDashboard = () => {
  const [selectedTab, setSelectedTab] = useState<'agents' | 'tasks' | 'collaborations'>('agents')
  const [showInitializeModal, setShowInitializeModal] = useState(false)
  const [selectedAgent, setSelectedAgent] = useState<AIAgent | null>(null)
  const queryClient = useQueryClient()

  // Fetch data
  const { data: agents, isLoading: agentsLoading } = useQuery<AIAgent[]>(
    'arts-agents',
    () => artsAPI.getAgents()
  )

  const { data: tasks, isLoading: tasksLoading } = useQuery<AgentTask[]>(
    'arts-tasks',
    () => artsAPI.getTasks({ limit: 50 })
  )

  const { data: collaborations, isLoading: collaborationsLoading } = useQuery<TeamCollaboration[]>(
    'arts-collaborations',
    () => artsAPI.getCollaborations()
  )

  // Mutations
  const initializeTeamMutation = useMutation(artsAPI.initializeTeam, {
    onSuccess: () => {
      queryClient.invalidateQueries('arts-agents')
      setShowInitializeModal(false)
    }
  })

  const assignTaskMutation = useMutation(artsAPI.assignTask, {
    onSuccess: () => {
      queryClient.invalidateQueries('arts-tasks')
    }
  })

  const handleInitializeTeam = (formData: any) => {
    initializeTeamMutation.mutate({
      project_id: formData.projectId,
      team_requirements: {
        team_size: formData.teamSize,
        required_specializations: formData.specializations,
        project_type: formData.projectType,
        complexity_level: formData.complexityLevel
      },
      opportunity_context: formData.opportunityContext
    })
  }

  const handleAssignTask = (agentId: number, taskData: any) => {
    assignTaskMutation.mutate({
      agent_id: agentId,
      task_description: taskData.description,
      priority: taskData.priority,
      context: taskData.context
    })
  }

  const getAgentStatusColor = (status: string) => {
    switch (status) {
      case 'available': return 'bg-green-100 text-green-800'
      case 'busy': return 'bg-yellow-100 text-yellow-800'
      case 'offline': return 'bg-gray-100 text-gray-800'
      default: return 'bg-blue-100 text-blue-800'
    }
  }

  const getTaskPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'bg-red-100 text-red-800'
      case 'medium': return 'bg-yellow-100 text-yellow-800'
      case 'low': return 'bg-green-100 text-green-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  if (agentsLoading || tasksLoading || collaborationsLoading) {
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
          <h1 className="text-3xl font-bold text-gray-900">🤖 AI Team Simulation (ARTS)</h1>
          <p className="text-gray-600">Manage your AI-powered project team</p>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={() => setShowInitializeModal(true)}
            className="btn-primary"
          >
            Initialize New Team
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="card p-6">
          <div className="flex items-center">
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-600">Total Agents</p>
              <p className="text-2xl font-bold text-gray-900">{agents?.length || 0}</p>
            </div>
            <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
              🤖
            </div>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center">
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-600">Available</p>
              <p className="text-2xl font-bold text-green-600">
                {agents?.filter(a => a.availability_status === 'available').length || 0}
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
              <p className="text-sm font-medium text-gray-600">Active Tasks</p>
              <p className="text-2xl font-bold text-blue-600">
                {tasks?.filter(t => t.status === 'active').length || 0}
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
              <p className="text-sm font-medium text-gray-600">Avg Performance</p>
              <p className="text-2xl font-bold text-purple-600">
                {agents?.length ? 
                  Math.round(agents.reduce((acc, a) => acc + a.performance_score, 0) / agents.length) : 0}%
              </p>
            </div>
            <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center">
              📊
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setSelectedTab('agents')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              selectedTab === 'agents'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            AI Agents ({agents?.length || 0})
          </button>
          <button
            onClick={() => setSelectedTab('tasks')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              selectedTab === 'tasks'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Tasks ({tasks?.length || 0})
          </button>
          <button
            onClick={() => setSelectedTab('collaborations')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              selectedTab === 'collaborations'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Collaborations ({collaborations?.length || 0})
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      {selectedTab === 'agents' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {agents?.map(agent => (
            <div key={agent.id} className="card p-6 hover:shadow-lg transition-shadow">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-900">{agent.agent_name}</h3>
                  <p className="text-sm text-gray-600">{agent.specialization}</p>
                </div>
                <span className={`inline-flex px-2 py-1 text-xs rounded-full ${getAgentStatusColor(agent.availability_status)}`}>
                  {agent.availability_status}
                </span>
              </div>
              
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Performance</span>
                  <span className="text-sm font-medium text-green-600">{agent.performance_score}%</span>
                </div>
                
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Workload</span>
                  <span className="text-sm font-medium">{agent.current_workload}/10</span>
                </div>
                
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Expertise</span>
                  <span className="text-sm font-medium capitalize">{agent.expertise_level}</span>
                </div>
                
                <div className="pt-3 border-t">
                  <p className="text-xs text-gray-600 mb-2">Communication Style:</p>
                  <p className="text-sm text-gray-800 capitalize">{agent.communication_style}</p>
                </div>
                
                <div className="pt-3 flex space-x-2">
                  <button
                    onClick={() => setSelectedAgent(agent)}
                    className="btn-secondary text-xs flex-1"
                  >
                    Assign Task
                  </button>
                  <button className="btn-outline text-xs flex-1">
                    View Details
                  </button>
                </div>
              </div>
            </div>
          ))}
          
          {(!agents || agents.length === 0) && (
            <div className="col-span-full text-center py-12">
              <div className="text-6xl mb-4">🤖</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No AI Agents Yet</h3>
              <p className="text-gray-600 mb-4">Initialize your first AI team to get started</p>
              <button
                onClick={() => setShowInitializeModal(true)}
                className="btn-primary"
              >
                Initialize AI Team
              </button>
            </div>
          )}
        </div>
      )}

      {selectedTab === 'tasks' && (
        <div className="space-y-4">
          {tasks?.map(task => (
            <div key={task.id} className="card p-6">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    <h3 className="text-lg font-medium text-gray-900">{task.task_description}</h3>
                    <span className={`inline-flex px-2 py-1 text-xs rounded-full ${getTaskPriorityColor(task.priority)}`}>
                      {task.priority}
                    </span>
                    <span className={`inline-flex px-2 py-1 text-xs rounded-full ${
                      task.status === 'completed' ? 'bg-green-100 text-green-800' :
                      task.status === 'active' ? 'bg-blue-100 text-blue-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {task.status}
                    </span>
                  </div>
                  
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <span className="text-gray-600">Agent:</span>
                      <span className="ml-1 font-medium">
                        {agents?.find(a => a.id === task.agent_id)?.agent_name || 'Unknown'}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-600">Type:</span>
                      <span className="ml-1 font-medium capitalize">{task.task_type}</span>
                    </div>
                    <div>
                      <span className="text-gray-600">Assigned:</span>
                      <span className="ml-1 font-medium">{format(new Date(task.assigned_date), 'MMM d')}</span>
                    </div>
                    <div>
                      <span className="text-gray-600">Complexity:</span>
                      <span className="ml-1 font-medium">{task.complexity_score}/10</span>
                    </div>
                  </div>
                  
                  {task.due_date && (
                    <div className="mt-2 text-sm">
                      <span className="text-gray-600">Due:</span>
                      <span className="ml-1 font-medium">{format(new Date(task.due_date), 'MMM d, yyyy')}</span>
                    </div>
                  )}
                </div>
                
                <div className="ml-4">
                  <div className="text-right">
                    <p className="text-sm text-gray-600">Progress</p>
                    <p className="text-lg font-semibold">
                      {task.actual_hours ? `${task.actual_hours}h` : `${task.estimated_hours}h est`}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          ))}
          
          {(!tasks || tasks.length === 0) && (
            <div className="text-center py-12">
              <div className="text-6xl mb-4">📋</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Tasks Yet</h3>
              <p className="text-gray-600">Assign tasks to your AI agents to get started</p>
            </div>
          )}
        </div>
      )}

      {selectedTab === 'collaborations' && (
        <div className="space-y-4">
          {collaborations?.map(collab => (
            <div key={collab.id} className="card p-6">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="text-lg font-medium text-gray-900">{collab.objective}</h3>
                  <p className="text-sm text-gray-600 capitalize">{collab.collaboration_type}</p>
                </div>
                <span className={`inline-flex px-2 py-1 text-xs rounded-full ${
                  collab.status === 'completed' ? 'bg-green-100 text-green-800' :
                  collab.status === 'active' ? 'bg-blue-100 text-blue-800' :
                  'bg-gray-100 text-gray-800'
                }`}>
                  {collab.status}
                </span>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                <div>
                  <span className="text-gray-600">Participants:</span>
                  <span className="ml-1 font-medium">{collab.participants?.length || 0} agents</span>
                </div>
                <div>
                  <span className="text-gray-600">Decisions:</span>
                  <span className="ml-1 font-medium">{collab.decisions_made?.length || 0}</span>
                </div>
                <div>
                  <span className="text-gray-600">Deliverables:</span>
                  <span className="ml-1 font-medium">{collab.deliverables?.length || 0}</span>
                </div>
              </div>
              
              {collab.conversation_log && collab.conversation_log.length > 0 && (
                <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                  <p className="text-sm font-medium text-gray-900 mb-2">Latest Activity:</p>
                  <p className="text-sm text-gray-700">
                    {collab.conversation_log[collab.conversation_log.length - 1]?.message || 'No recent activity'}
                  </p>
                </div>
              )}
            </div>
          ))}
          
          {(!collaborations || collaborations.length === 0) && (
            <div className="text-center py-12">
              <div className="text-6xl mb-4">🤝</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Collaborations Yet</h3>
              <p className="text-gray-600">Start team collaborations to solve complex problems</p>
            </div>
          )}
        </div>
      )}

      {/* Initialize Team Modal */}
      {showInitializeModal && (
        <InitializeTeamModal
          onClose={() => setShowInitializeModal(false)}
          onSubmit={handleInitializeTeam}
          isLoading={initializeTeamMutation.isLoading}
        />
      )}

      {/* Assign Task Modal */}
      {selectedAgent && (
        <AssignTaskModal
          agent={selectedAgent}
          onClose={() => setSelectedAgent(null)}
          onSubmit={(taskData: any) => {
            handleAssignTask(selectedAgent.id, taskData)
            setSelectedAgent(null)
          }}
          isLoading={assignTaskMutation.isLoading}
        />
      )}
    </div>
  )
}

// Initialize Team Modal Component
const InitializeTeamModal = ({ onClose, onSubmit, isLoading }: any) => {
  const [formData, setFormData] = useState({
    projectId: '',
    teamSize: 5,
    specializations: [],
    projectType: '',
    complexityLevel: 'medium'
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit(formData)
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Initialize AI Team</h2>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Project ID
            </label>
            <input
              type="number"
              value={formData.projectId}
              onChange={(e) => setFormData({ ...formData, projectId: e.target.value })}
              className="w-full border border-gray-300 rounded-md px-3 py-2"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Team Size
            </label>
            <select
              value={formData.teamSize}
              onChange={(e) => setFormData({ ...formData, teamSize: Number(e.target.value) })}
              className="w-full border border-gray-300 rounded-md px-3 py-2"
            >
              <option value={3}>3 agents</option>
              <option value={5}>5 agents</option>
              <option value={8}>8 agents (full team)</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Project Type
            </label>
            <select
              value={formData.projectType}
              onChange={(e) => setFormData({ ...formData, projectType: e.target.value })}
              className="w-full border border-gray-300 rounded-md px-3 py-2"
              required
            >
              <option value="">Select type</option>
              <option value="proposal_development">Proposal Development</option>
              <option value="market_research">Market Research</option>
              <option value="technical_analysis">Technical Analysis</option>
              <option value="compliance_review">Compliance Review</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Complexity Level
            </label>
            <select
              value={formData.complexityLevel}
              onChange={(e) => setFormData({ ...formData, complexityLevel: e.target.value })}
              className="w-full border border-gray-300 rounded-md px-3 py-2"
            >
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
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
              {isLoading ? 'Initializing...' : 'Initialize Team'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// Assign Task Modal Component
const AssignTaskModal = ({ agent, onClose, onSubmit, isLoading }: any) => {
  const [taskData, setTaskData] = useState({
    description: '',
    priority: 'medium',
    context: {}
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit(taskData)
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md">
        <h2 className="text-xl font-bold text-gray-900 mb-4">
          Assign Task to {agent.agent_name}
        </h2>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Task Description
            </label>
            <textarea
              value={taskData.description}
              onChange={(e) => setTaskData({ ...taskData, description: e.target.value })}
              className="w-full border border-gray-300 rounded-md px-3 py-2 h-24"
              placeholder="Describe the task in detail..."
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Priority
            </label>
            <select
              value={taskData.priority}
              onChange={(e) => setTaskData({ ...taskData, priority: e.target.value })}
              className="w-full border border-gray-300 rounded-md px-3 py-2"
            >
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
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
              {isLoading ? 'Assigning...' : 'Assign Task'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default ARTSDashboard