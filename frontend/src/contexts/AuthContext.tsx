'use client'

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { authAPI, waitlistAPI, User, TrialStatusResponse } from '@/lib/api'
import { useRouter } from 'next/navigation'

interface AuthContextType {
  user: User | null
  loading: boolean
  trialStatus: TrialStatusResponse | null
  inWaitlist: boolean
  login: (email: string, password: string) => Promise<void>
  signup: (data: {
    email: string
    username: string
    password: string
    full_name?: string
    phone?: string
  }) => Promise<void>
  logout: () => void
  refreshUser: () => Promise<void>
  refreshTrialStatus: () => Promise<void>
  checkWaitlistStatus: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [trialStatus, setTrialStatus] = useState<TrialStatusResponse | null>(null)
  const [inWaitlist, setInWaitlist] = useState(false)
  const router = useRouter()

  // Load user from localStorage on mount
  useEffect(() => {
    const loadUser = async () => {
      const token = localStorage.getItem('token')
      if (token) {
        try {
          const userData = await authAPI.getCurrentUser()
          setUser(userData)
          // Load trial status if user is authenticated
          await refreshTrialStatus()
          await checkWaitlistStatus()
        } catch (error) {
          console.error('Failed to load user:', error)
          localStorage.removeItem('token')
          localStorage.removeItem('user')
        }
      }
      setLoading(false)
    }

    loadUser()
  }, [])

  const refreshTrialStatus = async () => {
    try {
      const status = await authAPI.getTrialStatus()
      setTrialStatus(status)
    } catch (error) {
      console.error('Failed to load trial status:', error)
    }
  }

  const checkWaitlistStatus = async () => {
    try {
      const status = await waitlistAPI.getStatus()
      setInWaitlist(status.in_waitlist)
    } catch (error) {
      console.error('Failed to check waitlist:', error)
    }
  }

  const login = async (email: string, password: string) => {
    try {
      const response = await authAPI.login(email, password)
      localStorage.setItem('token', response.access_token)
      localStorage.setItem('user', JSON.stringify(response.user))
      setUser(response.user)
      await refreshTrialStatus()
      await checkWaitlistStatus()
      router.push('/designer')
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Login failed')
    }
  }

  const signup = async (data: {
    email: string
    username: string
    password: string
    full_name?: string
    phone?: string
  }) => {
    try {
      const response = await authAPI.signup(data)
      localStorage.setItem('token', response.access_token)
      localStorage.setItem('user', JSON.stringify(response.user))
      setUser(response.user)
      await refreshTrialStatus()
      router.push('/designer')
    } catch (error: any) {
      throw new Error(error.response?.data?.detail || 'Signup failed')
    }
  }

  const logout = () => {
    authAPI.logout()
    setUser(null)
    setTrialStatus(null)
    setInWaitlist(false)
    router.push('/login')
  }

  const refreshUser = async () => {
    try {
      const userData = await authAPI.getCurrentUser()
      setUser(userData)
      await refreshTrialStatus()
      await checkWaitlistStatus()
    } catch (error) {
      console.error('Failed to refresh user:', error)
    }
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        trialStatus,
        inWaitlist,
        login,
        signup,
        logout,
        refreshUser,
        refreshTrialStatus,
        checkWaitlistStatus,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
