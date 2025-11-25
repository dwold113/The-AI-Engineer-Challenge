'use client'

import { useEffect, useState, memo } from 'react'

interface BackgroundImageProps {
  imageUrl: string | null
}

function BackgroundImage({ imageUrl }: BackgroundImageProps) {
  const [isLoading, setIsLoading] = useState(false)
  const [mounted, setMounted] = useState(false)
  const [imageLoaded, setImageLoaded] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  useEffect(() => {
    if (!imageUrl || !mounted) {
      setImageLoaded(false)
      return
    }

    // For data URLs (uploaded images), they're already loaded
    if (imageUrl.startsWith('data:')) {
      setIsLoading(false)
      setImageLoaded(true)
      return
    }

    // For remote URLs, check if image loads
    setIsLoading(true)
    setImageLoaded(false)
    const img = new Image()
    
    img.onload = () => {
      console.log('Image loaded successfully', img.width, img.height)
      setIsLoading(false)
      setImageLoaded(true)
    }

    img.onerror = (error) => {
      console.error('Error loading image:', error, imageUrl)
      setIsLoading(false)
      setImageLoaded(false)
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

  // Render clear, high-quality background image using img element for maximum quality
  return (
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
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100vw',
        height: '100vh',
        objectFit: 'cover',
        objectPosition: 'center',
        zIndex: -1,
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
  )
}

export default memo(BackgroundImage)
