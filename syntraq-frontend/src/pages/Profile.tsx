import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { authAPI } from '../services/api'
import toast from 'react-hot-toast'

const Profile = () => {
  const [activeTab, setActiveTab] = useState('profile')
  const [companySetup, setCompanySetup] = useState({
    naics_codes: [] as string[],
    certifications: [] as string[],
    capabilities: [] as string[],
    contract_size_preference: ''
  })
  
  const queryClient = useQueryClient()

  const { data: user, error: userError } = useQuery('current-user', authAPI.getCurrentUser, {
    retry: false,
    onError: (error) => {
      console.error('Profile API error:', error)
      // Don't auto-redirect on error, let user stay on profile page
    }
  })
  const { data: _companyProfile } = useQuery('company-profile', () => 
    authAPI.getCurrentUser().then(user => user.company_profile || {}), {
    enabled: false, // Disable this query for now
    retry: false
  })

  const setupMutation = useMutation(authAPI.setupCompany, {
    onSuccess: () => {
      toast.success('Company profile updated')
      queryClient.invalidateQueries('company-profile')
    },
    onError: () => {
      toast.error('Failed to update profile')
    }
  })

  const handleSetupSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setupMutation.mutate(companySetup)
  }

  const addItem = (field: 'naics_codes' | 'certifications' | 'capabilities', value: string) => {
    if (value.trim()) {
      setCompanySetup(prev => ({
        ...prev,
        [field]: [...prev[field], value.trim()]
      }))
    }
  }

  const removeItem = (field: 'naics_codes' | 'certifications' | 'capabilities', index: number) => {
    setCompanySetup(prev => ({
      ...prev,
      [field]: prev[field].filter((_, i) => i !== index)
    }))
  }

  const tabs = [
    { id: 'profile', name: 'Profile', icon: '👤' },
    { id: 'company', name: 'Company Setup', icon: '🏢' },
    { id: 'preferences', name: 'Preferences', icon: '⚙️' },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Profile Settings</h1>
        <p className="text-gray-600">Manage your account and company information</p>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`
                flex items-center py-2 px-1 border-b-2 font-medium text-sm
                ${activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }
              `}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.name}
            </button>
          ))}
        </nav>
      </div>

      {/* Profile Tab */}
      {activeTab === 'profile' && (
        <div className="card p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Profile Information</h3>
          <dl className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <dt className="text-sm font-medium text-gray-500">Full Name</dt>
              <dd className="text-sm text-gray-900 mt-1">{user?.full_name}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Email</dt>
              <dd className="text-sm text-gray-900 mt-1">{user?.email}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Username</dt>
              <dd className="text-sm text-gray-900 mt-1">{user?.username}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Company</dt>
              <dd className="text-sm text-gray-900 mt-1">{user?.company_name}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Role</dt>
              <dd className="text-sm text-gray-900 mt-1 capitalize">{user?.role}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500">Member Since</dt>
              <dd className="text-sm text-gray-900 mt-1">
                {user?.created_at && new Date(user.created_at).toLocaleDateString()}
              </dd>
            </div>
          </dl>
        </div>
      )}

      {/* Company Setup Tab */}
      {activeTab === 'company' && (
        <div className="card p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Company Profile Setup</h3>
          <p className="text-gray-600 mb-6">
            This information helps our AI provide more accurate opportunity recommendations.
          </p>

          <form onSubmit={handleSetupSubmit} className="space-y-6">
            {/* NAICS Codes */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                NAICS Codes
              </label>
              <div className="flex space-x-2 mb-2">
                <input
                  type="text"
                  placeholder="Enter NAICS code (e.g., 541511)"
                  className="input-field flex-1"
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault()
                      addItem('naics_codes', e.currentTarget.value)
                      e.currentTarget.value = ''
                    }
                  }}
                />
                <button
                  type="button"
                  onClick={(e) => {
                    const input = e.currentTarget.previousElementSibling as HTMLInputElement
                    addItem('naics_codes', input.value)
                    input.value = ''
                  }}
                  className="btn-secondary"
                >
                  Add
                </button>
              </div>
              <div className="flex flex-wrap gap-2">
                {companySetup.naics_codes.map((code, index) => (
                  <span
                    key={index}
                    className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                  >
                    {code}
                    <button
                      type="button"
                      onClick={() => removeItem('naics_codes', index)}
                      className="ml-2 text-blue-600 hover:text-blue-500"
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
            </div>

            {/* Certifications */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Certifications
              </label>
              <div className="flex space-x-2 mb-2">
                <select
                  className="input-field flex-1"
                  onChange={(e) => {
                    if (e.target.value) {
                      addItem('certifications', e.target.value)
                      e.target.value = ''
                    }
                  }}
                >
                  <option value="">Select certification</option>
                  <option value="8(a)">8(a)</option>
                  <option value="WOSB">WOSB</option>
                  <option value="HUBZone">HUBZone</option>
                  <option value="VOSB">VOSB</option>
                  <option value="SDVOSB">SDVOSB</option>
                  <option value="SBA">SBA</option>
                </select>
              </div>
              <div className="flex flex-wrap gap-2">
                {companySetup.certifications.map((cert, index) => (
                  <span
                    key={index}
                    className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800"
                  >
                    {cert}
                    <button
                      type="button"
                      onClick={() => removeItem('certifications', index)}
                      className="ml-2 text-green-600 hover:text-green-500"
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
            </div>

            {/* Capabilities */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Core Capabilities
              </label>
              <div className="flex space-x-2 mb-2">
                <input
                  type="text"
                  placeholder="Enter capability (e.g., Software Development)"
                  className="input-field flex-1"
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault()
                      addItem('capabilities', e.currentTarget.value)
                      e.currentTarget.value = ''
                    }
                  }}
                />
                <button
                  type="button"
                  onClick={(e) => {
                    const input = e.currentTarget.previousElementSibling as HTMLInputElement
                    addItem('capabilities', input.value)
                    input.value = ''
                  }}
                  className="btn-secondary"
                >
                  Add
                </button>
              </div>
              <div className="flex flex-wrap gap-2">
                {companySetup.capabilities.map((capability, index) => (
                  <span
                    key={index}
                    className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800"
                  >
                    {capability}
                    <button
                      type="button"
                      onClick={() => removeItem('capabilities', index)}
                      className="ml-2 text-purple-600 hover:text-purple-500"
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
            </div>

            {/* Contract Size Preference */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Preferred Contract Size Range
              </label>
              <select
                value={companySetup.contract_size_preference}
                onChange={(e) => setCompanySetup(prev => ({ ...prev, contract_size_preference: e.target.value }))}
                className="input-field"
              >
                <option value="">Select range</option>
                <option value="under-100k">Under $100K</option>
                <option value="100k-500k">$100K - $500K</option>
                <option value="500k-1m">$500K - $1M</option>
                <option value="1m-5m">$1M - $5M</option>
                <option value="5m-plus">$5M+</option>
                <option value="any">Any Size</option>
              </select>
            </div>

            <button
              type="submit"
              disabled={setupMutation.isLoading}
              className="btn-primary"
            >
              {setupMutation.isLoading ? 'Saving...' : 'Save Company Profile'}
            </button>
          </form>
        </div>
      )}

      {/* Preferences Tab */}
      {activeTab === 'preferences' && (
        <div className="card p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">AI Preferences</h3>
          <div className="space-y-4">
            <div>
              <label className="flex items-center">
                <input type="checkbox" className="rounded mr-2" defaultChecked />
                <span className="text-sm text-gray-700">
                  Enable automatic AI analysis for new opportunities
                </span>
              </label>
            </div>
            <div>
              <label className="flex items-center">
                <input type="checkbox" className="rounded mr-2" defaultChecked />
                <span className="text-sm text-gray-700">
                  Send email notifications for high-relevance opportunities (70%+)
                </span>
              </label>
            </div>
            <div>
              <label className="flex items-center">
                <input type="checkbox" className="rounded mr-2" />
                <span className="text-sm text-gray-700">
                  Include low-relevance opportunities in dashboard
                </span>
              </label>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Profile