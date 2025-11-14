'use client'

import Link from 'next/link'
import { Sparkles, Eye, Shield, TrendingUp } from 'lucide-react'
import { motion } from 'framer-motion'

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-purple-50 to-white">
      {/* Header */}
      <header className="border-b bg-white/80 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Sparkles className="h-8 w-8 text-primary-600" />
              <h1 className="text-2xl font-bold text-gray-900">GemVision</h1>
            </div>
            <nav className="flex space-x-6">
              <Link href="/designer" className="text-gray-600 hover:text-primary-600">
                Designer
              </Link>
              <Link href="/tryon" className="text-gray-600 hover:text-primary-600">
                Try-On
              </Link>
              <Link href="/qc" className="text-gray-600 hover:text-primary-600">
                QC Inspector
              </Link>
              <Link href="/analytics" className="text-gray-600 hover:text-primary-600">
                Analytics
              </Link>
            </nav>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="container mx-auto px-4 py-20 text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
        >
          <h2 className="mb-6 text-5xl font-bold text-gray-900">
            AI-Powered Jewellery Design Platform
          </h2>
          <p className="mx-auto mb-8 max-w-2xl text-xl text-gray-600">
            Design stunning jewellery with AI, visualize on customers with virtual try-on,
            and ensure quality with automated inspection.
          </p>
          <div className="flex justify-center space-x-4">
            <Link
              href="/designer"
              className="rounded-lg bg-primary-600 px-8 py-3 text-white hover:bg-primary-700"
            >
              Start Designing
            </Link>
            <Link
              href="/demo"
              className="rounded-lg border-2 border-primary-600 px-8 py-3 text-primary-600 hover:bg-primary-50"
            >
              Watch Demo
            </Link>
          </div>
        </motion.div>
      </section>

      {/* Features Section */}
      <section className="container mx-auto px-4 py-20">
        <div className="grid gap-8 md:grid-cols-3">
          {/* AI Designer */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
          >
            <Link href="/designer" className="card group block h-full">
              <div className="mb-4 inline-block rounded-full bg-primary-100 p-3">
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
            <Link href="/tryon" className="card group block h-full">
              <div className="mb-4 inline-block rounded-full bg-gold-100 p-3">
                <Eye className="h-8 w-8 text-gold-600" />
              </div>
              <h3 className="mb-3 text-2xl font-bold text-gray-900 group-hover:text-gold-600">
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
              <div className="mt-6 text-gold-600 group-hover:text-gold-700">
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
            <Link href="/qc" className="card group block h-full">
              <div className="mb-4 inline-block rounded-full bg-green-100 p-3">
                <Shield className="h-8 w-8 text-green-600" />
              </div>
              <h3 className="mb-3 text-2xl font-bold text-gray-900 group-hover:text-green-600">
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
              <div className="mt-6 text-green-600 group-hover:text-green-700">
                Start Inspection →
              </div>
            </Link>
          </motion.div>
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
              <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-primary-600 text-2xl font-bold text-white">
                1
              </div>
              <h4 className="mb-2 font-semibold">Design</h4>
              <p className="text-sm text-gray-600">Generate concepts with AI</p>
            </div>
            <div className="hidden md:block">
              <div className="h-0.5 w-24 bg-gray-300" />
            </div>
            <div className="text-center">
              <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-gold-600 text-2xl font-bold text-white">
                2
              </div>
              <h4 className="mb-2 font-semibold">Visualize</h4>
              <p className="text-sm text-gray-600">Try on virtually</p>
            </div>
            <div className="hidden md:block">
              <div className="h-0.5 w-24 bg-gray-300" />
            </div>
            <div className="text-center">
              <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-green-600 text-2xl font-bold text-white">
                3
              </div>
              <h4 className="mb-2 font-semibold">Inspect</h4>
              <p className="text-sm text-gray-600">Automated QC</p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t bg-white py-8">
        <div className="container mx-auto px-4 text-center text-gray-600">
          <p>© 2024 GemVision. AI-powered jewellery platform.</p>
          <div className="mt-4 flex justify-center space-x-6">
            <Link href="/designer" className="hover:text-primary-600">
              Designer
            </Link>
            <Link href="/tryon" className="hover:text-primary-600">
              Try-On
            </Link>
            <Link href="/qc" className="hover:text-primary-600">
              QC
            </Link>
            <Link href="/analytics" className="hover:text-primary-600">
              Analytics
            </Link>
          </div>
        </div>
      </footer>
    </div>
  )
}
