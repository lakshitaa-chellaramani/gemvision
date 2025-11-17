'use client'

import Link from 'next/link'
import { Sparkles, Eye, Shield, TrendingUp, Gem } from 'lucide-react'
import { motion, useInView } from 'framer-motion'
import { useRef } from 'react'
import dynamic from 'next/dynamic'

const ModelViewer = dynamic(() => import('./ModelViewer'), { ssr: false })

// Scroll Reveal Card Component
function ScrollRevealCard() {
  const ref = useRef(null)
  const isInView = useInView(ref, { once: true, margin: '-100px' })

  return (
    <section ref={ref} className="py-20 bg-gray-50">
      <div className="container mx-auto px-4">
        <motion.div
          initial={{ opacity: 0, y: 100, scale: 0.9 }}
          animate={isInView ? { opacity: 1, y: 0, scale: 1 } : { opacity: 0, y: 100, scale: 0.9 }}
          transition={{ duration: 0.8, ease: 'easeOut' }}
          className="max-w-4xl mx-auto"
        >
          <div className="card border-gray-200 bg-white shadow-xl relative overflow-hidden">
            <div className="relative z-10 p-8 md:p-12">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-12 h-12 rounded-full bg-primary-600 flex items-center justify-center shadow-md shadow-primary-400/40">
                  <Gem className="h-6 w-6 text-white" />
                </div>
                <div>
                  <h3 className="text-2xl font-bold text-gray-900">Premium Features</h3>
                  <p className="text-gray-500 text-sm">Unlock the full potential</p>
                </div>
              </div>
              
              <div className="grid md:grid-cols-2 gap-6 mb-8">
                <div className="p-4 rounded-lg bg-gray-50 border border-gray-200">
                  <Sparkles className="h-6 w-6 text-primary-600 mb-3" />
                  <h4 className="text-lg font-semibold text-gray-900 mb-2">AI Design Engine</h4>
                  <p className="text-gray-600 text-sm">
                    Advanced machine learning algorithms create unique designs tailored to your preferences.
                  </p>
                </div>
                <div className="p-4 rounded-lg bg-gray-50 border border-gray-200">
                  <Eye className="h-6 w-6 text-primary-600 mb-3" />
                  <h4 className="text-lg font-semibold text-gray-900 mb-2">3D Visualization</h4>
                  <p className="text-gray-600 text-sm">
                    Real-time rendering with photorealistic materials and lighting for accurate previews.
                  </p>
                </div>
                <div className="p-4 rounded-lg bg-gray-50 border border-gray-200">
                  <TrendingUp className="h-6 w-6 text-primary-600 mb-3" />
                  <h4 className="text-lg font-semibold text-gray-900 mb-2">Instant Export</h4>
                  <p className="text-gray-600 text-sm">
                    Export designs in multiple formats ready for manufacturing and presentation.
                  </p>
                </div>
                <div className="p-4 rounded-lg bg-gray-50 border border-gray-200">
                  <Shield className="h-6 w-6 text-primary-600 mb-3" />
                  <h4 className="text-lg font-semibold text-gray-900 mb-2">Quality Assurance</h4>
                  <p className="text-gray-600 text-sm">
                    Built-in quality checks ensure every design meets professional standards.
                  </p>
                </div>
              </div>
              
              <div className="flex flex-wrap gap-4">
                <Link
                  href="/designer"
                  className="px-6 py-3 rounded-lg bg-primary-600 text-white font-semibold hover:bg-primary-700 transition-all"
                >
                  Start Creating
                </Link>
                <Link
                  href="/demo"
                  className="px-6 py-3 rounded-lg border border-gray-300 text-gray-700 font-semibold hover:border-primary-600 hover:text-primary-600 transition-all"
                >
                  View Demo
                </Link>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  )
}

