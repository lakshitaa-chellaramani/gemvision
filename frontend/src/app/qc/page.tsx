'use client'

import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { qcAPI } from '@/lib/api'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Textarea } from '@/components/ui/Textarea'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Shield, Upload, CheckCircle, XCircle, AlertTriangle, Eye } from 'lucide-react'
import toast from 'react-hot-toast'
import type { InspectionResult, Defect, QCDecision } from '@/types'

const SEVERITY_COLORS = {
  low: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  medium: 'bg-orange-100 text-orange-800 border-orange-200',
  high: 'bg-red-100 text-red-800 border-red-200',
}

const STATUS_COLORS = {
  passed: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
  review: 'bg-orange-100 text-orange-800',
  passed_with_notes: 'bg-blue-100 text-blue-800',
}

export default function QCPage() {
  const [result, setResult] = useState<InspectionResult | null>(null)
  const [selectedDefects, setSelectedDefects] = useState<string[]>([])
  const [itemReference, setItemReference] = useState('')
  const [operatorNotes, setOperatorNotes] = useState('')
  const [showReworkForm, setShowReworkForm] = useState(false)

  const inspectMutation = useMutation({
    mutationFn: (file: File) => qcAPI.inspect(file, 1, itemReference || undefined, false),
    onSuccess: (data) => {
      setResult(data)
      setSelectedDefects([])
      toast.success('Inspection completed!')
    },
    onError: () => {
      toast.error('Inspection failed')
    },
  })

  const triageMutation = useMutation({
    mutationFn: (data: {
      inspection_id: number
      decision: QCDecision
      operator_notes: string
      selected_defects?: string[]
    }) => qcAPI.triage(data),
    onSuccess: () => {
      toast.success('Inspection triaged successfully!')
      setShowReworkForm(false)
      setOperatorNotes('')
    },
    onError: () => {
      toast.error('Failed to triage inspection')
    },
  })

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      if (file.size > 10 * 1024 * 1024) {
        toast.error('File too large (max 10MB)')
        return
      }
      inspectMutation.mutate(file)
    }
  }

  const handleDefectToggle = (defectId: string) => {
    setSelectedDefects((prev) =>
      prev.includes(defectId) ? prev.filter((id) => id !== defectId) : [...prev, defectId]
    )
  }

  const handleTriage = (decision: QCDecision) => {
    if (!result) return

    if (decision === 'rework' && selectedDefects.length === 0) {
      toast.error('Please select at least one defect for rework')
      return
    }

    triageMutation.mutate({
      inspection_id: result.inspection_id,
      decision,
      operator_notes: operatorNotes,
      selected_defects: decision === 'rework' ? selectedDefects : undefined,
    })
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="border-b bg-white">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center space-x-2">
            <Shield className="h-6 w-6 text-green-600" />
            <h1 className="text-2xl font-bold text-gray-900">AI Quality Inspector</h1>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        <div className="grid gap-8 lg:grid-cols-3">
          {/* Left Sidebar - Upload & Info */}
          <div className="lg:col-span-1">
            <Card>
              <CardHeader>
                <CardTitle>Upload Item</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {/* Item Reference */}
                  <Input
                    label="Item Reference (Optional)"
                    placeholder="e.g., ORDER-12345"
                    value={itemReference}
                    onChange={(e) => setItemReference(e.target.value)}
                  />

                  {/* File Upload */}
                  <div>
                    <label className="mb-2 block text-sm font-medium text-gray-700">
                      Upload Photo
                    </label>
                    <div className="flex flex-col gap-2">
                      <input
                        type="file"
                        accept="image/*"
                        onChange={handleFileUpload}
                        className="hidden"
                        id="qc-upload"
                        disabled={inspectMutation.isPending}
                      />
                      <label htmlFor="qc-upload">
                        <Button
                          as="span"
                          variant="primary"
                          size="lg"
                          className="w-full cursor-pointer"
                          isLoading={inspectMutation.isPending}
                        >
                          <Upload className="mr-2 h-4 w-4" />
                          {inspectMutation.isPending ? 'Inspecting...' : 'Upload & Inspect'}
                        </Button>
                      </label>
                    </div>
                  </div>

                  {/* Detection Info */}
                  {result && (
                    <div className="rounded-md border p-3">
                      <h4 className="mb-2 font-medium text-gray-900">Detection Info</h4>
                      <dl className="space-y-1 text-sm">
                        <div className="flex justify-between">
                          <dt className="text-gray-600">Mode:</dt>
                          <dd className="font-medium text-gray-900">{result.detection_mode}</dd>
                        </div>
                        <div className="flex justify-between">
                          <dt className="text-gray-600">Threshold:</dt>
                          <dd className="font-medium text-gray-900">
                            {(result.confidence_threshold * 100).toFixed(0)}%
                          </dd>
                        </div>
                        <div className="flex justify-between">
                          <dt className="text-gray-600">Resolution:</dt>
                          <dd className="font-medium text-gray-900">
                            {result.image_analysis.resolution.join(' × ')}
                          </dd>
                        </div>
                      </dl>
                    </div>
                  )}

                  {/* Lighting Warning */}
                  {result?.lighting_warning && (
                    <div className="rounded-md bg-yellow-50 border border-yellow-200 p-3">
                      <div className="flex">
                        <AlertTriangle className="h-5 w-5 text-yellow-600" />
                        <div className="ml-3">
                          <h4 className="text-sm font-medium text-yellow-800">
                            Image Quality Warning
                          </h4>
                          <p className="mt-1 text-sm text-yellow-700">
                            {result.lighting_warning}
                          </p>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Instructions */}
                  <div className="rounded-md bg-blue-50 p-3 text-sm">
                    <h4 className="mb-2 font-medium text-blue-900">Tips for best results:</h4>
                    <ul className="space-y-1 text-blue-700">
                      <li>• Use good, even lighting</li>
                      <li>• Avoid glare and shadows</li>
                      <li>• Capture high-resolution images</li>
                      <li>• Center the item in frame</li>
                    </ul>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Right Content - Results */}
          <div className="lg:col-span-2">
            {!result ? (
              <Card className="flex h-96 items-center justify-center">
                <div className="text-center">
                  <Shield className="mx-auto h-16 w-16 text-gray-400" />
                  <h3 className="mt-4 text-lg font-medium text-gray-900">
                    No inspection yet
                  </h3>
                  <p className="mt-2 text-sm text-gray-600">
                    Upload a jewellery photo to start quality inspection
                  </p>
                </div>
              </Card>
            ) : (
              <div className="space-y-6">
                {/* Status Card */}
                <Card>
                  <CardContent>
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="flex items-center space-x-3">
                          <span
                            className={`inline-flex items-center rounded-full px-3 py-1 text-sm font-medium ${STATUS_COLORS[result.status]}`}
                          >
                            {result.status === 'passed' && <CheckCircle className="mr-1 h-4 w-4" />}
                            {result.status === 'failed' && <XCircle className="mr-1 h-4 w-4" />}
                            {result.status === 'review' && <AlertTriangle className="mr-1 h-4 w-4" />}
                            {result.status.toUpperCase().replace('_', ' ')}
                          </span>
                          <span className="text-2xl font-bold text-gray-900">
                            {result.defect_count} Defect{result.defect_count !== 1 ? 's' : ''} Found
                          </span>
                        </div>
                        <p className="mt-2 text-sm text-gray-600">{result.recommendation}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Image with Defect Overlays */}
                <Card>
                  <CardHeader>
                    <CardTitle>Inspection Image</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="relative">
                      <img
                        src={result.image_url}
                        alt="Inspected item"
                        className="w-full rounded-lg"
                      />
                      {/* Defect bounding boxes */}
                      <svg
                        className="absolute inset-0 h-full w-full"
                        style={{ pointerEvents: 'none' }}
                      >
                        {result.defects.map((defect) => (
                          <g key={defect.id}>
                            <rect
                              x={defect.bbox.x}
                              y={defect.bbox.y}
                              width={defect.bbox.width}
                              height={defect.bbox.height}
                              fill="none"
                              stroke={
                                defect.severity === 'high'
                                  ? '#EF4444'
                                  : defect.severity === 'medium'
                                  ? '#F59E0B'
                                  : '#EAB308'
                              }
                              strokeWidth="3"
                              strokeDasharray={selectedDefects.includes(defect.id) ? '0' : '5,5'}
                            />
                            <text
                              x={defect.bbox.x}
                              y={defect.bbox.y - 5}
                              fill={
                                defect.severity === 'high'
                                  ? '#EF4444'
                                  : defect.severity === 'medium'
                                  ? '#F59E0B'
                                  : '#EAB308'
                              }
                              fontSize="14"
                              fontWeight="bold"
                            >
                              {defect.label}
                            </text>
                          </g>
                        ))}
                      </svg>
                    </div>
                  </CardContent>
                </Card>

                {/* Defects List */}
                <Card>
                  <CardHeader>
                    <CardTitle>Detected Defects</CardTitle>
                  </CardHeader>
                  <CardContent>
                    {result.defects.length === 0 ? (
                      <div className="text-center py-6 text-gray-600">
                        <CheckCircle className="mx-auto h-12 w-12 text-green-500" />
                        <p className="mt-2">No defects detected</p>
                      </div>
                    ) : (
                      <div className="space-y-3">
                        {result.defects.map((defect) => (
                          <div
                            key={defect.id}
                            className={`rounded-lg border-2 p-4 transition-all ${
                              selectedDefects.includes(defect.id)
                                ? 'border-primary-600 bg-primary-50'
                                : 'border-gray-200 bg-white hover:border-gray-300'
                            }`}
                          >
                            <div className="flex items-start justify-between">
                              <div className="flex-1">
                                <div className="flex items-center space-x-2">
                                  <h4 className="font-medium text-gray-900">{defect.label}</h4>
                                  <span
                                    className={`inline-block rounded-full border px-2 py-0.5 text-xs font-medium ${SEVERITY_COLORS[defect.severity]}`}
                                  >
                                    {defect.severity.toUpperCase()}
                                  </span>
                                </div>
                                <p className="mt-1 text-sm text-gray-600">{defect.description}</p>
                                <div className="mt-2 flex items-center space-x-4 text-xs text-gray-500">
                                  <span>Confidence: {(defect.confidence * 100).toFixed(1)}%</span>
                                  <span>
                                    Position: ({defect.bbox.x}, {defect.bbox.y})
                                  </span>
                                </div>
                              </div>
                              <input
                                type="checkbox"
                                checked={selectedDefects.includes(defect.id)}
                                onChange={() => handleDefectToggle(defect.id)}
                                className="h-5 w-5 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                              />
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>

                {/* Triage Actions */}
                <Card>
                  <CardHeader>
                    <CardTitle>Triage Actions</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {/* Operator Notes */}
                      <Textarea
                        label="Operator Notes (Optional)"
                        placeholder="Add any notes about this inspection..."
                        value={operatorNotes}
                        onChange={(e) => setOperatorNotes(e.target.value)}
                        rows={3}
                      />

                      {/* Selected Defects Info */}
                      {selectedDefects.length > 0 && (
                        <div className="rounded-md bg-blue-50 p-3 text-sm text-blue-900">
                          {selectedDefects.length} defect{selectedDefects.length !== 1 ? 's' : ''}{' '}
                          selected for rework
                        </div>
                      )}

                      {/* Action Buttons */}
                      <div className="flex flex-wrap gap-2">
                        <Button
                          variant="primary"
                          onClick={() => handleTriage('accept')}
                          isLoading={triageMutation.isPending}
                          disabled={triageMutation.isPending}
                        >
                          <CheckCircle className="mr-2 h-4 w-4" />
                          Accept (Pass QC)
                        </Button>
                        <Button
                          variant="danger"
                          onClick={() => handleTriage('rework')}
                          isLoading={triageMutation.isPending}
                          disabled={selectedDefects.length === 0 || triageMutation.isPending}
                        >
                          <XCircle className="mr-2 h-4 w-4" />
                          Send for Rework ({selectedDefects.length})
                        </Button>
                        <Button
                          variant="outline"
                          onClick={() => handleTriage('escalate')}
                          isLoading={triageMutation.isPending}
                          disabled={triageMutation.isPending}
                        >
                          <AlertTriangle className="mr-2 h-4 w-4" />
                          Escalate for Review
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
