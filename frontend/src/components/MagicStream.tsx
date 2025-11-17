'use client'

import { FC } from 'react'
import { motion } from 'framer-motion'

const MagicStream: FC = () => {
  // Generate points for the flowing stream path (curved S-shape from left to right)
  const streamPath = [
    { x: '10%', y: '50%' },
    { x: '25%', y: '45%' },
    { x: '40%', y: '50%' },
    { x: '55%', y: '55%' },
    { x: '70%', y: '50%' },
    { x: '85%', y: '45%' },
    { x: '90%', y: '50%' },
  ]

  return (
    <div className="absolute inset-0 pointer-events-none overflow-hidden" style={{ zIndex: 5 }}>
      {/* Flowing particles/light stream */}
      <svg 
        className="absolute inset-0 w-full h-full" 
        style={{ filter: 'blur(1px)' }}
        viewBox="0 0 100 100"
        preserveAspectRatio="none"
      >
        <defs>
          <linearGradient id="magicGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#9333ea" stopOpacity="0.8" />
            <stop offset="50%" stopColor="#60a5fa" stopOpacity="0.6" />
            <stop offset="100%" stopColor="#34d399" stopOpacity="0.4" />
          </linearGradient>
          <linearGradient id="particleGradient" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#ffffff" stopOpacity="0.9" />
            <stop offset="100%" stopColor="#9333ea" stopOpacity="0.3" />
          </linearGradient>
        </defs>

        {/* Main flowing stream path - curved S-shape from left to right */}
        <motion.path
          d="M 10 50 Q 25 45, 40 50 T 70 50 T 90 50"
          fill="none"
          stroke="url(#magicGradient)"
          strokeWidth="0.3"
          strokeLinecap="round"
          initial={{ pathLength: 0, opacity: 0 }}
          animate={{ 
            pathLength: 1, 
            opacity: [0, 1, 1, 0.8],
          }}
          transition={{ 
            duration: 3,
            repeat: Infinity,
            repeatType: 'loop',
            ease: 'easeInOut'
          }}
        />

        {/* Neural network style connecting lines */}
        {streamPath.slice(0, -1).map((point, i) => {
          const nextPoint = streamPath[i + 1]
          const x1 = parseFloat(point.x)
          const y1 = parseFloat(point.y)
          const x2 = parseFloat(nextPoint.x)
          const y2 = parseFloat(nextPoint.y)
          
          return (
            <motion.line
              key={i}
              x1={x1}
              y1={y1}
              x2={x2}
              y2={y2}
              stroke="url(#magicGradient)"
              strokeWidth="0.15"
              strokeOpacity="0.4"
              initial={{ pathLength: 0, opacity: 0 }}
              animate={{ 
                pathLength: 1, 
                opacity: [0.2, 0.5, 0.2],
              }}
              transition={{ 
                duration: 2,
                delay: i * 0.2,
                repeat: Infinity,
                repeatType: 'loop',
                ease: 'easeInOut'
              }}
            />
          )
        })}
      </svg>

      {/* Floating particles along the stream */}
      {Array.from({ length: 12 }).map((_, i) => {
        const progress = i / 12
        const pointIndex = Math.floor(progress * (streamPath.length - 1))
        const point = streamPath[pointIndex]
        const nextPoint = streamPath[pointIndex + 1] || point
        const t = (progress * (streamPath.length - 1)) % 1
        
        // Interpolate between points for smoother movement
        const leftPercent = parseFloat(point.x) + (parseFloat(nextPoint.x) - parseFloat(point.x)) * t
        const topPercent = parseFloat(point.y) + (parseFloat(nextPoint.y) - parseFloat(point.y)) * t
        
        return (
          <motion.div
            key={i}
            className="absolute w-2 h-2 rounded-full bg-gradient-to-br from-purple-400 via-blue-400 to-emerald-400"
            style={{
              left: `${leftPercent}%`,
              top: `${topPercent}%`,
              filter: 'blur(0.5px)',
              boxShadow: '0 0 8px rgba(147, 51, 234, 0.8)',
              transform: 'translate(-50%, -50%)',
            }}
            initial={{ 
              opacity: 0,
              scale: 0,
            }}
            animate={{ 
              opacity: [0, 1, 1, 0],
              scale: [0, 1.2, 1, 0.8],
            }}
            transition={{
              duration: 3,
              delay: i * 0.25,
              repeat: Infinity,
              repeatType: 'loop',
              ease: 'easeInOut',
            }}
          />
        )
      })}

      {/* Light particles/dots that flow along the path */}
      {Array.from({ length: 20 }).map((_, i) => (
        <motion.div
          key={`particle-${i}`}
          className="absolute w-1 h-1 rounded-full bg-white"
          style={{
            filter: 'blur(1px)',
            boxShadow: '0 0 4px rgba(255, 255, 255, 0.9)',
          }}
          initial={{ 
            left: '10%',
            top: '50%',
            opacity: 0,
          }}
          animate={{ 
            left: ['10%', '90%'],
            top: ['50%', '45%', '50%', '45%', '50%'],
            opacity: [0, 1, 1, 0.8, 0],
          }}
          transition={{
            duration: 4,
            delay: i * 0.2,
            repeat: Infinity,
            repeatType: 'loop',
            ease: 'easeInOut',
          }}
        />
      ))}
    </div>
  )
}

export default MagicStream
