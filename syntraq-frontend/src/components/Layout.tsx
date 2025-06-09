/*
© 2025 Aliff Capital, Quartermasters FZC, and SkillvenzA. All rights reserved.

Syntraq AI - Main Layout Component
A Joint Innovation by Aliff Capital, Quartermasters FZC, and SkillvenzA
*/

import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

interface LayoutProps {
  children: React.ReactNode
}

const Layout = ({ children }: LayoutProps) => {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const { user, logout } = useAuth()
  const location = useLocation()

  const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: '📊' },
    { name: 'Opportunities', href: '/opportunities', icon: '🎯' },
    { name: 'AI Team (ARTS)', href: '/arts', icon: '🤖' },
    { name: 'Financial (FVMS)', href: '/financial', icon: '💰' },
    { name: 'Proposals (PME)', href: '/proposals', icon: '📄' },
    { name: 'Communications (CAH)', href: '/communications', icon: '💬' },
    { name: 'Profile', href: '/profile', icon: '👤' },
  ]

  const isActive = (href: string) => location.pathname === href

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <div className={`
        fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-lg transform transition-transform duration-300 ease-in-out
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
        lg:translate-x-0 lg:static lg:inset-0
      `}>
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center justify-center h-16 px-4 bg-blue-600">
            <h1 className="text-white font-bold text-xl">Syntraq AI</h1>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-4 space-y-2">
            {navigation.map((item) => (
              <Link
                key={item.name}
                to={item.href}
                className={`
                  flex items-center px-4 py-2 text-sm font-medium rounded-lg transition-colors
                  ${isActive(item.href)
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                  }
                `}
                onClick={() => setSidebarOpen(false)}
              >
                <span className="mr-3 text-lg">{item.icon}</span>
                {item.name}
              </Link>
            ))}
          </nav>

          {/* User Info */}
          <div className="p-4 border-t border-gray-200">
            <div className="flex items-center">
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-900">{user?.full_name}</p>
                <p className="text-xs text-gray-500">{user?.company_name}</p>
              </div>
              <button
                onClick={logout}
                className="ml-3 text-gray-400 hover:text-gray-600"
                title="Logout"
              >
                🚪
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Overlay for mobile */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 z-40 bg-gray-600 bg-opacity-75 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Main content */}
      <div className="flex-1 lg:pl-0">
        {/* Top bar */}
        <div className="lg:hidden">
          <div className="flex items-center justify-between h-16 px-4 bg-white shadow">
            <button
              onClick={() => setSidebarOpen(true)}
              className="text-gray-500 hover:text-gray-600"
            >
              ☰
            </button>
            <h1 className="text-lg font-semibold text-gray-900">Syntraq AI</h1>
            <div></div>
          </div>
        </div>

        {/* Page content */}
        <main className="flex-1 p-6">
          {children}
        </main>
        
        {/* Footer */}
        <footer className="bg-gray-50 border-t border-gray-200 py-4 px-6">
          <div className="text-center">
            <p className="text-sm text-gray-600">
              © 2025 Syntraq AI - A Joint Innovation by{' '}
              <a href="https://www.aliffcapital.com" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:text-blue-800">
                Aliff Capital
              </a>
              ,{' '}
              <a href="https://www.quartermasters.me" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:text-blue-800">
                Quartermasters FZC
              </a>
              , and{' '}
              <a href="https://www.skillvenza.com" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:text-blue-800">
                SkillvenzA
              </a>
            </p>
            <p className="text-xs text-gray-500 mt-1">All Rights Reserved.</p>
          </div>
        </footer>
      </div>
    </div>
  )
}

export default Layout