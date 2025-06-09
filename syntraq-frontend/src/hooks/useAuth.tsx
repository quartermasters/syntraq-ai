import { useState, useEffect, createContext, useContext } from 'react'
import { authAPI } from '../services/api'
import toast from 'react-hot-toast'

interface User {
  id: number
  email: string
  username: string
  full_name: string
  company_name: string
  role: string
  is_active: boolean
  created_at: string
}

interface AuthContextType {
  user: User | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (userData: any) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextType | null>(null)

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    console.log('AuthProvider useEffect running')
    const token = localStorage.getItem('auth_token')
    console.log('Token from localStorage:', token)
    if (token) {
      console.log('Token found, calling checkAuth')
      checkAuth()
    } else {
      console.log('No token found, setting loading to false')
      setLoading(false)
    }
  }, [])

  const checkAuth = async () => {
    try {
      console.log('Checking auth with token:', localStorage.getItem('auth_token'))
      const userData = await authAPI.getCurrentUser()
      console.log('checkAuth success, user data:', userData)
      setUser(userData)
    } catch (error) {
      console.error('checkAuth failed:', error)
      localStorage.removeItem('auth_token')
      setUser(null)
    } finally {
      setLoading(false)
    }
  }

  const login = async (email: string, password: string) => {
    try {
      // Demo mode - create mock user for testing
      const mockUser = {
        id: 1,
        email: email,
        username: email.split('@')[0],
        full_name: 'Demo User',
        company_name: 'Syntraq Demo Company',
        role: 'admin',
        is_active: true,
        created_at: new Date().toISOString()
      }
      
      localStorage.setItem('auth_token', 'demo-token-12345')
      setUser(mockUser)
      toast.success('Welcome to Syntraq AI Demo!')
    } catch (error: any) {
      toast.error('Demo login failed')
      throw error
    }
  }

  const register = async (userData: any) => {
    try {
      // Demo mode - create mock user for testing
      const mockUser = {
        id: 1,
        email: userData.email,
        username: userData.username,
        full_name: userData.full_name,
        company_name: userData.company_name,
        role: 'admin',
        is_active: true,
        created_at: new Date().toISOString()
      }
      
      localStorage.setItem('auth_token', 'demo-token-12345')
      setUser(mockUser)
      toast.success('Demo account created successfully!')
    } catch (error: any) {
      toast.error('Demo registration failed')
      throw error
    }
  }

  const logout = () => {
    localStorage.removeItem('auth_token')
    setUser(null)
    toast.success('Logged out successfully')
  }

  const authValue = {
    user,
    loading,
    login,
    register,
    logout
  }

  return (
    <AuthContext.Provider value={authValue}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}