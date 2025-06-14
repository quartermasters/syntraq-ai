/*
© 2025 Aliff Capital, Quartermasters FZC, and SkillvenzA. All rights reserved.

Syntraq AI - Frontend Application Router
A Joint Innovation by Aliff Capital, Quartermasters FZC, and SkillvenzA
*/

import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './hooks/useAuth'
import Layout from './components/Layout'
import Login from './pages/Login'
import Register from './pages/Register'
import EnhancedDashboard from './pages/EnhancedDashboard'
import Opportunities from './pages/Opportunities'
import OpportunityDetail from './pages/OpportunityDetail'
import Profile from './pages/Profile'
import ARTSDashboard from './components/arts/ARTSDashboard'
import FinancialDashboard from './components/fvms/FinancialDashboard'
import ProposalDashboard from './components/pme/ProposalDashboard'
import CommunicationHub from './components/cah/CommunicationHub'

function App() {
  const { user, loading } = useAuth()
  
  console.log('App render - loading:', loading, 'user:', user)

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <Routes>
      {!user ? (
        // Unauthenticated routes
        <>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="*" element={<Navigate to="/login" replace />} />
        </>
      ) : (
        // Authenticated routes
        <>
          <Route path="/dashboard" element={<Layout><EnhancedDashboard /></Layout>} />
          <Route path="/opportunities" element={<Layout><Opportunities /></Layout>} />
          <Route path="/opportunities/:id" element={<Layout><OpportunityDetail /></Layout>} />
          <Route path="/arts" element={<Layout><ARTSDashboard /></Layout>} />
          <Route path="/financial" element={<Layout><FinancialDashboard /></Layout>} />
          <Route path="/proposals" element={<Layout><ProposalDashboard /></Layout>} />
          <Route path="/communications" element={<Layout><CommunicationHub /></Layout>} />
          <Route path="/profile" element={<Layout><Profile /></Layout>} />
          <Route path="/login" element={<Navigate to="/dashboard" replace />} />
          <Route path="/register" element={<Navigate to="/dashboard" replace />} />
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </>
      )}
    </Routes>
  )
}

export default App