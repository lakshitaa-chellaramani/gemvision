'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { analyticsAPI } from '@/lib/api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { TrendingUp, Sparkles, Eye, Shield, BarChart } from 'lucide-react'
import ProtectedRoute from '@/components/ProtectedRoute'
import Navbar from '@/components/Navbar'
import WaitlistModal from '@/components/auth/WaitlistModal'
import TrialCounter from '@/components/auth/TrialCounter'

export default function AnalyticsPage() {
  const [showWaitlist, setShowWaitlist] = useState(false)

  const { data: dashboard, isLoading: dashboardLoading } = useQuery({
    queryKey: ['dashboard', 30],
    queryFn: () => analyticsAPI.getDashboard(30, 1),
  })

  const { data: kpis, isLoading: kpisLoading } = useQuery({
    queryKey: ['kpis', 30],
    queryFn: () => analyticsAPI.getKPIs(30, 1),
  })

  if (dashboardLoading || kpisLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <div className="spinner mx-auto" />
          <p className="mt-4 text-gray-600">Loading analytics...</p>
        </div>
      </div>
    )
  }

  return (
    <ProtectedRoute>
      <Navbar />
      <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-4">
        <TrialCounter feature="3d_generation" featureName="3D Model Generation" />
      </div>

      <div className="container mx-auto px-4 py-8">
        <div className="space-y-8">
          {/* KPI Cards */}
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Total Designs</p>
                    <p className="mt-2 text-3xl font-bold text-gray-900">
                      {dashboard?.totals.designs || 0}
                    </p>
                  </div>
                  <div className="rounded-full bg-primary-100 p-3">
                    <Sparkles className="h-6 w-6 text-primary-600" />
                  </div>
                </div>
                {kpis && (
                  <p className="mt-2 text-sm text-gray-600">
                    Avg {kpis.avg_designs_per_day.toFixed(1)}/day
                  </p>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Try-Ons</p>
                    <p className="mt-2 text-3xl font-bold text-gray-900">
                      {dashboard?.totals.tryons || 0}
                    </p>
                  </div>
                  <div className="rounded-full bg-gold-100 p-3">
                    <Eye className="h-6 w-6 text-gold-600" />
                  </div>
                </div>
                {dashboard && (
                  <p className="mt-2 text-sm text-gray-600">
                    {dashboard.tryon_approval_rate.toFixed(1)}% approval rate
                  </p>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">QC Inspections</p>
                    <p className="mt-2 text-3xl font-bold text-gray-900">
                      {dashboard?.totals.inspections || 0}
                    </p>
                  </div>
                  <div className="rounded-full bg-green-100 p-3">
                    <Shield className="h-6 w-6 text-green-600" />
                  </div>
                </div>
                {kpis && (
                  <p className="mt-2 text-sm text-gray-600">
                    {kpis.qc_false_positive_rate.toFixed(1)}% false positive
                  </p>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Conversion Rate</p>
                    <p className="mt-2 text-3xl font-bold text-gray-900">
                      {kpis?.conversion_to_tryon_rate.toFixed(1) || 0}%
                    </p>
                  </div>
                  <div className="rounded-full bg-blue-100 p-3">
                    <TrendingUp className="h-6 w-6 text-blue-600" />
                  </div>
                </div>
                <p className="mt-2 text-sm text-gray-600">Design → Try-On</p>
              </CardContent>
            </Card>
          </div>

          {/* Charts Row */}
          <div className="grid gap-6 lg:grid-cols-2">
            {/* Designs by Category */}
            <Card>
              <CardHeader>
                <CardTitle>Designs by Category</CardTitle>
              </CardHeader>
              <CardContent>
                {dashboard?.designs_by_category &&
                Object.keys(dashboard.designs_by_category).length > 0 ? (
                  <div className="space-y-3">
                    {Object.entries(dashboard.designs_by_category).map(([category, count]) => (
                      <div key={category}>
                        <div className="flex items-center justify-between text-sm mb-1">
                          <span className="font-medium capitalize text-gray-700">{category}</span>
                          <span className="text-gray-900">{String(count)}</span>
                        </div>
                        <div className="h-2 w-full overflow-hidden rounded-full bg-gray-200">
                          <div
                            className="h-full rounded-full bg-primary-600"
                            style={{
                              width: `${
                                (Number(count) / Math.max(...Object.values(dashboard.designs_by_category).map(Number))) * 100
                              }%`,
                            }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-6 text-gray-500">No data available</div>
                )}
              </CardContent>
            </Card>

            {/* Designs by Style */}
            <Card>
              <CardHeader>
                <CardTitle>Designs by Style</CardTitle>
              </CardHeader>
              <CardContent>
                {dashboard?.designs_by_style &&
                Object.keys(dashboard.designs_by_style).length > 0 ? (
                  <div className="space-y-3">
                    {Object.entries(dashboard.designs_by_style).map(([style, count]) => (
                      <div key={style}>
                        <div className="flex items-center justify-between text-sm mb-1">
                          <span className="font-medium capitalize text-gray-700">
                            {style.replace('_', ' ')}
                          </span>
                          <span className="text-gray-900">{String(count)}</span>
                        </div>
                        <div className="h-2 w-full overflow-hidden rounded-full bg-gray-200">
                          <div
                            className="h-full rounded-full bg-gold-600"
                            style={{
                              width: `${
                                (Number(count) / Math.max(...Object.values(dashboard.designs_by_style).map(Number))) *
                                100
                              }%`,
                            }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-6 text-gray-500">No data available</div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* QC Decisions */}
          <Card>
            <CardHeader>
              <CardTitle>QC Inspection Results</CardTitle>
            </CardHeader>
            <CardContent>
              {dashboard?.qc_decisions && Object.keys(dashboard.qc_decisions).length > 0 ? (
                <div className="grid gap-4 md:grid-cols-3">
                  {Object.entries(dashboard.qc_decisions).map(([decision, count]) => (
                    <div key={decision} className="rounded-lg border border-gray-200 bg-gray-50 p-4">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium capitalize text-gray-700">
                          {decision}
                        </span>
                        <span className="text-2xl font-bold text-gray-900">{String(count)}</span>
                      </div>
                      <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-gray-200">
                        <div
                          className={`h-full rounded-full ${
                            decision === 'accept'
                              ? 'bg-green-600'
                              : decision === 'rework'
                              ? 'bg-red-600'
                              : 'bg-orange-600'
                          }`}
                          style={{
                            width: `${
                              (Number(count) / Object.values(dashboard.qc_decisions as any[]).reduce((a: number, b: number) => a + b, 0)) *
                              100
                            }%`,
                          }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-6 text-gray-500">No QC data available</div>
              )}
            </CardContent>
          </Card>

          {/* Recent Activity */}
          <Card>
            <CardHeader>
              <CardTitle>Recent Designs</CardTitle>
            </CardHeader>
            <CardContent>
              {dashboard?.recent_activity && dashboard.recent_activity.length > 0 ? (
                <div className="space-y-4">
                  {(dashboard.recent_activity as any[]).map((activity: any) => (
                    <div
                      key={activity.id}
                      className="flex items-center space-x-4 rounded-lg border border-gray-200 p-4"
                    >
                      {activity.thumbnail && (
                        <div className="h-16 w-16 flex-shrink-0 overflow-hidden rounded-md">
                          <img
                            src={activity.thumbnail}
                            alt="Design"
                            className="h-full w-full object-cover"
                          />
                        </div>
                      )}
                      <div className="flex-1">
                        <div className="flex items-center space-x-2">
                          <span className="inline-block rounded-full bg-primary-100 px-2 py-0.5 text-xs font-medium text-primary-800 capitalize">
                            {activity.category}
                          </span>
                          <span className="inline-block rounded-full bg-gold-100 px-2 py-0.5 text-xs font-medium text-gold-800 capitalize">
                            {activity.style_preset}
                          </span>
                        </div>
                        <p className="mt-1 text-sm text-gray-600">
                          Created {new Date(activity.created_at).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-6 text-gray-500">No recent activity</div>
              )}
            </CardContent>
          </Card>

          {/* Performance Metrics */}
          <Card>
            <CardHeader>
              <CardTitle>Performance Metrics (Last 30 Days)</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <div className="rounded-lg bg-gradient-to-br from-primary-50 to-primary-100 p-4">
                  <p className="text-sm font-medium text-primary-900">Avg Designs/Day</p>
                  <p className="mt-2 text-2xl font-bold text-primary-900">
                    {kpis?.avg_designs_per_day.toFixed(1) || '0'}
                  </p>
                </div>
                <div className="rounded-lg bg-gradient-to-br from-gold-50 to-gold-100 p-4">
                  <p className="text-sm font-medium text-gold-900">Design → Try-On</p>
                  <p className="mt-2 text-2xl font-bold text-gold-900">
                    {kpis?.conversion_to_tryon_rate.toFixed(1) || '0'}%
                  </p>
                </div>
                <div className="rounded-lg bg-gradient-to-br from-green-50 to-green-100 p-4">
                  <p className="text-sm font-medium text-green-900">QC False Positive</p>
                  <p className="mt-2 text-2xl font-bold text-green-900">
                    {kpis?.qc_false_positive_rate.toFixed(1) || '0'}%
                  </p>
                </div>
                <div className="rounded-lg bg-gradient-to-br from-blue-50 to-blue-100 p-4">
                  <p className="text-sm font-medium text-blue-900">AI Confidence</p>
                  <p className="mt-2 text-2xl font-bold text-blue-900">
                    {kpis?.avg_ai_confidence.toFixed(1) || '0'}%
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
      </div>

      <WaitlistModal
        isOpen={showWaitlist}
        onClose={() => setShowWaitlist(false)}
        feature="3D Model Generation"
      />
    </ProtectedRoute>
  )
}
