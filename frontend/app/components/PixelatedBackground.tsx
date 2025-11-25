'use client'

import { useEffect, useState, memo } from 'react'

interface BackgroundImageProps {
  imageUrl: string | null
}

function BackgroundImage({ imageUrl }: BackgroundImageProps) {
  const [isLoading, setIsLoading] = useState(false)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  useEffect(() => {
    if (!imageUrl || !mounted) {
      return
    }

    setIsLoading(true)
    const img = new Image()
    
    img.onload = () => {
      console.log('Image loaded successfully', img.width, img.height)
      setIsLoading(false)
    }

    img.onerror = (error) => {
      console.error('Error loading image:', error, imageUrl)
      setIsLoading(false)
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

  // Loading state
  if (isLoading) {
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
        // Ensure no compression or quality loss
        loading: 'eager',
        decoding: 'async',
      }}
    />
  )
}

export default memo(BackgroundImage)
