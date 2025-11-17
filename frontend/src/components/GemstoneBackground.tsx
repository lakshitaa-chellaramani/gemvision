'use client'

import { FC } from 'react'

const GemstoneBackground: FC = () => {
  return (
    <div className="absolute inset-0 overflow-hidden">
      {/* Dark base with gemstone-like gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900" />
      
      {/* Gemstone facets effect using multiple overlapping gradients */}
      <div className="absolute inset-0 opacity-40">
        <div 
          className="absolute top-1/4 left-1/4 w-96 h-96 rounded-full blur-3xl" 
          style={{
            background: 'radial-gradient(circle, rgba(16, 185, 129, 0.3) 0%, transparent 70%)'
          }}
        />
        <div 
          className="absolute top-1/2 right-1/3 w-80 h-80 rounded-full blur-3xl" 
          style={{
            background: 'radial-gradient(circle, rgba(59, 130, 246, 0.3) 0%, transparent 70%)'
          }}
        />
        <div 
          className="absolute bottom-1/4 left-1/3 w-72 h-72 rounded-full blur-3xl" 
          style={{
            background: 'radial-gradient(circle, rgba(34, 211, 238, 0.2) 0%, transparent 70%)'
          }}
        />
      </div>

      {/* Light refraction lines (gemstone facets) */}
      <div className="absolute inset-0 opacity-20">
        <div 
          className="absolute top-0 left-1/4 w-px h-full bg-gradient-to-b from-transparent via-cyan-300 to-transparent"
          style={{ transform: 'rotate(15deg)', transformOrigin: 'top' }}
        />
        <div 
          className="absolute top-0 left-2/4 w-px h-full bg-gradient-to-b from-transparent via-emerald-300 to-transparent"
          style={{ transform: 'rotate(-12deg)', transformOrigin: 'top' }}
        />
        <div 
          className="absolute top-0 right-1/4 w-px h-full bg-gradient-to-b from-transparent via-blue-300 to-transparent"
          style={{ transform: 'rotate(8deg)', transformOrigin: 'top' }}
        />
      </div>

      {/* Blur overlay to simulate macro photography out-of-focus effect */}
      <div className="absolute inset-0 backdrop-blur-[2px] opacity-60" />
      
      {/* Subtle vignette */}
      <div 
        className="absolute inset-0" 
        style={{
          background: 'radial-gradient(circle at center, transparent 0%, transparent 50%, rgba(0, 0, 0, 0.4) 100%)'
        }}
      />
    </div>
  )
}

export default GemstoneBackground
