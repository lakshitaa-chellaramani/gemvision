'use client'

import { useState, useEffect } from 'react'
import { useMutation } from '@tanstack/react-query'
import { designerAPI } from '@/lib/api'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { Textarea } from '@/components/ui/Textarea'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Sparkles, Download, Heart, Share2, RefreshCw, Loader2, Wand2, Gem, Palette, Box, X } from 'lucide-react'
import Image from 'next/image'
import toast from 'react-hot-toast'
import type { GenerateDesignResponse, JewelleryCategory, StylePreset, RealismMode, Model3DResult } from '@/types'
import { Model3DViewer } from '@/components/Model3DViewer'
import ProtectedRoute from '@/components/ProtectedRoute'
import Navbar from '@/components/Navbar'
import WaitlistModal from '@/components/auth/WaitlistModal'
import TrialCounter from '@/components/auth/TrialCounter'

const CATEGORIES: { value: JewelleryCategory; label: string }[] = [
  { value: 'ring', label: 'Ring' },
  { value: 'necklace', label: 'Necklace' },
  { value: 'earring', label: 'Earring' },
  { value: 'bracelet', label: 'Bracelet' },
]

const STYLES: { value: StylePreset; label: string }[] = [
  { value: 'bridal', label: 'Bridal' },
  { value: 'minimalist', label: 'Minimalist' },
  { value: 'traditional', label: 'Traditional' },
  { value: 'antique', label: 'Antique' },
  { value: 'heavy-stone', label: 'Heavy Stone' },
]

const REALISM_MODES: { value: RealismMode; label: string }[] = [
  { value: 'realistic', label: 'Realistic' },
  { value: 'photoreal', label: 'Photoreal' },
  { value: 'cad', label: 'CAD/Blueprint' },
  { value: 'sketch', label: 'Hand Sketch' },
]

const METAL_TYPES = [
  { value: 'white-gold', label: 'White Gold' },
  { value: 'yellow-gold', label: 'Yellow Gold' },
  { value: 'rose-gold', label: 'Rose Gold' },
  { value: 'platinum', label: 'Platinum' },
  { value: 'silver', label: 'Sterling Silver' },
  { value: 'mixed', label: 'Mixed Metals' },
]

const GEMSTONE_TYPES = [
  { value: 'diamond', label: 'Diamond' },
  { value: 'ruby', label: 'Ruby' },
  { value: 'sapphire', label: 'Sapphire' },
  { value: 'emerald', label: 'Emerald' },
  { value: 'amethyst', label: 'Amethyst' },
  { value: 'topaz', label: 'Topaz' },
  { value: 'pearl', label: 'Pearl' },
  { value: 'mixed', label: 'Mixed Gemstones' },
  { value: 'none', label: 'No Gemstones' },
]

const FINISH_TYPES = [
  { value: 'polished', label: 'High Polish' },
  { value: 'matte', label: 'Matte' },
  { value: 'brushed', label: 'Brushed' },
  { value: 'hammered', label: 'Hammered' },
  { value: 'satin', label: 'Satin' },
  { value: 'mixed', label: 'Mixed Finish' },
]

const SETTING_STYLES = [
  { value: 'prong', label: 'Prong Setting' },
  { value: 'bezel', label: 'Bezel Setting' },
  { value: 'pave', label: 'Pavé Setting' },
  { value: 'channel', label: 'Channel Setting' },
  { value: 'halo', label: 'Halo Setting' },
  { value: 'tension', label: 'Tension Setting' },
]

const LOADING_MESSAGES = [
  "✨ Creating magic...",
  "💎 Polishing virtual gemstones...",
  "🎨 Mixing precious metals...",
  "⚡ Channeling creative energy...",
  "🔮 Consulting the design oracle...",
  "🌟 Crafting perfection...",
  "💫 Weaving brilliance...",
  "🎭 Bringing your vision to life...",
]

const LOADING_3D_MESSAGES = [
  "🔨 Forging 3D geometry...",
  "📐 Calculating vertices and faces...",
  "🎯 Sculpting the model...",
  "✨ Rendering mesh topology...",
  "🔧 Building polygons...",
  "🌐 Generating 3D structure...",
  "💫 Creating depth and volume...",
  "🎨 Applying textures and materials...",
]

