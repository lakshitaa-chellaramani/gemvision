'use client'

import { useEffect, useRef } from 'react'

interface Model3DViewerProps {
  modelUrl: string
  alt?: string
  className?: string
  autoRotate?: boolean
  cameraControls?: boolean
}

declare global {
  namespace JSX {
    interface IntrinsicElements {
      'model-viewer': React.DetailedHTMLProps<
        React.HTMLAttributes<HTMLElement> & {
          src?: string
          alt?: string
          'auto-rotate'?: boolean
          'camera-controls'?: boolean
          'shadow-intensity'?: string
          'exposure'?: string
          'camera-orbit'?: string
          'min-camera-orbit'?: string
          'max-camera-orbit'?: string
          'field-of-view'?: string
          loading?: string
          'reveal'?: string
        },
        HTMLElement
      >
    }
  }
}

export function Model3DViewer({
  modelUrl,
  alt = '3D Model',
  className = '',
  autoRotate = true,
  cameraControls = true,
}: Model3DViewerProps) {
  const viewerRef = useRef<HTMLElement>(null)

  useEffect(() => {
    // Dynamically load model-viewer script
    const script = document.createElement('script')
    script.type = 'module'
    script.src = 'https://ajax.googleapis.com/ajax/libs/model-viewer/3.4.0/model-viewer.min.js'
    document.head.appendChild(script)

    return () => {
      // Cleanup script on unmount
      if (document.head.contains(script)) {
        document.head.removeChild(script)
      }
    }
  }, [])

  return (
    <div className={`relative ${className}`} style={{ width: '100%', height: '100%' }}>
      <model-viewer
        ref={viewerRef}
        src={modelUrl}
        alt={alt}
        auto-rotate={autoRotate}
        camera-controls={cameraControls}
        shadow-intensity="1"
        exposure="1"
        camera-orbit="0deg 75deg 105%"
        min-camera-orbit="auto auto 5%"
        max-camera-orbit="auto auto 500%"
        field-of-view="30deg"
        loading="eager"
        reveal="auto"
        style={{
          width: '100%',
          height: '100%',
          minHeight: '400px',
          backgroundColor: '#f3f4f6',
        }}
      />

      {/* Loading Indicator */}
      <div
        className="absolute inset-0 flex items-center justify-center bg-gray-100 pointer-events-none"
        style={{ display: 'none' }}
      >
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-sm text-gray-600">Loading 3D Model...</p>
        </div>
      </div>

      {/* Controls Hint */}
      <div className="absolute bottom-4 left-4 bg-black/70 text-white px-3 py-2 rounded-md text-xs">
        <p>🖱️ Drag to rotate • Scroll to zoom</p>
      </div>
    </div>
  )
}
