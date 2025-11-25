'use client'

import { useEffect, useState, memo, useRef } from 'react'

interface PixelatedBackgroundProps {
  imageUrl: string | null
  pixelSize?: number
}

function PixelatedBackground({ imageUrl, pixelSize = 4 }: PixelatedBackgroundProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
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
    if (!imageUrl || dimensions.width === 0 || dimensions.height === 0 || !mounted || !canvasRef.current) {
      return
    }

    setIsLoading(true)
    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d', { willReadFrequently: true })
    if (!ctx) {
      setIsLoading(false)
      return
    }

    const img = new Image()
    
    img.onload = () => {
      console.log('Image loaded successfully', img.width, img.height)
      
      const screenWidth = dimensions.width
      const screenHeight = dimensions.height
      const imgAspect = img.width / img.height
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
      ctx.drawImage(img, offsetX, offsetY, drawWidth, drawHeight)

      // Get image data
      const imageData = ctx.getImageData(0, 0, screenWidth, screenHeight)
      const data = imageData.data

      // Clear and redraw with pixelation
      ctx.fillStyle = '#000000'
      ctx.fillRect(0, 0, canvas.width, canvas.height)

      // Draw pixelated version
      for (let y = 0; y < screenHeight; y += pixelSize) {
        for (let x = 0; x < screenWidth; x += pixelSize) {
          // Sample from center of pixel block
          const sampleX = Math.min(x + Math.floor(pixelSize / 2), screenWidth - 1)
          const sampleY = Math.min(y + Math.floor(pixelSize / 2), screenHeight - 1)
          
          const index = (sampleY * screenWidth + sampleX) * 4
          const r = data[index]
          const g = data[index + 1]
          const b = data[index + 2]
          
          // Draw the pixel square
          ctx.fillStyle = `rgb(${r}, ${g}, ${b})`
          ctx.fillRect(x, y, pixelSize, pixelSize)
        }
      }

      console.log('Pixelated background rendered on canvas')
      setIsLoading(false)
    }

    img.onerror = (error) => {
      console.error('Error loading image:', error, imageUrl)
      setIsLoading(false)
    }

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

  // Render pixelated background using canvas
  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100vw',
        height: '100vh',
        zIndex: -1,
        margin: 0,
        padding: 0,
        pointerEvents: 'none',
        imageRendering: 'pixelated',
      }}
    />
  )
}

export default memo(PixelatedBackground)
