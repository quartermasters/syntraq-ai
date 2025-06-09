/**
 * © 2025 Aliff Capital, Quartermasters FZC, and SkillvenzA. All rights reserved.
 * 
 * Syntraq AI - CAH (Communication & Arrangement Hub) Dashboard
 * A Joint Innovation by Aliff Capital, Quartermasters FZC, and SkillvenzA
 */

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { cahAPI } from '../../services/api'
import { Contact, Communication, Meeting, CommunicationTemplate } from '../../types'
import { format } from 'date-fns'

const CommunicationHub = () => {
  const [selectedTab, setSelectedTab] = useState<'contacts' | 'communications' | 'meetings' | 'templates'>('communications')
  const [showComposeModal, setShowComposeModal] = useState(false)
  const [showCreateContactModal, setShowCreateContactModal] = useState(false)
  const [showScheduleMeetingModal, setShowScheduleMeetingModal] = useState(false)
  const [selectedContact, setSelectedContact] = useState<Contact | null>(null)
  const queryClient = useQueryClient()

  // Fetch data
  const { data: communications, isLoading: commsLoading } = useQuery<Communication[]>(
    'communications',
    () => cahAPI.getCommunications({ limit: 50 })
  )

  const { data: contacts, isLoading: contactsLoading } = useQuery<Contact[]>(
    'contacts',
    () => cahAPI.getContacts()
  )

  const { data: meetings, isLoading: meetingsLoading } = useQuery<Meeting[]>(
    'meetings',
    () => cahAPI.getMeetings({ limit: 30 })
  )

  const { data: templates } = useQuery<CommunicationTemplate[]>(
    'communication-templates',
    () => cahAPI.getTemplates()
  )

  const { data: communicationStats } = useQuery(
    'communication-stats',
    () => cahAPI.getCommunicationStats(30)
  )

  // Mutations
  const sendCommunicationMutation = useMutation(cahAPI.sendCommunication, {
    onSuccess: () => {
      queryClient.invalidateQueries('communications')
      setShowComposeModal(false)
    }
  })

  const createContactMutation = useMutation(cahAPI.createContact, {
    onSuccess: () => {
      queryClient.invalidateQueries('contacts')
      setShowCreateContactModal(false)
    }
  })

  const scheduleMeetingMutation = useMutation(cahAPI.scheduleMeeting, {
    onSuccess: () => {
      queryClient.invalidateQueries('meetings')
      setShowScheduleMeetingModal(false)
    }
  })


  const handleSendCommunication = (formData: any) => {
    sendCommunicationMutation.mutate(formData)
  }

  const handleCreateContact = (formData: any) => {
    createContactMutation.mutate(formData)
  }

  const handleScheduleMeeting = (formData: any) => {
    scheduleMeetingMutation.mutate(formData)
  }

  const getCommunicationTypeColor = (type: string) => {
    switch (type) {
      case 'email': return 'bg-blue-100 text-blue-800'
      case 'phone': return 'bg-green-100 text-green-800'
      case 'meeting': return 'bg-purple-100 text-purple-800'
      case 'document': return 'bg-orange-100 text-orange-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getContactTypeColor = (type: string) => {
    switch (type) {
      case 'government': return 'bg-blue-100 text-blue-800'
      case 'vendor': return 'bg-green-100 text-green-800'
      case 'partner': return 'bg-purple-100 text-purple-800'
      case 'internal': return 'bg-gray-100 text-gray-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getMeetingStatusColor = (status: string) => {
    switch (status) {
      case 'scheduled': return 'bg-blue-100 text-blue-800'
      case 'completed': return 'bg-green-100 text-green-800'
      case 'cancelled': return 'bg-red-100 text-red-800'
      case 'in_progress': return 'bg-yellow-100 text-yellow-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  if (commsLoading || contactsLoading || meetingsLoading) {
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
          <h1 className="text-3xl font-bold text-gray-900">💬 Communication Hub (CAH)</h1>
          <p className="text-gray-600">AI-powered stakeholder engagement and communication management</p>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={() => setShowComposeModal(true)}
            className="btn-primary"
          >
            Compose Message
          </button>
          <button
            onClick={() => setShowScheduleMeetingModal(true)}
            className="btn-secondary"
          >
            Schedule Meeting
          </button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="card p-6">
          <div className="flex items-center">
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-600">Total Communications</p>
              <p className="text-2xl font-bold text-gray-900">{communications?.length || 0}</p>
            </div>
            <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
              💬
            </div>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center">
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-600">Active Contacts</p>
              <p className="text-2xl font-bold text-green-600">
                {contacts?.filter(c => c.status === 'active').length || 0}
              </p>
            </div>
            <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
              👥
            </div>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center">
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-600">Response Rate</p>
              <p className="text-2xl font-bold text-purple-600">
                {communicationStats?.engagement_metrics?.response_rate?.toFixed(1) || 0}%
              </p>
            </div>
            <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center">
              📈
            </div>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center">
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-600">Upcoming Meetings</p>
              <p className="text-2xl font-bold text-orange-600">
                {meetings?.filter(m => m.status === 'scheduled' && new Date(m.scheduled_date) > new Date()).length || 0}
              </p>
            </div>
            <div className="w-8 h-8 bg-orange-100 rounded-full flex items-center justify-center">
              📅
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setSelectedTab('communications')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              selectedTab === 'communications'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Communications ({communications?.length || 0})
          </button>
          <button
            onClick={() => setSelectedTab('contacts')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              selectedTab === 'contacts'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Contacts ({contacts?.length || 0})
          </button>
          <button
            onClick={() => setSelectedTab('meetings')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              selectedTab === 'meetings'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Meetings ({meetings?.length || 0})
          </button>
          <button
            onClick={() => setSelectedTab('templates')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              selectedTab === 'templates'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Templates ({templates?.length || 0})
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      {selectedTab === 'communications' && (
        <div className="space-y-4">
          {communications?.map(comm => (
            <div key={comm.id} className="card p-6">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    <h3 className="text-lg font-medium text-gray-900">{comm.subject}</h3>
                    <span className={`inline-flex px-2 py-1 text-xs rounded-full ${getCommunicationTypeColor(comm.communication_type)}`}>
                      {comm.communication_type}
                    </span>
                    <span className={`inline-flex px-2 py-1 text-xs rounded-full ${
                      comm.status === 'sent' ? 'bg-green-100 text-green-800' :
                      comm.status === 'delivered' ? 'bg-blue-100 text-blue-800' :
                      comm.status === 'read' ? 'bg-purple-100 text-purple-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {comm.status}
                    </span>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm mb-3">
                    <div>
                      <span className="text-gray-600">To:</span>
                      <span className="ml-1 font-medium">
                        {contacts?.find(c => c.id === comm.contact_id)?.full_name || 'Unknown'}
                      </span>
                    </div>
                    <div>
                      <span className="text-gray-600">Direction:</span>
                      <span className="ml-1 font-medium capitalize">{comm.direction}</span>
                    </div>
                    <div>
                      <span className="text-gray-600">Date:</span>
                      <span className="ml-1 font-medium">{format(new Date(comm.communication_date), 'MMM d, yyyy h:mm a')}</span>
                    </div>
                  </div>
                  
                  {comm.content && (
                    <div className="text-sm text-gray-700 mb-3 line-clamp-2">
                      {comm.content.substring(0, 200)}...
                    </div>
                  )}
                  
                  {comm.ai_generated && (
                    <div className="inline-flex items-center text-xs text-blue-600 mb-2">
                      <span className="mr-1">🤖</span>
                      AI Generated Content
                    </div>
                  )}
                </div>
                
                <div className="ml-4 text-right">
                  <div className="space-y-2">
                    <button className="btn-outline text-xs block w-full">
                      View Details
                    </button>
                    {comm.direction === 'inbound' && comm.status === 'received' && (
                      <button className="btn-secondary text-xs block w-full">
                        Reply
                      </button>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
          
          {(!communications || communications.length === 0) && (
            <div className="text-center py-12">
              <div className="text-6xl mb-4">💬</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Communications Yet</h3>
              <p className="text-gray-600 mb-4">Start engaging with stakeholders</p>
              <button
                onClick={() => setShowComposeModal(true)}
                className="btn-primary"
              >
                Compose Message
              </button>
            </div>
          )}
        </div>
      )}

      {selectedTab === 'contacts' && (
        <div className="space-y-6">
          <div className="flex justify-end">
            <button
              onClick={() => setShowCreateContactModal(true)}
              className="btn-secondary"
            >
              Add Contact
            </button>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {contacts?.map(contact => (
              <div key={contact.id} className="card p-6 hover:shadow-lg transition-shadow">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-900">{contact.full_name}</h3>
                    <p className="text-sm text-gray-600">{contact.title} • {contact.organization}</p>
                  </div>
                  <span className={`inline-flex px-2 py-1 text-xs rounded-full ${getContactTypeColor(contact.contact_type)}`}>
                    {contact.contact_type}
                  </span>
                </div>
                
                <div className="space-y-2 text-sm">
                  <div className="flex items-center">
                    <span className="text-gray-600 w-16">Email:</span>
                    <span className="font-medium">{contact.email}</span>
                  </div>
                  {contact.phone && (
                    <div className="flex items-center">
                      <span className="text-gray-600 w-16">Phone:</span>
                      <span className="font-medium">{contact.phone}</span>
                    </div>
                  )}
                  <div className="flex items-center">
                    <span className="text-gray-600 w-16">Status:</span>
                    <span className={`font-medium ${
                      contact.status === 'active' ? 'text-green-600' : 'text-gray-600'
                    }`}>
                      {contact.status}
                    </span>
                  </div>
                </div>
                
                {contact.last_interaction_date && (
                  <div className="mt-3 pt-3 border-t text-xs text-gray-500">
                    Last interaction: {format(new Date(contact.last_interaction_date), 'MMM d, yyyy')}
                  </div>
                )}
                
                <div className="mt-4 flex space-x-2">
                  <button
                    onClick={() => setSelectedContact(contact)}
                    className="btn-secondary text-xs flex-1"
                  >
                    Send Message
                  </button>
                  <button className="btn-outline text-xs flex-1">
                    View History
                  </button>
                </div>
              </div>
            ))}
            
            {(!contacts || contacts.length === 0) && (
              <div className="col-span-full text-center py-12">
                <div className="text-6xl mb-4">👥</div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">No Contacts Yet</h3>
                <p className="text-gray-600 mb-4">Add contacts to start building relationships</p>
                <button
                  onClick={() => setShowCreateContactModal(true)}
                  className="btn-primary"
                >
                  Add Contact
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {selectedTab === 'meetings' && (
        <div className="space-y-4">
          {meetings?.map(meeting => (
            <div key={meeting.id} className="card p-6">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    <h3 className="text-lg font-medium text-gray-900">{meeting.title}</h3>
                    <span className={`inline-flex px-2 py-1 text-xs rounded-full ${getMeetingStatusColor(meeting.status)}`}>
                      {meeting.status}
                    </span>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm mb-3">
                    <div>
                      <span className="text-gray-600">Date:</span>
                      <span className="ml-1 font-medium">{format(new Date(meeting.scheduled_date), 'MMM d, yyyy h:mm a')}</span>
                    </div>
                    <div>
                      <span className="text-gray-600">Duration:</span>
                      <span className="ml-1 font-medium">{meeting.duration_minutes} minutes</span>
                    </div>
                    <div>
                      <span className="text-gray-600">Participants:</span>
                      <span className="ml-1 font-medium">{meeting.participants?.length || 0}</span>
                    </div>
                  </div>
                  
                  {meeting.agenda && (
                    <div className="text-sm text-gray-700 mb-3">
                      <span className="font-medium text-gray-600">Agenda:</span> {meeting.agenda}
                    </div>
                  )}
                  
                  {meeting.meeting_notes && meeting.status === 'completed' && (
                    <div className="mt-3 p-3 bg-gray-50 rounded-lg">
                      <p className="text-sm font-medium text-gray-900 mb-1">Meeting Notes:</p>
                      <p className="text-sm text-gray-700 line-clamp-3">{meeting.meeting_notes}</p>
                    </div>
                  )}
                </div>
                
                <div className="ml-4 text-right">
                  <div className="space-y-2">
                    <button className="btn-outline text-xs block w-full">
                      View Details
                    </button>
                    {meeting.status === 'scheduled' && new Date(meeting.scheduled_date) > new Date() && (
                      <button className="btn-secondary text-xs block w-full">
                        Join Meeting
                      </button>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
          
          {(!meetings || meetings.length === 0) && (
            <div className="text-center py-12">
              <div className="text-6xl mb-4">📅</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Meetings Scheduled</h3>
              <p className="text-gray-600 mb-4">Schedule meetings with stakeholders</p>
              <button
                onClick={() => setShowScheduleMeetingModal(true)}
                className="btn-primary"
              >
                Schedule Meeting
              </button>
            </div>
          )}
        </div>
      )}

      {selectedTab === 'templates' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {templates?.map(template => (
            <div key={template.id} className="card p-6">
              <div className="flex items-start justify-between mb-3">
                <h3 className="text-lg font-medium text-gray-900">{template.template_name}</h3>
                <span className={`inline-flex px-2 py-1 text-xs rounded-full ${
                  template.template_type === 'email' ? 'bg-blue-100 text-blue-800' :
                  template.template_type === 'proposal' ? 'bg-green-100 text-green-800' :
                  'bg-gray-100 text-gray-800'
                }`}>
                  {template.template_type}
                </span>
              </div>
              
              {template.description && (
                <p className="text-sm text-gray-600 mb-3">{template.description}</p>
              )}
              
              <div className="text-xs text-gray-500 mb-4">
                Used {template.usage_count || 0} times
              </div>
              
              <div className="flex space-x-2">
                <button className="btn-primary text-xs flex-1">
                  Use Template
                </button>
                <button className="btn-outline text-xs flex-1">
                  Edit
                </button>
              </div>
            </div>
          ))}
          
          {(!templates || templates.length === 0) && (
            <div className="col-span-full text-center py-12">
              <div className="text-6xl mb-4">📝</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No Templates Yet</h3>
              <p className="text-gray-600 mb-4">Create reusable communication templates</p>
              <button className="btn-primary">
                Create Template
              </button>
            </div>
          )}
        </div>
      )}

      {/* Compose Message Modal */}
      {showComposeModal && (
        <ComposeMessageModal
          contacts={contacts || []}
          templates={templates || []}
          onClose={() => setShowComposeModal(false)}
          onSubmit={handleSendCommunication}
          isLoading={sendCommunicationMutation.isLoading}
          selectedContact={selectedContact}
        />
      )}

      {/* Create Contact Modal */}
      {showCreateContactModal && (
        <CreateContactModal
          onClose={() => setShowCreateContactModal(false)}
          onSubmit={handleCreateContact}
          isLoading={createContactMutation.isLoading}
        />
      )}

      {/* Schedule Meeting Modal */}
      {showScheduleMeetingModal && (
        <ScheduleMeetingModal
          onClose={() => setShowScheduleMeetingModal(false)}
          onSubmit={handleScheduleMeeting}
          isLoading={scheduleMeetingMutation.isLoading}
        />
      )}
    </div>
  )
}

// Compose Message Modal Component
const ComposeMessageModal = ({ contacts, templates, onClose, onSubmit, isLoading, selectedContact }: any) => {
  const [formData, setFormData] = useState({
    contact_id: selectedContact?.id || '',
    subject: '',
    content: '',
    communication_type: 'email',
    template_id: ''
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit({
      ...formData,
      contact_id: Number(formData.contact_id),
      template_id: formData.template_id ? Number(formData.template_id) : undefined
    })
  }

  const handleTemplateSelect = (templateId: string) => {
    const template = templates.find((t: any) => t.id === Number(templateId))
    if (template) {
      setFormData({
        ...formData,
        template_id: templateId,
        subject: template.subject || formData.subject,
        content: template.content || formData.content
      })
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Compose Message</h2>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Contact *
              </label>
              <select
                value={formData.contact_id}
                onChange={(e) => setFormData({ ...formData, contact_id: e.target.value })}
                className="w-full border border-gray-300 rounded-md px-3 py-2"
                required
              >
                <option value="">Select contact</option>
                {contacts.map((contact: any) => (
                  <option key={contact.id} value={contact.id}>
                    {contact.full_name} - {contact.organization}
                  </option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Type *
              </label>
              <select
                value={formData.communication_type}
                onChange={(e) => setFormData({ ...formData, communication_type: e.target.value })}
                className="w-full border border-gray-300 rounded-md px-3 py-2"
                required
              >
                <option value="email">Email</option>
                <option value="phone">Phone Call</option>
                <option value="meeting">Meeting Request</option>
                <option value="document">Document</option>
              </select>
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Template (Optional)
            </label>
            <select
              value={formData.template_id}
              onChange={(e) => handleTemplateSelect(e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2"
            >
              <option value="">No template</option>
              {templates.map((template: any) => (
                <option key={template.id} value={template.id}>
                  {template.template_name}
                </option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Subject *
            </label>
            <input
              type="text"
              value={formData.subject}
              onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
              className="w-full border border-gray-300 rounded-md px-3 py-2"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Content *
            </label>
            <textarea
              value={formData.content}
              onChange={(e) => setFormData({ ...formData, content: e.target.value })}
              className="w-full border border-gray-300 rounded-md px-3 py-2 h-32"
              placeholder="Enter your message..."
              required
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
              type="button"
              className="btn-secondary"
              disabled={isLoading}
            >
              Generate with AI
            </button>
            <button
              type="submit"
              className="flex-1 btn-primary"
              disabled={isLoading}
            >
              {isLoading ? 'Sending...' : 'Send Message'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// Create Contact Modal Component
const CreateContactModal = ({ onClose, onSubmit, isLoading }: any) => {
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    phone: '',
    title: '',
    organization: '',
    contact_type: 'government',
    department: '',
    address: ''
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit(formData)
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Add Contact</h2>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Full Name *
            </label>
            <input
              type="text"
              value={formData.full_name}
              onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
              className="w-full border border-gray-300 rounded-md px-3 py-2"
              required
            />
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Email *
              </label>
              <input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="w-full border border-gray-300 rounded-md px-3 py-2"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Phone
              </label>
              <input
                type="tel"
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                className="w-full border border-gray-300 rounded-md px-3 py-2"
              />
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Title
              </label>
              <input
                type="text"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                className="w-full border border-gray-300 rounded-md px-3 py-2"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Contact Type *
              </label>
              <select
                value={formData.contact_type}
                onChange={(e) => setFormData({ ...formData, contact_type: e.target.value })}
                className="w-full border border-gray-300 rounded-md px-3 py-2"
                required
              >
                <option value="government">Government</option>
                <option value="vendor">Vendor</option>
                <option value="partner">Partner</option>
                <option value="internal">Internal</option>
              </select>
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Organization *
            </label>
            <input
              type="text"
              value={formData.organization}
              onChange={(e) => setFormData({ ...formData, organization: e.target.value })}
              className="w-full border border-gray-300 rounded-md px-3 py-2"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Department
            </label>
            <input
              type="text"
              value={formData.department}
              onChange={(e) => setFormData({ ...formData, department: e.target.value })}
              className="w-full border border-gray-300 rounded-md px-3 py-2"
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
              {isLoading ? 'Adding...' : 'Add Contact'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

// Schedule Meeting Modal Component
const ScheduleMeetingModal = ({ onClose, onSubmit, isLoading }: any) => {
  const [formData, setFormData] = useState({
    title: '',
    scheduled_date: '',
    duration_minutes: 60,
    meeting_type: 'call',
    agenda: '',
    participants: [] as number[],
    location: ''
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSubmit(formData)
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-lg max-h-[90vh] overflow-y-auto">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Schedule Meeting</h2>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Meeting Title *
            </label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              className="w-full border border-gray-300 rounded-md px-3 py-2"
              required
            />
          </div>
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Date & Time *
              </label>
              <input
                type="datetime-local"
                value={formData.scheduled_date}
                onChange={(e) => setFormData({ ...formData, scheduled_date: e.target.value })}
                className="w-full border border-gray-300 rounded-md px-3 py-2"
                required
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Duration (minutes) *
              </label>
              <input
                type="number"
                value={formData.duration_minutes}
                onChange={(e) => setFormData({ ...formData, duration_minutes: Number(e.target.value) })}
                className="w-full border border-gray-300 rounded-md px-3 py-2"
                required
              />
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Meeting Type *
            </label>
            <select
              value={formData.meeting_type}
              onChange={(e) => setFormData({ ...formData, meeting_type: e.target.value })}
              className="w-full border border-gray-300 rounded-md px-3 py-2"
              required
            >
              <option value="call">Phone Call</option>
              <option value="video">Video Conference</option>
              <option value="in_person">In Person</option>
              <option value="webinar">Webinar</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Location/Link
            </label>
            <input
              type="text"
              value={formData.location}
              onChange={(e) => setFormData({ ...formData, location: e.target.value })}
              className="w-full border border-gray-300 rounded-md px-3 py-2"
              placeholder="Meeting room, Zoom link, etc."
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Agenda
            </label>
            <textarea
              value={formData.agenda}
              onChange={(e) => setFormData({ ...formData, agenda: e.target.value })}
              className="w-full border border-gray-300 rounded-md px-3 py-2 h-24"
              placeholder="Meeting agenda and topics..."
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
              {isLoading ? 'Scheduling...' : 'Schedule Meeting'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default CommunicationHub