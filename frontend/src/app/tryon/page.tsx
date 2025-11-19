'use client'

import { useState, useRef, useEffect, Suspense } from 'react'
import { useMutation } from '@tanstack/react-query'
import { useSearchParams } from 'next/navigation'
import { tryonAPI, designerAPI } from '@/lib/api'
import { Button } from '@/components/ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Eye, Upload, Download, Share2, RotateCw, Move, ZoomIn, Sparkles, Info, CheckCircle2, Image as ImageIcon } from 'lucide-react'
import toast from 'react-hot-toast'
import type { TryOnTransform, FingerType } from '@/types'
import ProtectedRoute from '@/components/ProtectedRoute'
import Navbar from '@/components/Navbar'
import WaitlistModal from '@/components/auth/WaitlistModal'
import TrialCounter from '@/components/auth/TrialCounter'
import { compressImage } from '@/lib/imageCompression'

// API URL helper - matches same logic as api.ts
const getApiUrl = () => {
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      return 'http://localhost:8000'
    }
    return 'https://jeweltech.ai'
  }
  return 'https://jeweltech.ai'
}

const FINGER_TYPES: { value: FingerType; label: string }[] = [
  { value: 'index', label: 'Index Finger' },
  { value: 'middle', label: 'Middle Finger' },
  { value: 'ring', label: 'Ring Finger' },
  { value: 'little', label: 'Little Finger' },
]

