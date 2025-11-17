'use client'

import { useAuth } from '@/contexts/AuthContext'
import { Sparkles, AlertCircle } from 'lucide-react'

interface TrialCounterProps {
  feature: 'ai_designer' | 'virtual_tryon' | 'qc_inspector' | '3d_generation'
  featureName: string
}

export default function TrialCounter({ feature, featureName }: TrialCounterProps) {
  const { trialStatus, user } = useAuth()

  if (!user || !trialStatus) return null

  const status = trialStatus.trial_status[feature]

  if (!status) return null

  if (status.unlimited) {
    return (
      <div className="card bg-gradient-to-br from-primary-50 to-purple-50 border-primary-200">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-primary-600 flex items-center justify-center">
            <Sparkles className="h-5 w-5 text-white" />
          </div>
          <div>
            <p className="text-sm font-medium text-gray-900">Unlimited Access</p>
            <p className="text-xs text-gray-600">You have unlimited access to {featureName}</p>
          </div>
        </div>
      </div>
    )
  }

  const percentage = (status.remaining / status.limit) * 100
  const isLow = status.remaining <= 1

  return (
    <div className={`card ${isLow ? 'bg-amber-50 border-amber-200' : 'bg-gray-50 border-gray-200'}`}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          {isLow ? (
            <AlertCircle className="h-5 w-5 text-amber-600" />
          ) : (
            <Sparkles className="h-5 w-5 text-primary-600" />
          )}
          <span className="text-sm font-medium text-gray-900">
            {featureName} Trials
          </span>
        </div>
        <span className={`text-sm font-bold ${isLow ? 'text-amber-700' : 'text-primary-700'}`}>
          {status.remaining} / {status.limit} left
        </span>
      </div>

      {/* Progress bar */}
      <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
        <div
          className={`h-full transition-all duration-300 ${
            isLow ? 'bg-amber-500' : 'bg-primary-600'
          }`}
          style={{ width: `${percentage}%` }}
        />
      </div>

      {status.remaining === 0 && (
        <p className="mt-2 text-xs text-amber-700">
          You've used all your trials. Join the waitlist for unlimited access!
        </p>
      )}
    </div>
  )
}
