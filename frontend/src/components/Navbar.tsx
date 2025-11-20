'use client'

import { useAuth } from '@/contexts/AuthContext'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { Gem, LogOut, User, Menu, X, Sparkles, Eye, Shield, TrendingUp } from 'lucide-react'
import { useState } from 'react'

export default function Navbar() {
  const { user, logout } = useAuth()
  const pathname = usePathname()
  const router = useRouter()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  // Don't show navbar on auth pages
  const authPages = ['/login', '/signup', '/verify-email']
  if (authPages.some(page => pathname.startsWith(page))) {
    return null
  }

  const handleLogout = async () => {
    await logout()
    router.push('/login')
  }

  const navLinks = [
    { href: '/designer', label: 'AI Designer', icon: Sparkles },
    { href: '/tryon', label: 'Try-On', icon: Eye },
    { href: '/qc', label: 'QC Inspector', icon: Shield },
    { href: '/analytics', label: 'Analytics', icon: TrendingUp },
  ]

  return (
    <header className="border-b bg-white shadow-sm sticky top-0 z-50">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between py-3">
          {/* Logo */}
          <Link href="/" className="flex items-center space-x-3 group">
            <div className="relative bg-primary-600 w-10 h-10 rounded-lg rotate-45 flex items-center justify-center shadow-md shadow-primary-400/40">
              <Gem className="h-5 w-5 text-white -rotate-45" />
            </div>
            <h1 className="text-2xl font-bold text-gray-900">JewelTech</h1>
          </Link>

          {/* Desktop Navigation */}
          {user && (
            <nav className="hidden md:flex items-center gap-2 rounded-full border border-gray-200 bg-white px-3 py-1.5 text-sm shadow-sm">
              {navLinks.map((link) => {
                const Icon = link.icon
                const isActive = pathname.startsWith(link.href)
                return (
                  <Link
                    key={link.href}
                    href={link.href}
                    className={`px-3 py-1.5 rounded-full flex items-center gap-1.5 transition-colors ${
                      isActive
                        ? 'bg-primary-600 text-white'
                        : 'text-gray-600 hover:text-primary-600 hover:bg-gray-50'
                    }`}
                  >
                    <Icon className="h-4 w-4" />
                    {link.label}
                  </Link>
                )
              })}
            </nav>
          )}

          {/* User Info & Actions */}
          <div className="flex items-center gap-3">
            {user ? (
              <>
                {/* User Info - Desktop */}
                <div className="hidden md:flex items-center gap-3">
                  <div className="text-right">
                    <div className="text-sm font-medium text-gray-900 flex items-center gap-2">
                      {user.username}
                      {user.role === 'unlimited' && (
                        <span className="px-2 py-0.5 rounded-full bg-gradient-to-r from-amber-400 to-amber-600 text-white text-xs font-semibold">
                           Admin
                        </span>
                      )}
                    </div>
                    <div className="text-xs text-gray-500">{user.email}</div>
                  </div>
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary-500 to-purple-600 flex items-center justify-center text-white font-semibold shadow-md">
                    {user.username.charAt(0).toUpperCase()}
                  </div>
                </div>

                {/* Logout Button - Desktop */}
                <button
                  onClick={handleLogout}
                  className="hidden md:flex items-center gap-2 px-4 py-2 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50 transition-colors text-sm font-medium"
                >
                  <LogOut className="h-4 w-4" />
                  Logout
                </button>

                {/* Mobile Menu Button */}
                <button
                  onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                  className="md:hidden p-2 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  {mobileMenuOpen ? (
                    <X className="h-6 w-6 text-gray-900" />
                  ) : (
                    <Menu className="h-6 w-6 text-gray-900" />
                  )}
                </button>
              </>
            ) : (
              <div className="flex items-center gap-2">
                <Link
                  href="/login"
                  className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-primary-600 transition-colors"
                >
                  Sign In
                </Link>
                <Link
                  href="/signup"
                  className="px-4 py-2 rounded-lg bg-primary-600 text-white text-sm font-semibold hover:bg-primary-700 transition-colors"
                >
                  Get Started
                </Link>
              </div>
            )}
          </div>
        </div>

        {/* Mobile Menu */}
        {user && mobileMenuOpen && (
          <div className="md:hidden border-t border-gray-200 py-4 space-y-2">
            {/* User Info */}
            <div className="flex items-center gap-3 px-2 py-2">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary-500 to-purple-600 flex items-center justify-center text-white font-semibold">
                {user.username.charAt(0).toUpperCase()}
              </div>
              <div>
                <div className="text-sm font-medium text-gray-900 flex items-center gap-2">
                  {user.username}
                  {user.role === 'unlimited' && (
                    <span className="px-2 py-0.5 rounded-full bg-gradient-to-r from-amber-400 to-amber-600 text-white text-xs font-semibold">
                       Admin
                    </span>
                  )}
                </div>
                <div className="text-xs text-gray-500">{user.email}</div>
              </div>
            </div>

            {/* Navigation Links */}
            <div className="space-y-1">
              {navLinks.map((link) => {
                const Icon = link.icon
                const isActive = pathname.startsWith(link.href)
                return (
                  <Link
                    key={link.href}
                    href={link.href}
                    onClick={() => setMobileMenuOpen(false)}
                    className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                      isActive
                        ? 'bg-primary-600 text-white'
                        : 'text-gray-700 hover:bg-gray-100'
                    }`}
                  >
                    <Icon className="h-5 w-5" />
                    <span className="font-medium">{link.label}</span>
                  </Link>
                )
              })}
            </div>

            {/* Logout Button */}
            <button
              onClick={handleLogout}
              className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-red-600 hover:bg-red-50 transition-colors font-medium"
            >
              <LogOut className="h-5 w-5" />
              Logout
            </button>
          </div>
        )}
      </div>
    </header>
  )
}