const TIPS = [
  "💡 Tip: Be specific about materials for better results",
  "💡 Tip: Try different realism modes for unique styles",
  "💡 Tip: Combine multiple gemstones for exotic designs",
  "💡 Tip: Use the refine button to iterate on designs you like",
  "💡 Tip: Save your favorite designs to compare later",
]

const TIPS_3D = [
  "💡 Tip: 3D models are perfect for 3D printing jewelry prototypes",
  "💡 Tip: GLB format works best for web viewing and AR",
  "💡 Tip: You can import the model into Blender for editing",
  "💡 Tip: Use the 3D model for manufacturing and CAD workflows",
  "💡 Tip: Share your 3D models on platforms like Sketchfab",
]

const TEMPLATE_PROMPTS: Record<string, string[]> = {
  'ring-bridal': [
    'Solitaire engagement ring with round brilliant diamond, thin pavé band, 18k white gold',
    'Halo engagement ring with cushion cut center diamond, rose gold band with micro pavé',
    'Three-stone engagement ring with emerald cut center, platinum setting',
  ],
  'ring-minimalist': [
    'Simple solitaire ring with round diamond, thin polished band, 14k yellow gold',
    'Bezel set diamond ring, sleek modern design, brushed finish',
    'Thin band with single floating diamond, minimal setting',
  ],
  'necklace-bridal': [
    'Diamond pendant necklace with teardrop design, delicate chain, white gold',
    'Solitaire diamond pendant, classic round cut, simple chain, platinum',
    'Halo pendant necklace with pear-shaped diamond, micro pavé halo',
  ],
}

