import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { login as apiLogin, register as apiRegister } from '../services/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser]       = useState(null)
  const [loading, setLoading] = useState(true)
  const navigate              = useNavigate()

  // Rehydrate from localStorage
  useEffect(() => {
    const token = localStorage.getItem('nexus_jwt')
    const saved  = localStorage.getItem('nexus_user')
    if (token && saved) {
      try {
        setUser(JSON.parse(saved))
      } catch {
        localStorage.removeItem('nexus_jwt')
        localStorage.removeItem('nexus_user')
      }
    }
    setLoading(false)
  }, [])

  const login = useCallback(async (email, password) => {
    try {
      const { user: userData } = await apiLogin(email, password)
      setUser(userData)
      toast.success(`Welcome back, ${userData.name?.split(' ')[0] || 'Trader'}! 🚀`)
      navigate('/dashboard')
    } catch (error) {
      toast.error(error.message || 'Login failed')
      throw error
    }
  }, [navigate])

  const register = useCallback(async (name, email, password) => {
    try {
      const { user: userData } = await apiRegister(name, email, password)
      setUser(userData)
      toast.success(`Account created! Welcome, ${userData.name?.split(' ')[0]}! 🚀`)
      navigate('/dashboard')
    } catch (error) {
      toast.error(error.message || 'Registration failed')
      throw error
    }
  }, [navigate])

  const logout = useCallback(() => {
    localStorage.removeItem('nexus_jwt')
    localStorage.removeItem('nexus_user')
    setUser(null)
    toast.success('Logged out successfully.')
    navigate('/login')
  }, [navigate])

  const updateUser = useCallback((updates) => {
    setUser(prev => {
      const updated = { ...prev, ...updates }
      localStorage.setItem('nexus_user', JSON.stringify(updated))
      return updated
    })
  }, [])

  return (
    <AuthContext.Provider value={{
      user,
      loading,
      login,
      register,
      logout,
      updateUser,
      isAdmin: user?.role === 'admin',
    }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