export default function HomePage() {
  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="border-b border-gray-200 bg-white/90 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-3">
          <div className="flex items-center justify-between gap-4">
            <Link href="/" className="flex items-center space-x-3 group">
              {/* Logo */}
              <div className="relative">
                <div className="relative bg-primary-600 w-10 h-10 rounded-lg rotate-45 flex items-center justify-center shadow-md shadow-primary-400/40">
                  <Gem className="h-5 w-5 text-white -rotate-45" />
                </div>
              </div>
              <h1 className="text-2xl font-bold text-gray-900">
                GemVision
              </h1>
            </Link>
            <nav className="hidden md:flex items-center gap-2 rounded-full border border-gray-200 bg-white px-3 py-1.5 text-sm shadow-sm">
              <Link href="/designer" className="px-3 py-1 rounded-full text-gray-600 hover:text-primary-600 hover:bg-gray-50 transition-colors">
                Designer
              </Link>
              <Link href="/tryon" className="px-3 py-1 rounded-full text-gray-600 hover:text-primary-600 hover:bg-gray-50 transition-colors">
                Try-On
              </Link>
              <Link href="/qc" className="px-3 py-1 rounded-full text-gray-600 hover:text-primary-600 hover:bg-gray-50 transition-colors">
                QC
              </Link>
              <Link href="/analytics" className="px-3 py-1 rounded-full text-gray-600 hover:text-primary-600 hover:bg-gray-50 transition-colors">
                Analytics
              </Link>
              <Link
                href="/designer"
                className="ml-2 rounded-full bg-primary-600 px-4 py-1.5 text-xs font-semibold text-white hover:bg-primary-700 transition-colors"
              >
                Start
              </Link>
            </nav>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative min-h-[80vh] flex items-center bg-white overflow-hidden">
        {/* Subtle grid background */}
        <div className="pointer-events-none absolute inset-0 bg-[url('/grid.svg')] opacity-40" />

        {/* Content Container */}
        <div className="container relative z-10 mx-auto grid items-center gap-12 px-4 py-16 md:grid-cols-2 lg:gap-16">
          {/* Left Side - Text Content */}
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 1, ease: 'easeOut' }}
            className="text-center md:text-left"
          >
            {/* Main Headline */}
            <motion.h1
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.2 }}
              className="mb-4 text-5xl font-bold leading-tight text-gray-900 md:text-6xl lg:text-7xl"
            >
              Design in Seconds.
            </motion.h1>

            <p className="mb-8 text-lg text-gray-600 md:text-xl">
              Turn simple ideas into bespoke jewellery designs with real-time 3D previews.
            </p>

            {/* CTA Button */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.6 }}
              className="flex justify-center md:justify-start"
            >
              <Link
                href="/designer"
                className="rounded-lg bg-primary-600 px-10 py-4 text-lg font-semibold text-white shadow-md hover:bg-primary-700 transition-all"
              >
                Start Designing Now
              </Link>
            </motion.div>

            {/* Features Pills */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.8, delay: 0.8 }}
              className="mt-8 flex flex-wrap items-center justify-center gap-3 text-sm text-gray-600 md:justify-start"
            >
              <div className="flex items-center gap-2 rounded-full border border-gray-200 px-4 py-2 bg-white">
                <Sparkles className="h-4 w-4 text-primary-600" />
                AI-Powered
              </div>
              <div className="flex items-center gap-2 rounded-full border border-gray-200 px-4 py-2 bg-white">
                <Eye className="h-4 w-4 text-primary-600" />
                3D Preview
              </div>
              <div className="flex items-center gap-2 rounded-full border border-gray-200 px-4 py-2 bg-white">
                <TrendingUp className="h-4 w-4 text-primary-600" />
                Instant Results
              </div>
            </motion.div>
          </motion.div>

          {/* Right Side - 3D Jewelry Model */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9, x: 30 }}
            animate={{ opacity: 1, scale: 1, x: 0 }}
            transition={{ duration: 1, delay: 0.3, ease: 'easeOut' }}
            className="relative"
          >
            {/* 3D Model Container */}
            <div className="relative rounded-3xl border border-gray-200 bg-white p-4 shadow-xl">
              <ModelViewer
                url="/gold.glb"
                width="100%"
                height={600}
                environmentPreset="none"
                autoRotate
                autoRotateSpeed={0.3}
                enableHoverRotation
                enableMouseParallax
                defaultZoom={1.3}
                minZoomDistance={0.8}
                maxZoomDistance={5}
                fadeIn
                showScreenshotButton={false}
              />
              
              {/* Subtle hint text */}
              <div className="pointer-events-none mt-3 flex select-none justify-between text-xs text-gray-400">
                <span>Drag to explore</span>
                <span>Scroll to zoom</span>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Horizontal Full-Width Card Section */}
      <section className="py-16 bg-gray-50">
        <div className="container mx-auto px-4">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
            className="card border-gray-200 bg-white shadow-xl"
          >
            <div className="grid md:grid-cols-2 gap-8 items-center">
              <div>
                <h2 className="text-4xl font-bold mb-4 text-gray-900">
                  Transform Ideas Into Reality
                </h2>
                <p className="text-gray-600 text-lg mb-6">
                  Our AI-powered platform turns your creative vision into stunning, photorealistic jewelry designs in seconds. Experience the future of jewelry creation.
                </p>
                <Link
                  href="/designer"
                  className="inline-block rounded-lg bg-primary-600 px-8 py-3 text-white font-semibold hover:bg-primary-700 transition-all"
                >
                  Get Started →
                </Link>
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div className="text-center p-4 rounded-lg bg-gray-50 border border-gray-200">
                  <div className="text-3xl font-bold text-primary-600 mb-2">10x</div>
                  <div className="text-sm text-gray-500">Faster</div>
                </div>
                <div className="text-center p-4 rounded-lg bg-gray-50 border border-gray-200">
                  <div className="text-3xl font-bold text-primary-600 mb-2">100+</div>
                  <div className="text-sm text-gray-500">Designs</div>
                </div>
                <div className="text-center p-4 rounded-lg bg-gray-50 border border-gray-200">
                  <div className="text-3xl font-bold text-primary-600 mb-2">AI</div>
                  <div className="text-sm text-gray-500">Powered</div>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Features Section */}
      <section className="container mx-auto px-4 py-20 text-gray-900">
        <div className="grid gap-8 md:grid-cols-3">
          {/* AI Designer */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
          >
            <Link href="/designer" className="card group block h-full hover:shadow-md">
              <div className="mb-4 inline-block rounded-full bg-primary-50 p-3">
                <Sparkles className="h-8 w-8 text-primary-600" />
              </div>
              <h3 className="mb-3 text-2xl font-bold text-gray-900 group-hover:text-primary-600">
                AI Jewellery Designer
              </h3>
              <p className="mb-4 text-gray-600">
                Transform text prompts into stunning jewellery designs. Generate multiple
                variations instantly with AI-powered image generation.
              </p>
              <ul className="space-y-2 text-sm text-gray-600">
                <li>• Text-to-image generation</li>
                <li>• Multiple style presets</li>
                <li>• Category-specific templates</li>
                <li>• Save as design ideas</li>
              </ul>
              <div className="mt-6 text-primary-600 group-hover:text-primary-700">
                Launch Designer →
              </div>
            </Link>
          </motion.div>

          {/* Virtual Try-On */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
          >
            <Link href="/tryon" className="card group block h-full hover:shadow-md">
              <div className="mb-4 inline-block rounded-full bg-amber-50 p-3">
                <Eye className="h-8 w-8 text-amber-500" />
              </div>
              <h3 className="mb-3 text-2xl font-bold text-gray-900 group-hover:text-amber-600">
                Virtual Try-On
              </h3>
              <p className="mb-4 text-gray-600">
                Let customers visualize jewellery on their hand. Upload a photo and place
                designs with interactive controls.
              </p>
              <ul className="space-y-2 text-sm text-gray-600">
                <li>• Photo upload or camera</li>
                <li>• Interactive placement</li>
                <li>• Scale, rotate, adjust</li>
                <li>• Save and share snapshots</li>
              </ul>
              <div className="mt-6 text-amber-600 group-hover:text-amber-700">
                Try It Now →
              </div>
            </Link>
          </motion.div>

          {/* QC Inspector */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
          >
            <Link href="/qc" className="card group block h-full hover:shadow-md">
              <div className="mb-4 inline-block rounded-full bg-emerald-50 p-3">
                <Shield className="h-8 w-8 text-emerald-500" />
              </div>
              <h3 className="mb-3 text-2xl font-bold text-gray-900 group-hover:text-emerald-600">
                AI Quality Inspector
              </h3>
              <p className="mb-4 text-gray-600">
                Automated defect detection for quality control. Identify scratches,
                misalignments, and surface issues instantly.
              </p>
              <ul className="space-y-2 text-sm text-gray-600">
                <li>• Automated defect detection</li>
                <li>• Confidence scoring</li>
                <li>• Rework job creation</li>
                <li>• Full audit trail</li>
              </ul>
              <div className="mt-6 text-emerald-600 group-hover:text-emerald-700">
                Start Inspection →
              </div>
            </Link>
          </motion.div>
        </div>
      </section>

      {/* Scroll-Reveal Card Section */}
      <ScrollRevealCard />

      {/* Diamond 3D Model Section */}
      <section className="py-16 bg-white">
        <div className="container mx-auto px-4">
          <div className="grid gap-10 md:grid-cols-2 items-center">
            <div>
              <h3 className="text-3xl font-bold text-gray-900 mb-4">
                Explore Your Diamond in 3D
              </h3>
              <p className="text-gray-600 mb-6">
                Rotate, zoom, and inspect your diamond model from every angle to evaluate brilliance,
                cut and overall appearance before production.
              </p>
              <ul className="space-y-2 text-gray-600 text-sm">
                <li>• High-detail diamond 3D model</li>
                <li>• Smooth rotation and zoom controls</li>
                <li>• Perfect for showcasing premium pieces</li>
              </ul>
            </div>
            <div className="rounded-3xl border border-gray-200 bg-white p-4 shadow-xl">
              <ModelViewer
                url="/diamond.glb"
                width="100%"
                height={400}
                environmentPreset="none"
                autoRotate
                autoRotateSpeed={0.4}
                enableHoverRotation
                enableMouseParallax
                defaultZoom={1.5}
                minZoomDistance={1}
                maxZoomDistance={4}
                fadeIn
                showScreenshotButton={false}
              />
            </div>
          </div>
        </div>
      </section>

      {/* Workflow Section */}
      <section className="bg-gray-50 py-20">
        <div className="container mx-auto px-4">
          <h3 className="mb-12 text-center text-3xl font-bold text-gray-900">
            Complete Jewellery Workflow
          </h3>
          <div className="flex flex-col items-center justify-center space-y-8 md:flex-row md:space-x-8 md:space-y-0">
            <div className="text-center">
              <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-primary-600 text-2xl font-bold text-white shadow-md shadow-primary-400/40">
                1
              </div>
              <h4 className="mb-2 font-semibold text-gray-900">Design</h4>
              <p className="text-sm text-gray-600">Generate concepts with AI</p>
            </div>
            <div className="hidden md:block">
              <div className="h-0.5 w-24 bg-gray-200" />
            </div>
            <div className="text-center">
              <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-gold-600 text-2xl font-bold text-white">
                2
              </div>
              <h4 className="mb-2 font-semibold text-gray-900">Visualize</h4>
              <p className="text-sm text-gray-600">Try on virtually</p>
            </div>
            <div className="hidden md:block">
              <div className="h-0.5 w-24 bg-gray-200" />
            </div>
            <div className="text-center">
              <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-green-600 text-2xl font-bold text-white">
                3
              </div>
              <h4 className="mb-2 font-semibold text-gray-900">Inspect</h4>
              <p className="text-sm text-gray-600">Automated QC</p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-200 bg-white">
        <div className="container mx-auto px-4 py-10">
          <div className="grid gap-8 md:grid-cols-3 items-start">
            {/* Brand + tagline */}
            <div>
              <div className="flex items-center gap-2 mb-3">
                <div className="relative bg-primary-600 w-8 h-8 rounded-lg rotate-45 flex items-center justify-center shadow-sm shadow-primary-400/40">
                  <Gem className="h-4 w-4 text-white -rotate-45" />
                </div>
                <span className="text-lg font-semibold text-gray-900">GemVision</span>
              </div>
              <p className="text-sm text-gray-500 max-w-xs">
                AI-assisted jewellery design, 3D visualization, and production-ready outputs in seconds.
              </p>
            </div>

            {/* Quick links */}
            <div className="text-sm">
              <h4 className="mb-3 font-semibold text-gray-900">Product</h4>
              <div className="flex flex-col gap-2 text-gray-600">
                <Link href="/designer" className="hover:text-primary-600 transition-colors">
                  AI Designer
                </Link>
                <Link href="/tryon" className="hover:text-primary-600 transition-colors">
                  Virtual Try-On
                </Link>
                <Link href="/qc" className="hover:text-primary-600 transition-colors">
                  Quality Inspector
                </Link>
                <Link href="/analytics" className="hover:text-primary-600 transition-colors">
                  Analytics
                </Link>
              </div>
            </div>

            {/* CTA / status */}
            <div className="text-sm md:text-right">
              <h4 className="mb-3 font-semibold text-gray-900">Get Started</h4>
              <Link
                href="/designer"
                className="inline-flex items-center justify-center rounded-full bg-primary-600 px-5 py-2 text-xs font-semibold text-white shadow-sm hover:bg-primary-700 transition-colors"
              >
                Start Designing
              </Link>
              <p className="mt-2 text-xs text-gray-400">
                No credit card required. Start designing in under 60 seconds.
              </p>
            </div>
          </div>
          <div className="mt-8 border-t border-gray-100 pt-4 text-center text-xs text-gray-400">
            © 2024 GemVision. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  )
}