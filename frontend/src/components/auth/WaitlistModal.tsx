'use client'

import { useState } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { waitlistAPI } from '@/lib/api'
import { X, Sparkles, Users, CheckCircle } from 'lucide-react'

interface WaitlistModalProps {
  isOpen: boolean
  onClose: () => void
  feature: string
}

export default function WaitlistModal({ isOpen, onClose, feature }: WaitlistModalProps) {
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)
  const [position, setPosition] = useState<number | null>(null)
  const [error, setError] = useState('')
  const { checkWaitlistStatus } = useAuth()

  if (!isOpen) return null

  const handleJoin = async () => {
    setLoading(true)
    setError('')

    try {
      const response = await waitlistAPI.join()
      setSuccess(true)
      setPosition(response.position)
      await checkWaitlistStatus()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to join waitlist')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
        {/* Background overlay */}
        <div className="fixed inset-0 transition-opacity bg-gray-500 bg-opacity-75" onClick={onClose}></div>

        {/* Modal panel */}
        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
          {/* Close button */}
          <button
            onClick={onClose}
            className="absolute top-4 right-4 text-gray-400 hover:text-gray-600"
          >
            <X className="h-6 w-6" />
          </button>

          {success ? (
            // Success state
            <div className="p-8 text-center">
              <div className="flex justify-center mb-4">
                <div className="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center">
                  <CheckCircle className="h-10 w-10 text-green-600" />
                </div>
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-2">You're on the list!</h3>
              <div className="inline-flex items-center gap-2 px-4 py-2 bg-primary-50 rounded-full mb-4">
                <Users className="h-5 w-5 text-primary-600" />
                <span className="text-lg font-semibold text-primary-700">
                  Position #{position}
                </span>
              </div>
              <p className="text-gray-600 mb-6">
                We'll notify you as soon as unlimited access is ready. Thanks for your interest!
              </p>
              <button
                onClick={onClose}
                className="btn-primary w-full py-5 text-lg font-semibold"
              >
                Continue
              </button>
            </div>
          ) : (
            // Join waitlist state
            <div className="p-8">
              <div className="flex justify-center mb-4">
                <div className="w-16 h-16 rounded-full bg-gradient-to-br from-primary-600 to-purple-600 flex items-center justify-center shadow-lg shadow-primary-400/40 animate-pulse">
                  <Sparkles className="h-8 w-8 text-white" />
                </div>
              </div>

              <h3 className="text-3xl font-bold text-gray-900 text-center mb-3">
                Exclusive Access Awaits
              </h3>

              {/* Scarcity Badge */}
              <div className="bg-gradient-to-r from-amber-50 to-orange-50 border-2 border-amber-300 rounded-lg p-3 mb-4">
                <p className="text-center text-amber-900 font-bold text-sm">
                  🔥 LIMITED AVAILABILITY 🔥
                </p>
                <p className="text-center text-amber-800 text-xs mt-1">
                  We're only serving the first <strong>50 clients</strong> this year
                </p>
              </div>

              <p className="text-gray-600 text-center mb-2">
                You've used all your trials for <strong>{feature}</strong>.
              </p>
              <p className="text-gray-700 text-center mb-6 font-medium">
                Join our exclusive waitlist to secure your spot for unlimited premium access!
              </p>

              {/* Features list */}
              <div className="bg-gray-50 rounded-lg p-4 mb-6 space-y-3">
                <div className="flex items-start gap-3">
                  <CheckCircle className="h-5 w-5 text-green-600 mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="font-medium text-gray-900">Unlimited Generations</p>
                    <p className="text-sm text-gray-600">No more trial limits on any feature</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <CheckCircle className="h-5 w-5 text-green-600 mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="font-medium text-gray-900">Priority Support</p>
                    <p className="text-sm text-gray-600">Get help when you need it</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <CheckCircle className="h-5 w-5 text-green-600 mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="font-medium text-gray-900">Early Access</p>
                    <p className="text-sm text-gray-600">Be first to try new features</p>
                  </div>
                </div>
              </div>

              {error && (
                <div className="mb-4 p-3 rounded-lg bg-red-50 border border-red-200">
                  <p className="text-sm text-red-600">{error}</p>
                </div>
              )}

              <button
                onClick={handleJoin}
                disabled={loading}
                className="btn-primary w-full flex items-center justify-center gap-2 py-5 text-lg font-semibold"
              >
                {loading ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                    Joining...
                  </>
                ) : (
                  <>
                    <Users className="h-5 w-5" />
                    Join Waitlist
                  </>
                )}
              </button>

              <button
                onClick={onClose}
                className="w-full mt-3 px-4 py-2 text-sm text-gray-600 hover:text-gray-900"
              >
                Maybe later
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
