'use client'

import { useEffect, useState, memo } from 'react'

interface BackgroundImageProps {
  imageUrl: string | null
}

function BackgroundImage({ imageUrl }: BackgroundImageProps) {
  const [isLoading, setIsLoading] = useState(false)
  const [mounted, setMounted] = useState(false)
  const [imageLoaded, setImageLoaded] = useState(false)
  const [imageAspectRatio, setImageAspectRatio] = useState<number | null>(null)
  const [screenAspectRatio, setScreenAspectRatio] = useState<number>(16/9)

  useEffect(() => {
    setMounted(true)
  }, [])

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const updateAspectRatio = () => {
        setScreenAspectRatio(window.innerWidth / window.innerHeight)
      }
      updateAspectRatio()
      window.addEventListener('resize', updateAspectRatio)
      return () => window.removeEventListener('resize', updateAspectRatio)
    }
  }, [])

  useEffect(() => {
    if (!imageUrl || !mounted) {
      setImageLoaded(false)
      setImageAspectRatio(null)
      return
    }

    // For data URLs (uploaded images), they're already loaded
    if (imageUrl.startsWith('data:')) {
      setIsLoading(false)
      // Get image dimensions for uploaded images
      const img = new Image()
      img.onload = () => {
        const aspectRatio = img.width / img.height
        setImageAspectRatio(aspectRatio)
        setImageLoaded(true)
      }
      img.src = imageUrl
      return
    }

    // For remote URLs, check if image loads
    setIsLoading(true)
    setImageLoaded(false)
    const img = new Image()
    
    img.onload = () => {
      console.log('Image loaded successfully', img.width, img.height)
      const aspectRatio = img.width / img.height
      setImageAspectRatio(aspectRatio)
      setIsLoading(false)
      setImageLoaded(true)
    }

    img.onerror = (error) => {
      console.error('Error loading image:', error, imageUrl)
      setIsLoading(false)
      setImageLoaded(false)
      setImageAspectRatio(null)
    }

    img.src = imageUrl
  }, [imageUrl, mounted])

  if (!mounted) {
    return null
  }

  // Default gradient background when no image
  if (!imageUrl) {
    return (
      <div 
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: '100vw',
          height: '100vh',
          background: 'linear-gradient(to bottom right, #581c87, #1e3a8a, #000000)',
          zIndex: -1,
          margin: 0,
          padding: 0,
        }}
      />
    )
  }

  // Loading state (only for remote URLs)
  if (isLoading && !imageUrl?.startsWith('data:')) {
    return (
      <div 
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: '100vw',
          height: '100vh',
          backgroundColor: '#000000',
          zIndex: -1,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <div style={{ color: 'white', fontSize: '1.25rem' }}>Loading image...</div>
      </div>
    )
  }

  // Smart fit mode logic:
  // - AI-generated images: ALWAYS use 'cover' to fill entire screen
  // - Uploaded images/GIFs: Use smart judgment based on aspect ratio
  const isUploadedImage = imageUrl?.startsWith('data:')
  
  let useContain = false
  
  if (imageAspectRatio !== null) {
    if (!isUploadedImage) {
      // AI-generated images: ALWAYS cover the full screen
      useContain = false
    } else {
      // Uploaded images/GIFs: Use smart judgment
      // Calculate aspect ratio difference
      const aspectRatioDiff = Math.abs(imageAspectRatio - screenAspectRatio)
      const ratioDifference = aspectRatioDiff / Math.max(imageAspectRatio, screenAspectRatio)
      
      // If aspect ratios are similar (within 30% difference), use cover to fill screen
      // If very different (more than 30% difference), use contain to avoid cropping
      if (ratioDifference > 0.3) {
        // Aspect ratios are very different - use contain to show full image without cropping
        useContain = true
      } else {
        // Aspect ratios are similar - use cover to fill screen
        useContain = false
      }
    }
  }

  // Render clear, high-quality background image using img element for maximum quality
  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100vw',
        height: '100vh',
        backgroundColor: '#000000',
        zIndex: -1,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      <img
        src={imageUrl}
        alt="Background"
        loading="eager"
        decoding="async"
        onLoad={() => {
          setImageLoaded(true)
          setIsLoading(false)
        }}
        onError={() => {
          console.error('Error rendering image:', imageUrl)
          setIsLoading(false)
          setImageLoaded(false)
        }}
        style={{
          width: '100%',
          height: '100%',
          objectFit: useContain ? 'contain' : 'cover',
          objectPosition: 'center',
          margin: 0,
          padding: 0,
          pointerEvents: 'none',
          imageRendering: 'auto',
          WebkitBackfaceVisibility: 'hidden',
          backfaceVisibility: 'hidden',
          transform: 'translateZ(0)',
          willChange: 'transform',
          display: imageUrl ? 'block' : 'none',
        }}
      />
    </div>
  )
}

export default memo(BackgroundImage)
