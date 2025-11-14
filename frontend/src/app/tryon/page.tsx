'use client'

import { useState, useRef, useEffect } from 'react'
import { useMutation } from '@tanstack/react-query'
import { tryonAPI } from '@/lib/api'
import { Button } from '@/components/ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Eye, Upload, Download, Share2, RotateCw, Move, ZoomIn } from 'lucide-react'
import toast from 'react-hot-toast'
import type { TryOnTransform, FingerType } from '@/types'

const FINGER_TYPES: { value: FingerType; label: string }[] = [
  { value: 'index', label: 'Index Finger' },
  { value: 'middle', label: 'Middle Finger' },
  { value: 'ring', label: 'Ring Finger' },
  { value: 'little', label: 'Little Finger' },
]

export default function TryOnPage() {
  const [handPhoto, setHandPhoto] = useState<string | null>(null)
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

  const uploadHandPhotoMutation = useMutation({
    mutationFn: tryonAPI.uploadHandPhoto,
    onSuccess: (data) => {
      setHandPhoto(data.url)
      toast.success('Hand photo uploaded!')
    },
    onError: () => {
      toast.error('Failed to upload photo')
    },
  })

  const handleHandPhotoUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      if (file.size > 10 * 1024 * 1024) {
        toast.error('File too large (max 10MB)')
        return
      }
      uploadHandPhotoMutation.mutate(file)
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

  const renderCanvas = () => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    ctx.clearRect(0, 0, canvas.width, canvas.height)

    // Draw hand photo
    if (handPhoto) {
      const img = new window.Image()
      img.src = handPhoto
      img.onload = () => {
        canvas.width = img.width
        canvas.height = img.height
        ctx.drawImage(img, 0, 0)

        // Draw overlay
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
  }

  useEffect(() => {
    renderCanvas()
  }, [handPhoto, overlayImage, transform])

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
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="border-b bg-white">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center space-x-2">
            <Eye className="h-6 w-6 text-gold-600" />
            <h1 className="text-2xl font-bold text-gray-900">Virtual Try-On</h1>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        <div className="grid gap-8 lg:grid-cols-3">
          {/* Left Sidebar - Controls */}
          <div className="lg:col-span-1">
            <Card>
              <CardHeader>
                <CardTitle>Upload & Controls</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {/* Upload Hand Photo */}
                  <div>
                    <label className="mb-2 block text-sm font-medium text-gray-700">
                      Hand Photo
                    </label>
                    <div className="flex flex-col gap-2">
                      <input
                        type="file"
                        accept="image/*"
                        onChange={handleHandPhotoUpload}
                        className="hidden"
                        id="hand-upload"
                      />
                      <label htmlFor="hand-upload">
                        <Button
                          as="span"
                          variant="outline"
                          size="sm"
                          className="w-full cursor-pointer"
                          isLoading={uploadHandPhotoMutation.isPending}
                        >
                          <Upload className="mr-2 h-4 w-4" />
                          Upload Hand Photo
                        </Button>
                      </label>
                    </div>
                  </div>

                  {/* Upload Ring Overlay */}
                  <div>
                    <label className="mb-2 block text-sm font-medium text-gray-700">
                      Ring Overlay (PNG)
                    </label>
                    <div className="flex flex-col gap-2">
                      <input
                        type="file"
                        accept="image/png,image/*"
                        onChange={handleOverlayUpload}
                        className="hidden"
                        id="overlay-upload"
                      />
                      <label htmlFor="overlay-upload">
                        <Button
                          as="span"
                          variant="outline"
                          size="sm"
                          className="w-full cursor-pointer"
                        >
                          <Upload className="mr-2 h-4 w-4" />
                          Upload Ring Image
                        </Button>
                      </label>
                    </div>
                  </div>

                  {/* Finger Presets */}
                  <div>
                    <label className="mb-2 block text-sm font-medium text-gray-700">
                      Quick Position
                    </label>
                    <div className="grid grid-cols-2 gap-2">
                      {FINGER_TYPES.map((finger) => (
                        <Button
                          key={finger.value}
                          variant={fingerType === finger.value ? 'primary' : 'outline'}
                          size="sm"
                          onClick={() => handleFingerPreset(finger.value)}
                        >
                          {finger.label}
                        </Button>
                      ))}
                    </div>
                  </div>

                  <div className="border-t pt-4">
                    <h4 className="mb-3 font-medium text-gray-900">Transform Controls</h4>

                    {/* Scale */}
                    <div className="mb-3">
                      <label className="mb-1 block text-sm text-gray-700">
                        Scale: {transform.scale.toFixed(2)}x
                      </label>
                      <input
                        type="range"
                        min="0.1"
                        max="3"
                        step="0.1"
                        value={transform.scale}
                        onChange={(e) =>
                          setTransform({ ...transform, scale: Number(e.target.value) })
                        }
                        className="w-full"
                      />
                    </div>

                    {/* Rotation */}
                    <div className="mb-3">
                      <label className="mb-1 block text-sm text-gray-700">
                        Rotation: {transform.rotation}°
                      </label>
                      <input
                        type="range"
                        min="0"
                        max="360"
                        value={transform.rotation}
                        onChange={(e) =>
                          setTransform({ ...transform, rotation: Number(e.target.value) })
                        }
                        className="w-full"
                      />
                    </div>

                    {/* Opacity */}
                    <div className="mb-3">
                      <label className="mb-1 block text-sm text-gray-700">
                        Opacity: {(transform.opacity * 100).toFixed(0)}%
                      </label>
                      <input
                        type="range"
                        min="0"
                        max="1"
                        step="0.1"
                        value={transform.opacity}
                        onChange={(e) =>
                          setTransform({ ...transform, opacity: Number(e.target.value) })
                        }
                        className="w-full"
                      />
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="border-t pt-4 space-y-2">
                    <Button
                      variant="primary"
                      size="sm"
                      onClick={handleSaveSnapshot}
                      className="w-full"
                      disabled={!handPhoto || !overlayImage}
                    >
                      <Download className="mr-2 h-4 w-4" />
                      Save Snapshot
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleReset}
                      className="w-full"
                    >
                      <RotateCw className="mr-2 h-4 w-4" />
                      Reset Position
                    </Button>
                  </div>

                  {/* Instructions */}
                  <div className="rounded-md bg-blue-50 p-3 text-sm">
                    <h4 className="mb-2 font-medium text-blue-900">Instructions:</h4>
                    <ul className="space-y-1 text-blue-700">
                      <li>• Click & drag to move</li>
                      <li>• Scroll to zoom</li>
                      <li>• Use sliders for precise control</li>
                      <li>• Try finger presets for quick positioning</li>
                    </ul>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Right Content - Canvas */}
          <div className="lg:col-span-2">
            <Card>
              <CardContent>
                {!handPhoto ? (
                  <div className="flex h-96 items-center justify-center rounded-lg border-2 border-dashed border-gray-300 bg-gray-50">
                    <div className="text-center">
                      <Eye className="mx-auto h-16 w-16 text-gray-400" />
                      <h3 className="mt-4 text-lg font-medium text-gray-900">
                        Upload a hand photo to start
                      </h3>
                      <p className="mt-2 text-sm text-gray-600">
                        Take a photo of your hand or upload an existing one
                      </p>
                    </div>
                  </div>
                ) : (
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
                        className="max-h-[600px] w-full cursor-move"
                      />

                      {/* Overlay instructions */}
                      {handPhoto && !overlayImage && (
                        <div className="absolute inset-0 flex items-center justify-center bg-black/50">
                          <div className="rounded-lg bg-white p-6 text-center">
                            <Upload className="mx-auto h-12 w-12 text-primary-600" />
                            <h3 className="mt-2 text-lg font-medium">Upload a ring overlay</h3>
                            <p className="mt-1 text-sm text-gray-600">
                              Upload a PNG image of a ring to place it on your hand
                            </p>
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Transform Info */}
                    {overlayImage && (
                      <div className="flex items-center justify-between text-sm text-gray-600">
                        <div className="flex items-center space-x-4">
                          <span className="flex items-center">
                            <Move className="mr-1 h-4 w-4" />
                            X: {transform.x.toFixed(0)}, Y: {transform.y.toFixed(0)}
                          </span>
                          <span className="flex items-center">
                            <ZoomIn className="mr-1 h-4 w-4" />
                            {(transform.scale * 100).toFixed(0)}%
                          </span>
                          <span className="flex items-center">
                            <RotateCw className="mr-1 h-4 w-4" />
                            {transform.rotation}°
                          </span>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}