function TryOnContent() {
  const searchParams = useSearchParams()
  const designIdParam = searchParams.get('design')

  const [bodyPhoto, setBodyPhoto] = useState<File | null>(null)
  const [bodyPhotoPreview, setBodyPhotoPreview] = useState<string | null>(null)
  const [jewelryPhoto, setJewelryPhoto] = useState<File | null>(null)
  const [jewelryPhotoPreview, setJewelryPhotoPreview] = useState<string | null>(null)
  const [jewelryType, setJewelryType] = useState<string>('ring')
  const [jewelryDescription, setJewelryDescription] = useState<string>('')
  const [designData, setDesignData] = useState<any>(null)
  const [tryOnResult, setTryOnResult] = useState<any>(null)
  const [detectionResult, setDetectionResult] = useState<any>(null)
  const [showWaitlist, setShowWaitlist] = useState(false)

  const [overlayImage, setOverlayImage] = useState<string | null>(null)
  const [transform, setTransform] = useState<TryOnTransform>({
    x: 50,
    y: 50,
    scale: 1,
    rotation: 0,
    opacity: 1,
    hue: 0,
  })
  const [fingerType, setFingerType] = useState<FingerType>('ring')
  const [isDragging, setIsDragging] = useState(false)
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 })

  const canvasRef = useRef<HTMLCanvasElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  // Load design data if coming from designer page
  useEffect(() => {
    if (designIdParam) {
      // TODO: Fetch design data from API
      // For now, we'll let users upload jewelry photo manually
    }
  }, [designIdParam])

  const generateAITryOnMutation = useMutation({
    mutationFn: tryonAPI.generateAITryOn,
    onSuccess: (data) => {
      console.log('✅ Mutation success callback triggered')
      console.log('📦 Response data:', data)

      if (data.detection_result) {
        console.log('🔍 Detection result:', {
          bodyPart: data.detection_result.primary_body_part,
          placement: data.detection_result.recommended_placement_area,
          confidence: data.detection_result.confidence
        })
      }

      if (data.result_url) {
        console.log('🖼️  Result URL:', data.result_url)
      }

      setTryOnResult(data)
      setDetectionResult(data.detection_result)
      toast.success('AI Try-On generated successfully!')
    },
    onError: (error: any) => {
      console.error('❌ Mutation error callback triggered')
      console.error('🔴 Error object:', error)
      console.error('📝 Error message:', error.message)
      console.error('📋 Error details:', error)
      // Check if it's a trial limit error
      if (error.response?.status === 402) {
        setShowWaitlist(true)
        return
      }
      // Show friendly generic error
      toast.error('Oops! Something went wrong. Please try again.')
    },
  })

  const handleBodyPhotoUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      if (file.size > 10 * 1024 * 1024) {
        toast.error('File too large (max 10MB)')
        return
      }

      // Show loading toast
      const loadingToast = toast.loading('Compressing image...')

      try {
        // Compress image before setting
        const compressedFile = await compressImage(file, {
          maxSizeMB: 0.4, // 400KB max
          maxWidthOrHeight: 1920,
          quality: 0.85,
        })

        setBodyPhoto(compressedFile)

        // Create preview
        const reader = new FileReader()
        reader.onload = (e) => {
          setBodyPhotoPreview(e.target?.result as string)
        }
        reader.readAsDataURL(compressedFile)

        toast.success(`Body photo uploaded! (${(compressedFile.size / 1024).toFixed(0)} KB)`, {
          id: loadingToast,
        })
      } catch (error) {
        console.error('Compression error:', error)
        toast.error('Failed to compress image', { id: loadingToast })
      }
    }
  }

  const handleJewelryPhotoUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      if (file.size > 10 * 1024 * 1024) {
        toast.error('File too large (max 10MB)')
        return
      }

      // Show loading toast
      const loadingToast = toast.loading('Compressing image...')

      try {
        // Compress image before setting
        const compressedFile = await compressImage(file, {
          maxSizeMB: 0.4, // 400KB max
          maxWidthOrHeight: 1920,
          quality: 0.85,
        })

        setJewelryPhoto(compressedFile)

        // Create preview
        const reader = new FileReader()
        reader.onload = (e) => {
          setJewelryPhotoPreview(e.target?.result as string)
        }
        reader.readAsDataURL(compressedFile)

        toast.success(`Jewelry photo uploaded! (${(compressedFile.size / 1024).toFixed(0)} KB)`, {
          id: loadingToast,
        })
      } catch (error) {
        console.error('Compression error:', error)
        toast.error('Failed to compress image', { id: loadingToast })
      }
    }
  }

  const handleGenerateAITryOn = async () => {
    console.log('🎨 ============================================================')
    console.log('🎨 STARTING VIRTUAL TRY-ON GENERATION')
    console.log('🎨 ============================================================')

    if (!bodyPhoto || !jewelryPhoto) {
      console.error('❌ Missing required photos')
      toast.error('Please upload both photos')
      return
    }

    console.log('📸 Body photo:', bodyPhoto.name, `(${(bodyPhoto.size / 1024).toFixed(2)} KB)`)
    console.log('💍 Jewelry photo:', jewelryPhoto.name, `(${(jewelryPhoto.size / 1024).toFixed(2)} KB)`)
    console.log('📋 Jewelry type:', jewelryType)
    console.log('📝 Description:', jewelryDescription || '(none provided)')
    console.log('🎯 Auto-detect: enabled')
    console.log('📚 Use examples: enabled')
    console.log('⏳ Sending request to backend...')

    try {
      const result = await generateAITryOnMutation.mutateAsync({
        bodyPhoto,
        jewelryPhoto,
        jewelryType,
        jewelryDescription,
        autoDetect: true,
        useExamples: true,
      })

      console.log('✅ Try-on generation successful!')
      console.log('📊 Result:', result)
      console.log('🎨 ============================================================')
    } catch (error) {
      console.error('❌ ============================================================')
      console.error('❌ TRY-ON GENERATION FAILED')
      console.error('💥 Error:', error)
      console.error('❌ ============================================================')
    }
  }

  const handleOverlayUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      const reader = new FileReader()
      reader.onload = (e) => {
        setOverlayImage(e.target?.result as string)
      }
      reader.readAsDataURL(file)
    }
  }

  const handleCanvasMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    setIsDragging(true)
    const rect = canvasRef.current?.getBoundingClientRect()
    if (rect) {
      setDragStart({
        x: e.clientX - rect.left - transform.x,
        y: e.clientY - rect.top - transform.y,
      })
    }
  }

  const handleCanvasMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDragging) return
    const rect = canvasRef.current?.getBoundingClientRect()
    if (rect) {
      setTransform({
        ...transform,
        x: e.clientX - rect.left - dragStart.x,
        y: e.clientY - rect.top - dragStart.y,
      })
    }
  }

  const handleCanvasMouseUp = () => {
    setIsDragging(false)
  }

  const handleWheel = (e: React.WheelEvent<HTMLCanvasElement>) => {
    e.preventDefault()
    const delta = e.deltaY > 0 ? -0.1 : 0.1
    setTransform({
      ...transform,
      scale: Math.max(0.1, Math.min(3, transform.scale + delta)),
    })
  }

  useEffect(() => {
    // Render canvas for manual overlay mode (legacy)
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    ctx.clearRect(0, 0, canvas.width, canvas.height)

    if (bodyPhotoPreview) {
      const img = new window.Image()
      img.src = bodyPhotoPreview
      img.onload = () => {
        canvas.width = img.width
        canvas.height = img.height
        ctx.drawImage(img, 0, 0)

        if (overlayImage) {
          const overlay = new window.Image()
          overlay.src = overlayImage
          overlay.onload = () => {
            ctx.save()
            ctx.translate(transform.x, transform.y)
            ctx.rotate((transform.rotation * Math.PI) / 180)
            ctx.scale(transform.scale, transform.scale)
            ctx.globalAlpha = transform.opacity

            const overlayWidth = overlay.width
            const overlayHeight = overlay.height
            ctx.drawImage(overlay, -overlayWidth / 2, -overlayHeight / 2, overlayWidth, overlayHeight)

            ctx.restore()
          }
        }
      }
    }
  }, [bodyPhotoPreview, overlayImage, transform])

  const handleSaveSnapshot = async () => {
    const canvas = canvasRef.current
    if (!canvas) return

    canvas.toBlob((blob) => {
      if (blob) {
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = 'tryon-snapshot.png'
        a.click()
        toast.success('Snapshot saved!')
      }
    })
  }

  const handleReset = () => {
    setTransform({
      x: 50,
      y: 50,
      scale: 1,
      rotation: 0,
      opacity: 1,
      hue: 0,
    })
  }

  const handleFingerPreset = (finger: FingerType) => {
    setFingerType(finger)
    // Simple preset positions based on finger type
    const presets = {
      index: { x: 30, y: 40 },
      middle: { x: 45, y: 35 },
      ring: { x: 60, y: 40 },
      little: { x: 75, y: 50 },
    }
    const preset = presets[finger]
    setTransform({
      ...transform,
      x: (canvasRef.current?.width || 500) * (preset.x / 100),
      y: (canvasRef.current?.height || 500) * (preset.y / 100),
    })
  }

  return (
    <ProtectedRoute>
      <Navbar />
      <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-4">
        <TrialCounter feature="virtual_tryon" featureName="Virtual Try-On" />
      </div>

      {/* Info Banner */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border-b border-blue-200">
        <div className="container mx-auto px-4 py-3">
          <div className="flex items-start space-x-3">
            <Info className="h-5 w-5 text-blue-600 mt-0.5 flex-shrink-0" />
            <div className="text-sm text-blue-900">
              <strong className="font-semibold">Smart Auto-Detection:</strong> Upload ANY body photo and our AI will automatically detect the right placement for your jewelry.
              <div className="mt-1 flex flex-wrap gap-x-4 text-blue-700">
                <span>• Hand → Rings & Bracelets</span>
                <span>• Neck → Necklaces</span>
                <span>• Ear → Earrings</span>
                <span>• Full Body → AI Decides</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8">
        <div className="grid gap-8 lg:grid-cols-3">
          {/* Left Sidebar - AI Try-On Controls */}
          <div className="lg:col-span-1 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Sparkles className="mr-2 h-5 w-5 text-primary-600" />
                  AI Try-On Setup
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {/* Upload Body Photo */}
                  <div>
                    <label className="mb-2 block text-sm font-medium text-gray-700">
                      Your Photo <span className="text-gray-500">(Hand, Neck, Full Body, Ear)</span>
                    </label>
                    <div className="flex flex-col gap-2">
                      <input
                        type="file"
                        accept="image/*"
                        onChange={handleBodyPhotoUpload}
                        className="hidden"
                        id="body-upload"
                      />
                      <label htmlFor="body-upload">
                        <Button
                          as="span"
                          variant="outline"
                          size="sm"
                          className="w-full cursor-pointer"
                        >
                          <Upload className="mr-2 h-4 w-4" />
                          {bodyPhoto ? 'Change Photo' : 'Upload Any Photo'}
                        </Button>
                      </label>
                      {bodyPhotoPreview && (
                        <div className="mt-2 rounded-lg overflow-hidden border-2 border-green-500">
                          <img src={bodyPhotoPreview} alt="Your photo" className="w-full h-32 object-cover" />
                          <div className="bg-green-50 px-2 py-1 text-xs text-green-700 flex items-center">
                            <CheckCircle2 className="h-3 w-3 mr-1" />
                            Photo uploaded
                          </div>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Upload Jewelry Photo */}
                  <div>
                    <label className="mb-2 block text-sm font-medium text-gray-700">
                      Jewelry Image
                    </label>
                    <div className="flex flex-col gap-2">
                      <input
                        type="file"
                        accept="image/*"
                        onChange={handleJewelryPhotoUpload}
                        className="hidden"
                        id="jewelry-upload"
                      />
                      <label htmlFor="jewelry-upload">
                        <Button
                          as="span"
                          variant="outline"
                          size="sm"
                          className="w-full cursor-pointer"
                        >
                          <ImageIcon className="mr-2 h-4 w-4" />
                          {jewelryPhoto ? 'Change Jewelry' : 'Upload Jewelry'}
                        </Button>
                      </label>
                      {jewelryPhotoPreview && (
                        <div className="mt-2 rounded-lg overflow-hidden border-2 border-green-500">
                          <img src={jewelryPhotoPreview} alt="Jewelry" className="w-full h-32 object-cover bg-gray-100" />
                          <div className="bg-green-50 px-2 py-1 text-xs text-green-700 flex items-center">
                            <CheckCircle2 className="h-3 w-3 mr-1" />
                            Jewelry uploaded
                          </div>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Jewelry Type */}
                  <div>
                    <label className="mb-2 block text-sm font-medium text-gray-700">
                      Jewelry Type
                    </label>
                    <select
                      value={jewelryType}
                      onChange={(e) => setJewelryType(e.target.value)}
                      className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                    >
                      <option value="ring">Ring</option>
                      <option value="bracelet">Bracelet</option>
                      <option value="necklace">Necklace</option>
                      <option value="earring">Earring</option>
                    </select>
                  </div>

                  {/* Generate Button */}
                  <Button
                    variant="primary"
                    size="md"
                    onClick={handleGenerateAITryOn}
                    className="w-full bg-gradient-to-r from-primary-600 to-primary-700"
                    disabled={!bodyPhoto || !jewelryPhoto}
                    isLoading={generateAITryOnMutation.isPending}
                  >
                    <Sparkles className="mr-2 h-4 w-4" />
                    Generate AI Try-On
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Detection Results Card */}
            {detectionResult && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">Auto-Detection Results</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div>
                      <div className="text-xs font-medium text-gray-500 mb-1">Detected Body Part</div>
                      <div className="text-sm font-semibold text-gray-900 capitalize">
                        {detectionResult.primary_body_part || 'Unknown'}
                      </div>
                    </div>

                    <div>
                      <div className="text-xs font-medium text-gray-500 mb-1">Placement Area</div>
                      <div className="text-sm font-semibold text-gray-900 capitalize">
                        {detectionResult.recommended_placement_area || 'Not specified'}
                      </div>
                    </div>

                    <div>
                      <div className="text-xs font-medium text-gray-500 mb-1">Confidence</div>
                      <div className="flex items-center space-x-2">
                        <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-green-500"
                            style={{ width: `${(detectionResult.confidence || 0) * 100}%` }}
                          />
                        </div>
                        <span className="text-sm font-semibold">
                          {((detectionResult.confidence || 0) * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>

                    {detectionResult.ai_recommendation && (
                      <div className="mt-3 p-3 bg-blue-50 rounded-md">
                        <div className="text-xs font-medium text-blue-900 mb-1">AI Recommendation</div>
                        <div className="text-xs text-blue-700">
                          {detectionResult.ai_recommendation}
                        </div>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            )}

          </div>

          {/* Right Content - AI Try-On Result */}
          <div className="lg:col-span-2">
            <Card>
              <CardContent>
                {!tryOnResult ? (
                  <div className="flex h-96 items-center justify-center rounded-lg border-2 border-dashed border-gray-300 bg-gradient-to-br from-gray-50 to-blue-50">
                    <div className="text-center max-w-md">
                      <Sparkles className="mx-auto h-16 w-16 text-primary-500" />
                      <h3 className="mt-4 text-lg font-medium text-gray-900">
                        AI-Powered Virtual Try-On
                      </h3>
                      <p className="mt-2 text-sm text-gray-600">
                        Upload any body photo (hand, neck, full body, or ear) and jewelry image to get started
                      </p>
                      <div className="mt-6 grid grid-cols-2 gap-4 text-xs text-gray-500">
                        <div className="flex items-start space-x-2">
                          <CheckCircle2 className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                          <span className="text-left">Auto-detects body parts</span>
                        </div>
                        <div className="flex items-start space-x-2">
                          <CheckCircle2 className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                          <span className="text-left">Smart jewelry placement</span>
                        </div>
                        <div className="flex items-start space-x-2">
                          <CheckCircle2 className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                          <span className="text-left">Works with any angle</span>
                        </div>
                        <div className="flex items-start space-x-2">
                          <CheckCircle2 className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                          <span className="text-left">Photorealistic results</span>
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {/* AI Generated Result */}
                    <div className="relative rounded-lg overflow-hidden bg-gray-100">
                      <img
                        src={
                          tryOnResult.result_url?.startsWith('http')
                            ? tryOnResult.result_url
                            : `${getApiUrl()}${tryOnResult.result_url || tryOnResult.composite_url}`
                        }
                        alt="AI Try-On Result"
                        className="w-full max-h-[600px] object-contain"
                      />

                      {/* Success Badge */}
                      <div className="absolute top-4 right-4 bg-green-500 text-white px-3 py-1 rounded-full text-xs font-semibold flex items-center shadow-lg">
                        <CheckCircle2 className="h-3 w-3 mr-1" />
                        AI Generated
                      </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex items-center justify-between">
                      <div className="flex space-x-2">
                        <Button
                          variant="primary"
                          size="sm"
                          onClick={() => {
                            const link = document.createElement('a')
                            const url = tryOnResult.result_url || tryOnResult.composite_url
                            link.href = url?.startsWith('http') ? url : `${getApiUrl()}${url}`
                            link.download = 'ai-tryon-result.jpg'
                            link.click()
                            toast.success('Downloaded!')
                          }}
                        >
                          <Download className="mr-2 h-4 w-4" />
                          Download
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            setTryOnResult(null)
                            setDetectionResult(null)
                            setBodyPhoto(null)
                            setBodyPhotoPreview(null)
                            setJewelryPhoto(null)
                            setJewelryPhotoPreview(null)
                            setJewelryDescription('')
                          }}
                        >
                          <RotateCw className="mr-2 h-4 w-4" />
                          Try Another
                        </Button>
                      </div>

                      <div className="text-xs text-gray-500">
                        Powered by Google Gemini Imagen 3 🍌
                      </div>
                    </div>

                    {/* Metadata */}
                    {tryOnResult.metadata && (
                      <div className="p-4 bg-gray-50 rounded-lg text-xs text-gray-600">
                        <div className="font-medium text-gray-700 mb-2">Generation Details</div>
                        <div className="grid grid-cols-2 gap-2">
                          {tryOnResult.metadata.generation_time && (
                            <div>
                              <span className="font-medium">Time:</span> {tryOnResult.metadata.generation_time}s
                            </div>
                          )}
                          {tryOnResult.metadata.model && (
                            <div>
                              <span className="font-medium">Model:</span> {tryOnResult.metadata.model}
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Manual Canvas (Legacy - Hidden unless overlay uploaded) */}
                {!tryOnResult && overlayImage && bodyPhotoPreview && (
                  <div className="mt-8 pt-8 border-t">
                    <h4 className="text-sm font-medium text-gray-700 mb-4">Manual Overlay Preview</h4>
                    <div className="space-y-4">
                      <div
                        ref={containerRef}
                        className="relative overflow-hidden rounded-lg bg-gray-100"
                      >
                        <canvas
                          ref={canvasRef}
                          onMouseDown={handleCanvasMouseDown}
                          onMouseMove={handleCanvasMouseMove}
                          onMouseUp={handleCanvasMouseUp}
                          onMouseLeave={handleCanvasMouseUp}
                          onWheel={handleWheel}
                          className="max-h-[400px] w-full cursor-move"
                        />
                      </div>

                      {/* Transform Info */}
                      {overlayImage && (
                        <div className="flex items-center justify-between text-xs text-gray-600">
                          <div className="flex items-center space-x-4">
                            <span className="flex items-center">
                              <Move className="mr-1 h-3 w-3" />
                              X: {transform.x.toFixed(0)}, Y: {transform.y.toFixed(0)}
                            </span>
                            <span className="flex items-center">
                              <ZoomIn className="mr-1 h-3 w-3" />
                              {(transform.scale * 100).toFixed(0)}%
                            </span>
                            <span className="flex items-center">
                              <RotateCw className="mr-1 h-3 w-3" />
                              {transform.rotation}°
                            </span>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
      </div>

      <WaitlistModal
        isOpen={showWaitlist}
        onClose={() => setShowWaitlist(false)}
        feature="Virtual Try-On"
      />
    </ProtectedRoute>
  )
}

export default function TryOnPage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center">Loading...</div>}>
      <TryOnContent />
    </Suspense>
  )
}