export default function DesignerPage() {
  const [prompt, setPrompt] = useState('')
  const [category, setCategory] = useState<JewelleryCategory>('ring')
  const [stylePreset, setStylePreset] = useState<StylePreset>('bridal')
  const [realismMode, setRealismMode] = useState<RealismMode>('realistic')
  const [result, setResult] = useState<GenerateDesignResponse | null>(null)
  const [showWaitlist, setShowWaitlist] = useState(false)

  // Advanced options
  const [metalType, setMetalType] = useState('white-gold')
  const [gemstoneType, setGemstoneType] = useState('diamond')
  const [finishType, setFinishType] = useState('polished')
  const [settingStyle, setSettingStyle] = useState('prong')
  const [showAdvanced, setShowAdvanced] = useState(false)

  // Loading animation state
  const [loadingMessage, setLoadingMessage] = useState(LOADING_MESSAGES[0])
  const [currentTip, setCurrentTip] = useState(TIPS[0])
  const [progress, setProgress] = useState(0)

  // 3D Loading animation state
  const [loading3DMessage, setLoading3DMessage] = useState(LOADING_3D_MESSAGES[0])
  const [current3DTip, setCurrent3DTip] = useState(TIPS_3D[0])
  const [progress3D, setProgress3D] = useState(0)

  // 3D Model state
  const [model3D, setModel3D] = useState<Model3DResult | null>(null)
  const [show3DModal, setShow3DModal] = useState(false)

  // Mutations - must be declared before useEffect
  const generateMutation = useMutation({
    mutationFn: designerAPI.generate,
    onSuccess: (data) => {
      setResult(data)
      setProgress(100)
      toast.success('Design generated successfully! 🎉')
    },
    onError: (error: any) => {
      setProgress(0)
      // Check if it's a trial limit error
      if (error.response?.status === 402) {
        setShowWaitlist(true)
        return
      }
      // Show friendly generic error
      toast.error('Oops! Something went wrong. Please try again.')
    },
  })

  const saveIdeaMutation = useMutation({
    mutationFn: (designId: number) => designerAPI.saveAsIdea(designId, false),
    onSuccess: () => {
      toast.success('Design saved as idea! ❤️')
    },
  })

  const generate3DMutation = useMutation({
    mutationFn: async (imageUrl: string) => {
      // Pass URL directly to backend - backend will fetch it server-side (avoids CORS)
      return designerAPI.generate3D(imageUrl, true, 'glb')
    },
    onSuccess: (data: Model3DResult) => {
      setModel3D(data)
      setShow3DModal(true)
      toast.success('3D model generated successfully! 🎉')
    },
    onError: (error: any) => {
      // Check if it's a trial limit error
      if (error.response?.status === 402) {
        setShowWaitlist(true)
        return
      }
      // Show friendly generic error
      toast.error('Oops! Something went wrong. Please try again.')
    },
  })

  // Rotate loading messages and tips
  useEffect(() => {
    if (generateMutation.isPending) {
      const messageInterval = setInterval(() => {
        setLoadingMessage(LOADING_MESSAGES[Math.floor(Math.random() * LOADING_MESSAGES.length)])
      }, 2000)

      const tipInterval = setInterval(() => {
        setCurrentTip(TIPS[Math.floor(Math.random() * TIPS.length)])
      }, 4000)

      // Simulate progress
      setProgress(0)
      const progressInterval = setInterval(() => {
        setProgress(prev => {
          if (prev >= 90) return prev
          return prev + Math.random() * 15
        })
      }, 500)

      return () => {
        clearInterval(messageInterval)
        clearInterval(tipInterval)
        clearInterval(progressInterval)
      }
    } else {
      setProgress(100)
    }
  }, [generateMutation.isPending])

  // Rotate 3D loading messages and tips
  useEffect(() => {
    if (generate3DMutation.isPending) {
      const messageInterval = setInterval(() => {
        setLoading3DMessage(LOADING_3D_MESSAGES[Math.floor(Math.random() * LOADING_3D_MESSAGES.length)])
      }, 2500)

      const tipInterval = setInterval(() => {
        setCurrent3DTip(TIPS_3D[Math.floor(Math.random() * TIPS_3D.length)])
      }, 5000)

      // Simulate progress for 3D generation (slower)
      setProgress3D(0)
      const progressInterval = setInterval(() => {
        setProgress3D(prev => {
          if (prev >= 85) return prev
          return prev + Math.random() * 8
        })
      }, 800)

      return () => {
        clearInterval(messageInterval)
        clearInterval(tipInterval)
        clearInterval(progressInterval)
      }
    } else {
      setProgress3D(100)
    }
  }, [generate3DMutation.isPending])

  const handleGenerate = () => {
    if (!prompt.trim()) {
      toast.error('Please enter a prompt')
      return
    }

    // Build enhanced prompt with advanced options
    let enhancedPrompt = prompt

    if (showAdvanced) {
      const metalLabel = METAL_TYPES.find(m => m.value === metalType)?.label
      const gemLabel = GEMSTONE_TYPES.find(g => g.value === gemstoneType)?.label
      const finishLabel = FINISH_TYPES.find(f => f.value === finishType)?.label

      if (metalLabel && !prompt.toLowerCase().includes('gold') && !prompt.toLowerCase().includes('platinum')) {
        enhancedPrompt += `, ${metalLabel}`
      }

      if (gemLabel && gemstoneType !== 'none' && !prompt.toLowerCase().includes(gemstoneType)) {
        enhancedPrompt += `, ${gemLabel}`
      }

      if (finishLabel && finishType !== 'polished') {
        enhancedPrompt += `, ${finishLabel} finish`
      }

      if (category === 'ring' && settingStyle) {
        const settingLabel = SETTING_STYLES.find(s => s.value === settingStyle)?.label
        if (settingLabel && !prompt.toLowerCase().includes('setting')) {
          enhancedPrompt += `, ${settingLabel}`
        }
      }
    }

    generateMutation.mutate({
      prompt: enhancedPrompt,
      category,
      style_preset: stylePreset,
      realism_mode: realismMode,
      num_images: 1,
    })
  }

  const handleDownload = async (imageUrl: string, index: number) => {
    try {
      // Try to fetch with CORS mode
      const response = await fetch(imageUrl, { mode: 'cors' })

      if (!response.ok) {
        throw new Error('Failed to fetch image')
      }

      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `gemvision-design-${result?.design_id || 'unknown'}-${index + 1}.png`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      toast.success('Image downloaded! 📥')
    } catch (error) {
      // Fallback: Try direct download link (works if same-origin or CORS headers allow)
      try {
        const a = document.createElement('a')
        a.href = imageUrl
        a.download = `gemvision-design-${result?.design_id || 'unknown'}-${index + 1}.png`
        a.target = '_blank'
        a.rel = 'noopener noreferrer'
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        toast.success('Opening image in new tab... Right-click to save! 📥')
      } catch (fallbackError) {
        // Final fallback: Open in new tab
        window.open(imageUrl, '_blank')
        // toast.info('Image opened in new tab. Right-click to save! 🖼️')
      }
    }
  }

  const handleShare = async () => {
    if (!result) return

    const shareData = {
      title: 'Check out this AI-generated jewellery design!',
      text: `Created with GemVision AI Designer - ${result.category} in ${result.style_preset} style`,
      url: window.location.href,
    }

    try {
      if (navigator.share && navigator.canShare(shareData)) {
        await navigator.share(shareData)
        toast.success('Shared successfully! 🎉')
      } else {
        // Fallback: copy to clipboard
        await navigator.clipboard.writeText(result.images[0].url)
        toast.success('Image URL copied to clipboard! 📋')
      }
    } catch (error) {
      // Copy to clipboard as final fallback
      try {
        await navigator.clipboard.writeText(result.images[0].url)
        toast.success('Image URL copied to clipboard! 📋')
      } catch {
        toast.error('Failed to share')
      }
    }
  }

  const handleRefine = () => {
    if (!result) return

    // Keep the current prompt and settings but regenerate
    setPrompt(result.enhanced_prompt || result.prompt)
    window.scrollTo({ top: 0, behavior: 'smooth' })

    // Optionally auto-generate with slight variation
    toast.success('Ready to refine! Adjust parameters and click Generate 🎨')
  }

  const handleTemplateClick = (template: string) => {
    setPrompt(template)
  }

  const getTemplates = () => {
    const key = `${category}-${stylePreset}`
    return TEMPLATE_PROMPTS[key] || []
  }

  return (
    <ProtectedRoute>
      <Navbar />
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      <div className="container mx-auto px-4 py-4">
        <TrialCounter feature="ai_designer" featureName="AI Jewelry Designer" />
      </div>

      <div className="container mx-auto px-4 py-8">
        <div className="grid gap-8 lg:grid-cols-3">
          {/* Left Sidebar - Form */}
          <div className="lg:col-span-1">
            <Card className="sticky top-4">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Wand2 className="h-5 w-5" />
                  Design Parameters
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {/* Category */}
                  <Select
                    label="Category"
                    value={category}
                    onChange={(e) => setCategory(e.target.value as JewelleryCategory)}
                    options={CATEGORIES}
                  />

                  {/* Style Preset */}
                  <Select
                    label="Style Preset"
                    value={stylePreset}
                    onChange={(e) => setStylePreset(e.target.value as StylePreset)}
                    options={STYLES}
                  />

                  {/* Realism Mode */}
                  <Select
                    label="Realism Mode"
                    value={realismMode}
                    onChange={(e) => setRealismMode(e.target.value as RealismMode)}
                    options={REALISM_MODES}
                  />

                  {/* Advanced Options Toggle */}
                  <button
                    onClick={() => setShowAdvanced(!showAdvanced)}
                    className="flex w-full items-center justify-between rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
                  >
                    <span className="flex items-center gap-2">
                      <Gem className="h-4 w-4" />
                      Advanced Options
                    </span>
                    <span className="text-xs text-gray-500">
                      {showAdvanced ? '▼' : '▶'}
                    </span>
                  </button>

                  {/* Advanced Options */}
                  {showAdvanced && (
                    <div className="space-y-4 rounded-lg border border-primary-200 bg-primary-50/50 p-4">
                      <Select
                        label="Metal Type"
                        value={metalType}
                        onChange={(e) => setMetalType(e.target.value)}
                        options={METAL_TYPES}
                      />

                      <Select
                        label="Gemstone"
                        value={gemstoneType}
                        onChange={(e) => setGemstoneType(e.target.value)}
                        options={GEMSTONE_TYPES}
                      />

                      <Select
                        label="Finish"
                        value={finishType}
                        onChange={(e) => setFinishType(e.target.value)}
                        options={FINISH_TYPES}
                      />

                      {category === 'ring' && (
                        <Select
                          label="Setting Style"
                          value={settingStyle}
                          onChange={(e) => setSettingStyle(e.target.value)}
                          options={SETTING_STYLES}
                        />
                      )}
                    </div>
                  )}

                  {/* Prompt */}
                  <Textarea
                    label="Design Prompt"
                    placeholder="e.g., 'Elegant solitaire ring with round brilliant diamond, thin pavé band, 18k white gold'"
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    rows={4}
                  />

                  {/* Template Prompts */}
                  {getTemplates().length > 0 && (
                    <div>
                      <label className="mb-2 block text-sm font-medium text-gray-700">
                        Template Prompts
                      </label>
                      <div className="space-y-2">
                        {getTemplates().map((template, idx) => (
                          <button
                            key={idx}
                            onClick={() => handleTemplateClick(template)}
                            className="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-left text-sm transition-colors hover:border-primary-500 hover:bg-primary-50"
                          >
                            {template}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Generate Button */}
                  <Button
                    variant="primary"
                    size="lg"
                    onClick={handleGenerate}
                    isLoading={generateMutation.isPending}
                    disabled={generateMutation.isPending}
                    className="w-full"
                  >
                    {generateMutation.isPending ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Generating...
                      </>
                    ) : (
                      <>
                        <Sparkles className="mr-2 h-4 w-4" />
                        Generate Design
                      </>
                    )}
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Right Content - Results */}
          <div className="lg:col-span-2">
            {generateMutation.isPending ? (
              /* Loading State */
              <Card className="overflow-hidden">
                <CardContent className="p-8">
                  <div className="flex flex-col items-center justify-center space-y-6">
                    {/* Animated Sparkles */}
                    <div className="relative">
                      <div className="absolute -inset-4 animate-pulse">
                        <Sparkles className="h-24 w-24 text-primary-200" />
                      </div>
                      <Sparkles className="relative h-16 w-16 animate-bounce text-primary-600" />
                    </div>

                    {/* Loading Message */}
                    <h3 className="text-2xl font-bold text-gray-900 animate-pulse">
                      {loadingMessage}
                    </h3>

                    {/* Progress Bar */}
                    <div className="w-full max-w-md">
                      <div className="h-2 overflow-hidden rounded-full bg-gray-200">
                        <div
                          className="h-full bg-gradient-to-r from-primary-500 to-primary-600 transition-all duration-500 ease-out"
                          style={{ width: `${progress}%` }}
                        />
                      </div>
                      <p className="mt-2 text-center text-sm text-gray-600">
                        {Math.round(progress)}%
                      </p>
                    </div>

                    {/* Tip */}
                    <div className="rounded-lg bg-primary-50 p-4 text-center">
                      <p className="text-sm text-primary-900">{currentTip}</p>
                    </div>

                    {/* Animated Gems */}
                    <div className="flex gap-4">
                      {[0, 1, 2].map((i) => (
                        <Gem
                          key={i}
                          className="h-8 w-8 animate-pulse text-primary-400"
                          style={{ animationDelay: `${i * 200}ms` }}
                        />
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ) : !result ? (
              /* Empty State */
              <Card className="flex h-96 items-center justify-center">
                <div className="text-center">
                  <div className="mx-auto mb-4 flex h-20 w-20 items-center justify-center rounded-full bg-primary-100">
                    <Palette className="h-10 w-10 text-primary-600" />
                  </div>
                  <h3 className="mt-4 text-lg font-medium text-gray-900">
                    No designs yet
                  </h3>
                  <p className="mt-2 text-sm text-gray-600">
                    Fill in the parameters and click Generate to create your first design
                  </p>
                </div>
              </Card>
            ) : (
              /* Results */
              <div className="space-y-6">
                {/* Main Image */}
                <Card>
                  <CardContent>
                    <div className="relative aspect-square overflow-hidden rounded-lg bg-gradient-to-br from-gray-100 to-gray-200">
                      <img
                        src={result.images[0].url}
                        alt="Generated design"
                        className="h-full w-full object-contain transition-transform hover:scale-105"
                      />
                    </div>

                    {/* Action Buttons */}
                    <div className="mt-4 flex flex-wrap gap-2">
                      <Button
                        variant="primary"
                        size="sm"
                        onClick={() => {
                          // Navigate to try-on page with design
                          window.location.href = `/tryon?design=${result.design_id}`
                        }}
                        className="bg-gradient-to-r from-primary-600 to-primary-700 hover:from-primary-700 hover:to-primary-800"
                      >
                        <Sparkles className="mr-2 h-4 w-4" />
                        Try It On
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDownload(result.images[0].url, 0)}
                      >
                        <Download className="mr-2 h-4 w-4" />
                        Download
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => saveIdeaMutation.mutate(result.design_id)}
                        isLoading={saveIdeaMutation.isPending}
                      >
                        <Heart className="mr-2 h-4 w-4" />
                        Save as Idea
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={handleShare}
                      >
                        <Share2 className="mr-2 h-4 w-4" />
                        Share
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={handleRefine}
                      >
                        <RefreshCw className="mr-2 h-4 w-4" />
                        Refine
                      </Button>
                      <Button
                        variant="primary"
                        size="sm"
                        onClick={() => generate3DMutation.mutate(result.images[0].url)}
                        isLoading={generate3DMutation.isPending}
                        disabled={generate3DMutation.isPending}
                        className="bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700"
                      >
                        {generate3DMutation.isPending ? (
                          <>
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            Generating 3D...
                          </>
                        ) : (
                          <>
                            <Box className="mr-2 h-4 w-4" />
                            Generate 3D Model
                          </>
                        )}
                      </Button>
                    </div>
                  </CardContent>
                </Card>

                {/* Metadata */}
                <Card>
                  <CardHeader>
                    <CardTitle>Design Details</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <dl className="space-y-3 text-sm">
                      <div className="flex justify-between rounded-lg bg-gray-50 p-3">
                        <dt className="font-medium text-gray-700">Category:</dt>
                        <dd className="text-gray-900 capitalize">{result.category}</dd>
                      </div>
                      <div className="flex justify-between rounded-lg bg-gray-50 p-3">
                        <dt className="font-medium text-gray-700">Style:</dt>
                        <dd className="text-gray-900 capitalize">{result.style_preset}</dd>
                      </div>
                      <div className="flex justify-between rounded-lg bg-gray-50 p-3">
                        <dt className="font-medium text-gray-700">Materials:</dt>
                        <dd className="text-gray-900">{result.materials.join(', ')}</dd>
                      </div>
                      <div className="flex justify-between rounded-lg bg-gray-50 p-3">
                        <dt className="font-medium text-gray-700">Colors:</dt>
                        <dd className="text-gray-900">{result.colors.join(', ')}</dd>
                      </div>
                      <div className="flex justify-between rounded-lg bg-gray-50 p-3">
                        <dt className="font-medium text-gray-700">Confidence:</dt>
                        <dd className="text-gray-900">
                          <div className="flex items-center gap-2">
                            <div className="h-2 w-24 overflow-hidden rounded-full bg-gray-200">
                              <div
                                className="h-full bg-green-500"
                                style={{ width: `${result.confidence * 100}%` }}
                              />
                            </div>
                            <span>{(result.confidence * 100).toFixed(1)}%</span>
                          </div>
                        </dd>
                      </div>
                      <div className="rounded-lg bg-primary-50 p-3">
                        <dt className="mb-2 font-medium text-gray-700">Prompt Used:</dt>
                        <dd className="text-sm italic text-gray-600">{result.enhanced_prompt}</dd>
                      </div>
                    </dl>
                  </CardContent>
                </Card>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 3D Generation Loading Modal */}
      {generate3DMutation.isPending && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <Card className="max-w-2xl w-full">
            <CardContent className="p-8">
              <div className="flex flex-col items-center justify-center space-y-6">
                {/* Animated 3D Box */}
                <div className="relative">
                  <div className="absolute -inset-4 animate-pulse">
                    <Box className="h-24 w-24 text-purple-200" />
                  </div>
                  <Box className="relative h-16 w-16 animate-bounce text-purple-600" style={{ animationDuration: '1.5s' }} />
                </div>

                {/* Loading Message */}
                <h3 className="text-2xl font-bold text-gray-900 animate-pulse">
                  {loading3DMessage}
                </h3>

                {/* Progress Bar */}
                <div className="w-full max-w-md">
                  <div className="h-3 overflow-hidden rounded-full bg-gray-200">
                    <div
                      className="h-full bg-gradient-to-r from-purple-500 via-indigo-500 to-purple-600 transition-all duration-500 ease-out animate-pulse"
                      style={{ width: `${progress3D}%` }}
                    />
                  </div>
                  <p className="mt-2 text-center text-sm text-gray-600">
                    {Math.round(progress3D)}% - This may take 1-3 minutes
                  </p>
                </div>

                {/* Tip */}
                <div className="rounded-lg bg-purple-50 p-4 text-center border border-purple-200">
                  <p className="text-sm text-purple-900">{current3DTip}</p>
                </div>

                {/* Animated Process Steps */}
                <div className="flex gap-4">
                  {[
                    { icon: '📤', label: 'Upload' },
                    { icon: '🔨', label: 'Process' },
                    { icon: '🎨', label: 'Render' },
                    { icon: '📥', label: 'Download' }
                  ].map((step, i) => (
                    <div
                      key={i}
                      className="flex flex-col items-center space-y-1"
                      style={{
                        animation: `pulse 2s ease-in-out ${i * 0.3}s infinite`
                      }}
                    >
                      <div className="text-3xl">{step.icon}</div>
                      <div className="text-xs text-gray-600">{step.label}</div>
                    </div>
                  ))}
                </div>

                {/* Info */}
                <div className="text-center text-sm text-gray-500">
                  <p>Creating high-quality 3D geometry...</p>
                  {/* <p className="text-xs mt-1">Powered by Tripo3D AI</p> */}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* 3D Model Modal */}
      {show3DModal && model3D && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <Card className="max-w-2xl w-full max-h-[90vh] overflow-auto">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <Box className="h-5 w-5" />
                  3D Model Generated
                </CardTitle>
                <button
                  onClick={() => setShow3DModal(false)}
                  className="rounded-full p-1 hover:bg-gray-100"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {/* 3D Model Viewer */}
                <div className="relative rounded-lg overflow-hidden bg-gradient-to-br from-gray-100 to-gray-200">
                  <Model3DViewer
                    modelUrl={model3D.model_url}
                    alt="Generated 3D Model"
                    autoRotate={true}
                    cameraControls={true}
                    className="min-h-[400px]"
                  />
                </div>

                {/* Model Stats */}
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div className="rounded-lg bg-gray-50 p-3">
                    <dt className="font-medium text-gray-700">Vertices:</dt>
                    <dd className="text-gray-900">{model3D.stats.vertices.toLocaleString()}</dd>
                  </div>
                  <div className="rounded-lg bg-gray-50 p-3">
                    <dt className="font-medium text-gray-700">Faces:</dt>
                    <dd className="text-gray-900">{model3D.stats.faces.toLocaleString()}</dd>
                  </div>
                  <div className="rounded-lg bg-gray-50 p-3">
                    <dt className="font-medium text-gray-700">Format:</dt>
                    <dd className="text-gray-900 uppercase">{model3D.format}</dd>
                  </div>
                  <div className="rounded-lg bg-gray-50 p-3">
                    <dt className="font-medium text-gray-700">File Size:</dt>
                    <dd className="text-gray-900">
                      {(model3D.file_size / 1024 / 1024).toFixed(2)} MB
                    </dd>
                  </div>
                  <div className="rounded-lg bg-gray-50 p-3">
                    <dt className="font-medium text-gray-700">Watertight:</dt>
                    <dd className="text-gray-900">
                      {model3D.stats.is_watertight ? '✓ Yes' : '✗ No'}
                    </dd>
                  </div>
                  <div className="rounded-lg bg-gray-50 p-3">
                    <dt className="font-medium text-gray-700">Surface Area:</dt>
                    <dd className="text-gray-900">
                      {model3D.stats.surface_area.toFixed(2)} units²
                    </dd>
                  </div>
                </div>

                {/* Download Button */}
                <div className="flex gap-2">
                  <Button
                    variant="primary"
                    className="flex-1"
                    onClick={() => {
                      const a = document.createElement('a')
                      a.href = model3D.model_url
                      a.download = `gemvision-3d-model-${model3D.generation_id}.${model3D.format}`
                      a.click()
                      toast.success('3D model downloaded! 📥')
                    }}
                  >
                    <Download className="mr-2 h-4 w-4" />
                    Download {model3D.format.toUpperCase()} Model
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => setShow3DModal(false)}
                  >
                    Close
                  </Button>
                </div>

                <div className="rounded-lg bg-blue-50 p-3 text-sm text-blue-900">
                  <p className="font-medium mb-1">💡 How to use your 3D model:</p>
                  <ul className="list-disc list-inside space-y-1 text-xs">
                    <li>Import into Blender, Maya, or 3D Studio Max for editing</li>
                    <li>Use for 3D printing or manufacturing</li>
                    <li>View in AR/VR applications</li>
                    <li>Upload to Sketchfab or other 3D sharing platforms</li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
      </div>

      <WaitlistModal
        isOpen={showWaitlist}
        onClose={() => setShowWaitlist(false)}
        feature="AI Jewelry Designer"
      />
    </ProtectedRoute>
  )
}
