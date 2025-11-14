'use client'

import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { designerAPI } from '@/lib/api'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { Textarea } from '@/components/ui/Textarea'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Sparkles, Download, Heart, Share2, RefreshCw } from 'lucide-react'
import Image from 'next/image'
import toast from 'react-hot-toast'
import type { GenerateDesignResponse, JewelleryCategory, StylePreset, RealismMode } from '@/types'

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
  const [numImages, setNumImages] = useState(4)
  const [result, setResult] = useState<GenerateDesignResponse | null>(null)
  const [selectedImage, setSelectedImage] = useState<number>(0)

  const generateMutation = useMutation({
    mutationFn: designerAPI.generate,
    onSuccess: (data) => {
      setResult(data)
      setSelectedImage(0)
      toast.success('Design generated successfully!')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to generate design')
    },
  })

  const saveIdeaMutation = useMutation({
    mutationFn: (designId: number) => designerAPI.saveAsIdea(designId, false),
    onSuccess: () => {
      toast.success('Design saved as idea!')
    },
  })

  const handleGenerate = () => {
    if (!prompt.trim()) {
      toast.error('Please enter a prompt')
      return
    }

    generateMutation.mutate({
      prompt,
      category,
      style_preset: stylePreset,
      realism_mode: realismMode,
      num_images: numImages,
    })
  }

  const handleTemplateClick = (template: string) => {
    setPrompt(template)
  }

  const handleDownload = (imageUrl: string) => {
    window.open(imageUrl, '_blank')
  }

  const getTemplates = () => {
    const key = `${category}-${stylePreset}`
    return TEMPLATE_PROMPTS[key] || []
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="border-b bg-white">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center space-x-2">
            <Sparkles className="h-6 w-6 text-primary-600" />
            <h1 className="text-2xl font-bold text-gray-900">AI Jewellery Designer</h1>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        <div className="grid gap-8 lg:grid-cols-3">
          {/* Left Sidebar - Form */}
          <div className="lg:col-span-1">
            <Card>
              <CardHeader>
                <CardTitle>Design Parameters</CardTitle>
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

                  {/* Number of Images */}
                  <div>
                    <label className="mb-2 block text-sm font-medium text-gray-700">
                      Number of Images: {numImages}
                    </label>
                    <input
                      type="range"
                      min="1"
                      max="4"
                      value={numImages}
                      onChange={(e) => setNumImages(Number(e.target.value))}
                      className="w-full"
                    />
                  </div>

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
                            className="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-left text-sm hover:bg-gray-50"
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
                    className="w-full"
                  >
                    <Sparkles className="mr-2 h-4 w-4" />
                    Generate Design
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Right Content - Results */}
          <div className="lg:col-span-2">
            {!result ? (
              <Card className="flex h-96 items-center justify-center">
                <div className="text-center">
                  <Sparkles className="mx-auto h-16 w-16 text-gray-400" />
                  <h3 className="mt-4 text-lg font-medium text-gray-900">
                    No designs yet
                  </h3>
                  <p className="mt-2 text-sm text-gray-600">
                    Fill in the parameters and click Generate to create your first design
                  </p>
                </div>
              </Card>
            ) : (
              <div className="space-y-6">
                {/* Main Image */}
                <Card>
                  <CardContent>
                    <div className="relative aspect-square overflow-hidden rounded-lg bg-gray-100">
                      <img
                        src={result.images[selectedImage].url}
                        alt="Generated design"
                        className="h-full w-full object-contain"
                      />
                    </div>

                    {/* Action Buttons */}
                    <div className="mt-4 flex flex-wrap gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDownload(result.images[selectedImage].url)}
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
                      <Button variant="outline" size="sm">
                        <Share2 className="mr-2 h-4 w-4" />
                        Share
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          setPrompt(result.prompt)
                          window.scrollTo({ top: 0, behavior: 'smooth' })
                        }}
                      >
                        <RefreshCw className="mr-2 h-4 w-4" />
                        Refine
                      </Button>
                    </div>
                  </CardContent>
                </Card>

                {/* Thumbnails */}
                {result.images.length > 1 && (
                  <Card>
                    <CardHeader>
                      <CardTitle>All Variations</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-4 gap-4">
                        {result.images.map((img, idx) => (
                          <button
                            key={idx}
                            onClick={() => setSelectedImage(idx)}
                            className={`relative aspect-square overflow-hidden rounded-lg border-2 transition-all ${
                              selectedImage === idx
                                ? 'border-primary-600 ring-2 ring-primary-200'
                                : 'border-gray-200 hover:border-gray-300'
                            }`}
                          >
                            <img
                              src={img.url}
                              alt={`Variation ${idx + 1}`}
                              className="h-full w-full object-cover"
                            />
                          </button>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Metadata */}
                <Card>
                  <CardHeader>
                    <CardTitle>Design Details</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <dl className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <dt className="font-medium text-gray-700">Category:</dt>
                        <dd className="text-gray-900">{result.category}</dd>
                      </div>
                      <div className="flex justify-between">
                        <dt className="font-medium text-gray-700">Style:</dt>
                        <dd className="text-gray-900">{result.style_preset}</dd>
                      </div>
                      <div className="flex justify-between">
                        <dt className="font-medium text-gray-700">Materials:</dt>
                        <dd className="text-gray-900">{result.materials.join(', ')}</dd>
                      </div>
                      <div className="flex justify-between">
                        <dt className="font-medium text-gray-700">Colors:</dt>
                        <dd className="text-gray-900">{result.colors.join(', ')}</dd>
                      </div>
                      <div className="flex justify-between">
                        <dt className="font-medium text-gray-700">Confidence:</dt>
                        <dd className="text-gray-900">{(result.confidence * 100).toFixed(1)}%</dd>
                      </div>
                      <div className="pt-2">
                        <dt className="mb-1 font-medium text-gray-700">Prompt Used:</dt>
                        <dd className="text-sm text-gray-600">{result.enhanced_prompt}</dd>
                      </div>
                    </dl>
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
