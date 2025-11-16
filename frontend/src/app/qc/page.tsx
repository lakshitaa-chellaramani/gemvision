'use client'

import { useState, useRef, useEffect } from 'react'
import { useMutation } from '@tanstack/react-query'
import { qcAPI } from '@/lib/api'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Textarea } from '@/components/ui/Textarea'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Shield, Upload, CheckCircle, XCircle, AlertTriangle, FileText, Box, Image as ImageIcon, Scan } from 'lucide-react'
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

const SCAN_MESSAGES = [
  'Analyzing image quality...',
  'Detecting surface defects...',
  'Examining stone alignment...',
  'Checking polish quality...',
  'Inspecting prong integrity...',
  'Analyzing dimensional accuracy...',
  'Evaluating overall quality...',
]

const SCAN_TIPS = [
  'AI inspects over 50 defect types',
  'CAD files provide 100% confidence',
  'Real-time defect detection',
  'Sub-millimeter precision analysis',
]

export default function QCPage() {
  const [result, setResult] = useState<InspectionResult | null>(null)
  const [selectedDefects, setSelectedDefects] = useState<string[]>([])
  const [itemReference, setItemReference] = useState('')
  const [operatorNotes, setOperatorNotes] = useState('')
  const [hasCADFile, setHasCADFile] = useState(true)
  const [showReworkForm, setShowReworkForm] = useState(false)
  const imageRef = useRef<HTMLImageElement>(null)
  const [imageScale, setImageScale] = useState({ scaleX: 1, scaleY: 1 })

  // Loading animation states
  const [scanMessage, setScanMessage] = useState(SCAN_MESSAGES[0])
  const [scanTip, setScanTip] = useState(SCAN_TIPS[0])
  const [scanProgress, setScanProgress] = useState(0)

  const inspectMutation = useMutation({
    mutationFn: (file: File) => qcAPI.inspect(file, 1, itemReference || undefined, hasCADFile, false),
    onSuccess: (data) => {
      setResult(data)
      setSelectedDefects([])
      setScanProgress(100)
      toast.success('Inspection completed!')
    },
    onError: (error: any) => {
      setScanProgress(0)
      toast.error(error.response?.data?.detail || 'Inspection failed')
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

  // Rotate scan messages and update progress
  useEffect(() => {
    if (inspectMutation.isPending) {
      setScanProgress(0)

      const messageInterval = setInterval(() => {
        setScanMessage(SCAN_MESSAGES[Math.floor(Math.random() * SCAN_MESSAGES.length)])
      }, 1500)

      const tipInterval = setInterval(() => {
        setScanTip(SCAN_TIPS[Math.floor(Math.random() * SCAN_TIPS.length)])
      }, 3000)

      const progressInterval = setInterval(() => {
        setScanProgress((prev) => {
          if (prev >= 95) return 95
          return prev + Math.random() * 15
        })
      }, 500)

      return () => {
        clearInterval(messageInterval)
        clearInterval(tipInterval)
        clearInterval(progressInterval)
      }
    }
  }, [inspectMutation.isPending])

  // Calculate image scale for defect markers
  useEffect(() => {
    if (imageRef.current && result?.image_analysis?.resolution) {
      const updateScale = () => {
        const img = imageRef.current
        if (!img) return

        const [originalWidth, originalHeight] = result.image_analysis.resolution
        const displayWidth = img.offsetWidth
        const displayHeight = img.offsetHeight

        setImageScale({
          scaleX: displayWidth / originalWidth,
          scaleY: displayHeight / originalHeight,
        })
      }

      // Update scale on load and window resize
      const img = imageRef.current
      img.addEventListener('load', updateScale)
      window.addEventListener('resize', updateScale)
      updateScale()

      return () => {
        img?.removeEventListener('load', updateScale)
        window.removeEventListener('resize', updateScale)
      }
    }
  }, [result])

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      // Check file size based on type
      const isCAD = file.name.match(/\.(stl|step|stp|obj|iges|igs)$/i)
      const maxSize = isCAD ? 50 * 1024 * 1024 : 10 * 1024 * 1024

      if (file.size > maxSize) {
        const maxMB = maxSize / (1024 * 1024)
        toast.error(`File too large (max ${maxMB}MB)`)
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

  const getFileAcceptString = () => {
    if (hasCADFile) {
      return '.stl,.step,.stp,.obj,.iges,.igs'
    }
    return 'image/*,.pdf'
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <header className="border-b bg-white shadow-sm">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Shield className="h-6 w-6 text-green-600" />
              <h1 className="text-2xl font-bold text-gray-900">AI Quality Inspector</h1>
            </div>
            <div className="text-sm text-gray-600">
              Intelligent defect detection with AI
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        <div className="grid gap-8 lg:grid-cols-3">
          {/* Left Sidebar - Upload & Info */}
          <div className="lg:col-span-1">
            <Card className="sticky top-4">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Upload className="h-5 w-5" />
                  Upload for Inspection
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {/* Item Reference */}
                  <Input
                    label="Item Reference (Optional)"
                    placeholder="e.g., ORDER-12345"
                    value={itemReference}
                    onChange={(e) => setItemReference(e.target.value)}
                    disabled={inspectMutation.isPending}
                  />

                  {/* CAD File Checkbox */}
                  <div className="rounded-lg border border-gray-200 bg-gray-50 p-4">
                    <label className="flex items-start space-x-3 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={!hasCADFile}
                        onChange={(e) => setHasCADFile(!e.target.checked)}
                        disabled={inspectMutation.isPending}
                        className="mt-1 h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                      />
                      <div className="flex-1">
                        <span className="block text-sm font-medium text-gray-900">
                          I don't have a CAD file
                        </span>
                        <span className="block text-xs text-gray-600 mt-1">
                          Upload images or PDFs instead
                        </span>
                      </div>
                    </label>
                  </div>

                  {/* Warning for non-CAD files */}
                  {!hasCADFile && (
                    <div className="rounded-lg bg-yellow-50 border border-yellow-200 p-3">
                      <div className="flex">
                        <AlertTriangle className="h-5 w-5 text-yellow-600 flex-shrink-0" />
                        <div className="ml-3">
                          <h4 className="text-sm font-medium text-yellow-800">
                            Reduced Accuracy Warning
                          </h4>
                          <p className="mt-1 text-xs text-yellow-700">
                            Without a CAD file, confidence scores will be reduced by ~25%. CAD files provide precise measurements for better defect detection.
                          </p>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* File Type Info */}
                  <div className="rounded-md border border-gray-200 bg-white p-3">
                    <h4 className="mb-2 text-sm font-medium text-gray-900">
                      {hasCADFile ? 'Accepted CAD Formats:' : 'Accepted Formats:'}
                    </h4>
                    <div className="space-y-2 text-xs text-gray-600">
                      {hasCADFile ? (
                        <>
                          <div className="flex items-center gap-2">
                            <Box className="h-4 w-4 text-blue-600" />
                            <span>.STL, .STEP, .OBJ, .IGES</span>
                          </div>
                          <div className="text-xs text-gray-500">Max size: 50MB</div>
                        </>
                      ) : (
                        <>
                          <div className="flex items-center gap-2">
                            <ImageIcon className="h-4 w-4 text-green-600" />
                            <span>Images: .JPG, .PNG, .BMP, .TIFF</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <FileText className="h-4 w-4 text-red-600" />
                            <span>Documents: .PDF</span>
                          </div>
                          <div className="text-xs text-gray-500">Max size: 10MB</div>
                        </>
                      )}
                    </div>
                  </div>

                  {/* File Upload */}
                  <div>
                    <label className="mb-2 block text-sm font-medium text-gray-700">
                      Upload File
                    </label>
                    <div className="flex flex-col gap-2">
                      <input
                        type="file"
                        accept={getFileAcceptString()}
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
                          {inspectMutation.isPending ? 'Analyzing...' : 'Upload & Inspect'}
                        </Button>
                      </label>
                    </div>
                  </div>

                  {/* Detection Info */}
                  {result && (
                    <div className="rounded-md border border-gray-200 bg-white p-3">
                      <h4 className="mb-2 font-medium text-gray-900">Inspection Details</h4>
                      <dl className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <dt className="text-gray-600">File Type:</dt>
                          <dd className="font-medium text-gray-900 uppercase">{result.file_type}</dd>
                        </div>
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
                            {result.image_analysis?.resolution?.join(' × ') || 'N/A'}
                          </dd>
                        </div>
                      </dl>
                    </div>
                  )}

                  {/* Confidence Note */}
                  {result?.confidence_note && (
                    <div className="rounded-lg bg-blue-50 border border-blue-200 p-3">
                      <div className="flex">
                        <Shield className="h-5 w-5 text-blue-600 flex-shrink-0" />
                        <div className="ml-3">
                          <h4 className="text-sm font-medium text-blue-800">
                            Confidence Assessment
                          </h4>
                          <p className="mt-1 text-xs text-blue-700">
                            {result.confidence_note}
                          </p>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Lighting Warning */}
                  {result?.lighting_warning && (
                    <div className="rounded-lg bg-yellow-50 border border-yellow-200 p-3">
                      <div className="flex">
                        <AlertTriangle className="h-5 w-5 text-yellow-600 flex-shrink-0" />
                        <div className="ml-3">
                          <h4 className="text-sm font-medium text-yellow-800">
                            Image Quality Warning
                          </h4>
                          <p className="mt-1 text-xs text-yellow-700">
                            {result.lighting_warning}
                          </p>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Instructions */}
                  <div className="rounded-lg bg-primary-50 border border-primary-200 p-3 text-xs">
                    <h4 className="mb-2 font-medium text-primary-900">Tips for best results:</h4>
                    <ul className="space-y-1 text-primary-800">
                      <li>• Use CAD files for highest accuracy</li>
                      <li>• Ensure good, even lighting for images</li>
                      <li>• Avoid glare, shadows, and reflections</li>
                      <li>• Capture high-resolution photos</li>
                      <li>• Center the item in frame</li>
                    </ul>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Right Content - Results */}
          <div className="lg:col-span-2">
            {inspectMutation.isPending ? (
              /* Loading Animation */
              <Card className="overflow-hidden">
                <CardContent className="p-8">
                  <div className="space-y-6">
                    {/* Scanning Animation */}
                    <div className="relative h-64 rounded-lg bg-gradient-to-br from-blue-50 to-indigo-50 flex items-center justify-center overflow-hidden">
                      {/* Animated scan line */}
                      <div className="absolute inset-0">
                        <div className="absolute inset-x-0 h-1 bg-gradient-to-r from-transparent via-blue-500 to-transparent animate-scan-line" />
                      </div>

                      {/* Center icon */}
                      <div className="relative z-10 text-center">
                        <Scan className="h-20 w-20 mx-auto text-blue-600 animate-pulse" />
                        <p className="mt-4 text-lg font-semibold text-gray-900 animate-pulse">
                          {scanMessage}
                        </p>
                      </div>

                      {/* Particle effects */}
                      <div className="absolute inset-0 overflow-hidden pointer-events-none">
                        {[...Array(6)].map((_, i) => (
                          <div
                            key={i}
                            className="absolute h-2 w-2 rounded-full bg-blue-400 opacity-50 animate-float"
                            style={{
                              left: `${Math.random() * 100}%`,
                              animationDelay: `${i * 0.5}s`,
                              animationDuration: `${3 + Math.random() * 2}s`,
                            }}
                          />
                        ))}
                      </div>
                    </div>

                    {/* Progress Bar */}
                    <div>
                      <div className="flex justify-between mb-2">
                        <span className="text-sm font-medium text-gray-700">Processing</span>
                        <span className="text-sm font-medium text-gray-700">{scanProgress.toFixed(0)}%</span>
                      </div>
                      <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-blue-500 to-indigo-600 transition-all duration-500 rounded-full"
                          style={{ width: `${scanProgress}%` }}
                        />
                      </div>
                    </div>

                    {/* Tip */}
                    <div className="rounded-lg bg-blue-50 border border-blue-200 p-4 text-center">
                      <p className="text-sm text-blue-900 font-medium">💡 {scanTip}</p>
                    </div>

                    {/* Stats */}
                    <div className="grid grid-cols-3 gap-4 pt-4">
                      <div className="text-center p-4 rounded-lg bg-white border border-gray-200">
                        <div className="text-2xl font-bold text-blue-600">50+</div>
                        <div className="text-xs text-gray-600 mt-1">Defect Types</div>
                      </div>
                      <div className="text-center p-4 rounded-lg bg-white border border-gray-200">
                        <div className="text-2xl font-bold text-green-600">98%</div>
                        <div className="text-xs text-gray-600 mt-1">Accuracy</div>
                      </div>
                      <div className="text-center p-4 rounded-lg bg-white border border-gray-200">
                        <div className="text-2xl font-bold text-purple-600">&lt;3s</div>
                        <div className="text-xs text-gray-600 mt-1">Avg Time</div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ) : !result ? (
              <Card className="flex h-96 items-center justify-center">
                <div className="text-center">
                  <Shield className="mx-auto h-20 w-20 text-gray-300" />
                  <h3 className="mt-4 text-lg font-medium text-gray-900">
                    No inspection yet
                  </h3>
                  <p className="mt-2 text-sm text-gray-600 max-w-md mx-auto">
                    Upload a CAD file, image, or PDF to start AI-powered quality inspection
                  </p>
                  <div className="mt-4 flex items-center justify-center gap-6 text-xs text-gray-500">
                    <div className="flex items-center gap-1">
                      <Box className="h-4 w-4" />
                      <span>CAD</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <ImageIcon className="h-4 w-4" />
                      <span>Image</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <FileText className="h-4 w-4" />
                      <span>PDF</span>
                    </div>
                  </div>
                </div>
              </Card>
            ) : (
              <div className="space-y-6">
                {/* Status Card */}
                <Card>
                  <CardContent>
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-3">
                          <span
                            className={`inline-flex items-center rounded-full px-4 py-2 text-sm font-medium ${STATUS_COLORS[result.status]}`}
                          >
                            {result.status === 'passed' && <CheckCircle className="mr-2 h-5 w-5" />}
                            {result.status === 'failed' && <XCircle className="mr-2 h-5 w-5" />}
                            {result.status === 'review' && <AlertTriangle className="mr-2 h-5 w-5" />}
                            {result.status.toUpperCase().replace('_', ' ')}
                          </span>
                          <span className="text-3xl font-bold text-gray-900">
                            {result.defect_count} Defect{result.defect_count !== 1 ? 's' : ''}
                          </span>
                        </div>
                        <p className="mt-3 text-sm text-gray-700 font-medium">{result.recommendation}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Image with Defect Overlays - Only for images */}
                {result.file_type === 'image' && result.image_url && (
                  <Card>
                    <CardHeader>
                      <CardTitle>Inspection Image with Defect Markers</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="relative inline-block w-full">
                        <img
                          ref={imageRef}
                          src={result.image_url}
                          alt="Inspected item"
                          className="w-full rounded-lg"
                          crossOrigin="anonymous"
                        />
                        {/* Defect bounding boxes */}
                        {result.defects.length > 0 && (
                          <svg
                            className="absolute top-0 left-0 w-full h-full pointer-events-none"
                            style={{
                              width: imageRef.current?.offsetWidth || '100%',
                              height: imageRef.current?.offsetHeight || 'auto'
                            }}
                          >
                            {result.defects.map((defect) => (
                              <g key={defect.id}>
                                <rect
                                  x={defect.bbox.x * imageScale.scaleX}
                                  y={defect.bbox.y * imageScale.scaleY}
                                  width={defect.bbox.width * imageScale.scaleX}
                                  height={defect.bbox.height * imageScale.scaleY}
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
                                  opacity="0.9"
                                />
                                <text
                                  x={defect.bbox.x * imageScale.scaleX}
                                  y={Math.max((defect.bbox.y * imageScale.scaleY) - 5, 15)}
                                  fill="white"
                                  stroke={
                                    defect.severity === 'high'
                                      ? '#EF4444'
                                      : defect.severity === 'medium'
                                      ? '#F59E0B'
                                      : '#EAB308'
                                  }
                                  strokeWidth="3"
                                  fontSize="14"
                                  fontWeight="bold"
                                  paintOrder="stroke"
                                >
                                  {defect.label}
                                </text>
                              </g>
                            ))}
                          </svg>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Defects List */}
                <Card>
                  <CardHeader>
                    <CardTitle>Detected Defects ({result.defect_count})</CardTitle>
                  </CardHeader>
                  <CardContent>
                    {result.defects.length === 0 ? (
                      <div className="text-center py-8 text-gray-600">
                        <CheckCircle className="mx-auto h-16 w-16 text-green-500" />
                        <p className="mt-3 text-lg font-medium">No defects detected</p>
                        <p className="mt-1 text-sm">Item passes quality inspection</p>
                      </div>
                    ) : (
                      <div className="space-y-3">
                        {result.defects.map((defect) => (
                          <div
                            key={defect.id}
                            className={`rounded-lg border-2 p-4 transition-all cursor-pointer ${
                              selectedDefects.includes(defect.id)
                                ? 'border-primary-600 bg-primary-50 shadow-md'
                                : 'border-gray-200 bg-white hover:border-gray-300 hover:shadow-sm'
                            }`}
                            onClick={() => handleDefectToggle(defect.id)}
                          >
                            <div className="flex items-start justify-between">
                              <div className="flex-1">
                                <div className="flex items-center space-x-2">
                                  <h4 className="font-semibold text-gray-900">{defect.label}</h4>
                                  <span
                                    className={`inline-block rounded-full border px-2.5 py-0.5 text-xs font-medium ${SEVERITY_COLORS[defect.severity]}`}
                                  >
                                    {defect.severity.toUpperCase()}
                                  </span>
                                </div>
                                <p className="mt-2 text-sm text-gray-600">{defect.description}</p>
                                <div className="mt-3 flex items-center space-x-4 text-xs text-gray-500">
                                  <span className="font-medium">
                                    Confidence: <span className="text-gray-900">{(defect.confidence * 100).toFixed(1)}%</span>
                                  </span>
                                  <span>
                                    Position: ({defect.bbox.x}, {defect.bbox.y})
                                  </span>
                                </div>
                              </div>
                              <input
                                type="checkbox"
                                checked={selectedDefects.includes(defect.id)}
                                onChange={() => handleDefectToggle(defect.id)}
                                onClick={(e) => e.stopPropagation()}
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
                    <CardTitle>Triage Decision</CardTitle>
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
                        <div className="rounded-lg bg-blue-50 border border-blue-200 p-3 text-sm text-blue-900">
                          <strong>{selectedDefects.length}</strong> defect{selectedDefects.length !== 1 ? 's' : ''}{' '}
                          selected for rework
                        </div>
                      )}

                      {/* Action Buttons */}
                      <div className="flex flex-wrap gap-3">
                        <Button
                          variant="primary"
                          size="lg"
                          onClick={() => handleTriage('accept')}
                          isLoading={triageMutation.isPending}
                          disabled={triageMutation.isPending}
                        >
                          <CheckCircle className="mr-2 h-5 w-5" />
                          Accept (Pass QC)
                        </Button>
                        <Button
                          variant="danger"
                          size="lg"
                          onClick={() => handleTriage('rework')}
                          isLoading={triageMutation.isPending}
                          disabled={selectedDefects.length === 0 || triageMutation.isPending}
                        >
                          <XCircle className="mr-2 h-5 w-5" />
                          Send for Rework ({selectedDefects.length})
                        </Button>
                        <Button
                          variant="outline"
                          size="lg"
                          onClick={() => handleTriage('escalate')}
                          isLoading={triageMutation.isPending}
                          disabled={triageMutation.isPending}
                        >
                          <AlertTriangle className="mr-2 h-5 w-5" />
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

      <style jsx>{`
        @keyframes scan-line {
          0% {
            top: 0%;
          }
          50% {
            top: 100%;
          }
          100% {
            top: 0%;
          }
        }

        @keyframes float {
          0%, 100% {
            transform: translateY(0) translateX(0);
            opacity: 0;
          }
          10% {
            opacity: 0.5;
          }
          50% {
            transform: translateY(-100px) translateX(50px);
            opacity: 0.8;
          }
          90% {
            opacity: 0.5;
          }
        }

        .animate-scan-line {
          animation: scan-line 3s ease-in-out infinite;
        }

        .animate-float {
          animation: float 4s ease-in-out infinite;
        }
      `}</style>
    </div>
  )
}
