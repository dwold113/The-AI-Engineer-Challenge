'use client'

import { useEffect, useState, memo } from 'react'

interface PixelatedBackgroundProps {
  imageUrl: string | null
  pixelSize?: number
}

function PixelatedBackground({ imageUrl, pixelSize = 15 }: PixelatedBackgroundProps) {
  const [pixels, setPixels] = useState<Array<{ x: number; y: number; color: string }>>([])
  const [isLoading, setIsLoading] = useState(false)
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 })
  const [mounted, setMounted] = useState(false)

  // Update dimensions on mount and resize
  useEffect(() => {
    setMounted(true)
    const updateDimensions = () => {
      setDimensions({
        width: window.innerWidth,
        height: window.innerHeight
      })
    }

    updateDimensions()
    window.addEventListener('resize', updateDimensions)
    return () => window.removeEventListener('resize', updateDimensions)
  }, [])

  useEffect(() => {
    if (!imageUrl || dimensions.width === 0 || dimensions.height === 0 || !mounted) {
      setPixels([])
      return
    }

    setIsLoading(true)
    
    const processImage = (image: HTMLImageElement) => {
      console.log('Processing image:', image.width, image.height)
      const canvas = document.createElement('canvas')
      const ctx = canvas.getContext('2d', { willReadFrequently: true })
      if (!ctx) {
        console.error('Failed to get canvas context')
        setIsLoading(false)
        return
      }

      const screenWidth = dimensions.width
      const screenHeight = dimensions.height
      const imgAspect = image.width / image.height
      const screenAspect = screenWidth / screenHeight

      let drawWidth = screenWidth
      let drawHeight = screenHeight
      let offsetX = 0
      let offsetY = 0

      // Cover mode: scale image to cover entire screen
      if (imgAspect > screenAspect) {
        drawHeight = screenHeight
        drawWidth = drawHeight * imgAspect
        offsetX = (screenWidth - drawWidth) / 2
      } else {
        drawWidth = screenWidth
        drawHeight = drawWidth / imgAspect
        offsetY = (screenHeight - drawHeight) / 2
      }

      canvas.width = screenWidth
      canvas.height = screenHeight

      // Fill background with black
      ctx.fillStyle = '#000000'
      ctx.fillRect(0, 0, canvas.width, canvas.height)
      
      // Draw image to cover entire screen
      ctx.drawImage(image, offsetX, offsetY, drawWidth, drawHeight)

      // Extract pixel data with better sampling
      const pixelData: Array<{ x: number; y: number; color: string }> = []
      
      for (let y = 0; y < screenHeight; y += pixelSize) {
        for (let x = 0; x < screenWidth; x += pixelSize) {
          // Sample from center of pixel block for better accuracy
          const sampleX = Math.min(x + Math.floor(pixelSize / 2), screenWidth - 1)
          const sampleY = Math.min(y + Math.floor(pixelSize / 2), screenHeight - 1)
          
          const imageData = ctx.getImageData(sampleX, sampleY, 1, 1)
          const data = imageData.data
          
          // Use the center pixel color directly for sharper results
          const r = data[0]
          const g = data[1]
          const b = data[2]
          
          pixelData.push({
            x,
            y,
            color: `rgb(${r}, ${g}, ${b})`
          })
        }
      }

      console.log('Pixel data generated:', pixelData.length, 'pixels')
      setPixels(pixelData)
      setIsLoading(false)
    }

    const img = new Image()
    
    img.onload = () => {
      console.log('Image loaded successfully', img.width, img.height, imageUrl)
      processImage(img)
    }

    img.onerror = (error) => {
      console.error('Error loading image:', error, imageUrl)
      setIsLoading(false)
      setPixels([])
    }

    // Try loading without CORS first (OpenAI images may not support CORS)
    img.src = imageUrl
  }, [imageUrl, pixelSize, dimensions, mounted])

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
        <div style={{ color: 'white', fontSize: '1.25rem' }}>Creating pixelated background...</div>
      </div>
    )
  }

  // Fallback: show image directly if pixelation failed
  if (pixels.length === 0) {
    return (
      <div 
        style={{ 
          position: 'fixed',
          top: 0,
          left: 0,
          width: '100vw',
          height: '100vh',
          backgroundImage: `url(${imageUrl})`,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          backgroundRepeat: 'no-repeat',
          zIndex: -1,
        }}
      />
    )
  }

  // Render pixelated background
  const columns = Math.ceil(dimensions.width / pixelSize)
  const rows = Math.ceil(dimensions.height / pixelSize)

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
        margin: 0,
        padding: 0,
        pointerEvents: 'none',
      }}
    >
      <div 
        style={{
          display: 'grid',
          gridTemplateColumns: `repeat(${columns}, ${pixelSize}px)`,
          gridTemplateRows: `repeat(${rows}, ${pixelSize}px)`,
          gap: 0,
          width: '100vw',
          height: '100vh',
          position: 'absolute',
          top: 0,
          left: 0,
          willChange: 'contents',
          transform: 'translateZ(0)',
          contain: 'layout style paint',
        }}
      >
        {pixels.map((pixel, index) => (
          <div
            key={`${pixel.x}-${pixel.y}-${index}`}
            style={{
              width: `${pixelSize}px`,
              height: `${pixelSize}px`,
              backgroundColor: pixel.color,
              willChange: 'background-color',
              transform: 'translateZ(0)',
            }}
          />
        ))}
      </div>
    </div>
  )
}

export default memo(PixelatedBackground)
