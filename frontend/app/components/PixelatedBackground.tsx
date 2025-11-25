'use client'

import { useEffect, useState } from 'react'

interface PixelatedBackgroundProps {
  imageUrl: string | null
  pixelSize?: number
}

export default function PixelatedBackground({ imageUrl, pixelSize = 15 }: PixelatedBackgroundProps) {
  const [pixels, setPixels] = useState<Array<{ x: number; y: number; color: string }>>([])
  const [isLoading, setIsLoading] = useState(false)
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 })

  // Update dimensions on mount and resize
  useEffect(() => {
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
    if (!imageUrl || dimensions.width === 0 || dimensions.height === 0) {
      setPixels([])
      return
    }

    setIsLoading(true)
    const img = new Image()
    
    // Try to load with CORS, but handle errors gracefully
    img.crossOrigin = 'anonymous'
    
    img.onload = () => {
      console.log('Image loaded successfully', img.width, img.height)
      const canvas = document.createElement('canvas')
      const ctx = canvas.getContext('2d', { willReadFrequently: true })
      if (!ctx) {
        setIsLoading(false)
        return
      }

      // Calculate dimensions to cover entire viewport (fill screen completely)
      const screenWidth = dimensions.width
      const screenHeight = dimensions.height
      const imgAspect = img.width / img.height
      const screenAspect = screenWidth / screenHeight

      let drawWidth = screenWidth
      let drawHeight = screenHeight
      let offsetX = 0
      let offsetY = 0

      // Cover mode: scale image to cover entire screen, cropping if necessary
      if (imgAspect > screenAspect) {
        // Image is wider - scale to cover height, crop width
        drawHeight = screenHeight
        drawWidth = drawHeight * imgAspect
        offsetX = (screenWidth - drawWidth) / 2
      } else {
        // Image is taller - scale to cover width, crop height
        drawWidth = screenWidth
        drawHeight = drawWidth / imgAspect
        offsetY = (screenHeight - drawHeight) / 2
      }

      canvas.width = screenWidth
      canvas.height = screenHeight

      // Fill background with black
      ctx.fillStyle = '#000000'
      ctx.fillRect(0, 0, canvas.width, canvas.height)

      // Draw image to cover entire screen (may crop edges)
      ctx.drawImage(img, offsetX, offsetY, drawWidth, drawHeight)

      // Extract pixel data
      const pixelData: Array<{ x: number; y: number; color: string }> = []
      
      for (let y = 0; y < screenHeight; y += pixelSize) {
        for (let x = 0; x < screenWidth; x += pixelSize) {
          const imageData = ctx.getImageData(x, y, pixelSize, pixelSize)
          const data = imageData.data
          
          // Calculate average color of the pixel block
          let r = 0, g = 0, b = 0, count = 0
          for (let i = 0; i < data.length; i += 4) {
            r += data[i]
            g += data[i + 1]
            b += data[i + 2]
            count++
          }
          
          const avgR = Math.floor(r / count)
          const avgG = Math.floor(g / count)
          const avgB = Math.floor(b / count)
          
          pixelData.push({
            x,
            y,
            color: `rgb(${avgR}, ${avgG}, ${avgB})`
          })
        }
      }

      console.log('Pixel data generated:', pixelData.length, 'pixels')
      setPixels(pixelData)
      setIsLoading(false)
    }

    img.onerror = (error) => {
      console.error('Error loading image:', error)
      setIsLoading(false)
      setPixels([])
    }

    img.src = imageUrl
  }, [imageUrl, pixelSize, dimensions])

  if (!imageUrl) {
    return (
      <div 
        className="fixed inset-0 bg-gradient-to-br from-purple-900 via-blue-900 to-black z-0" 
        style={{
          width: '100vw',
          height: '100vh',
          position: 'fixed',
          top: 0,
          left: 0,
          zIndex: 0,
        }}
      />
    )
  }

  if (isLoading) {
    return (
      <div className="fixed inset-0 bg-black flex items-center justify-center">
        <div className="text-white text-xl animate-pulse">Creating pixelated background...</div>
      </div>
    )
  }

  if (pixels.length === 0) {
    return null
  }

  const columns = dimensions.width > 0 ? Math.ceil(dimensions.width / pixelSize) : 0
  const rows = dimensions.height > 0 ? Math.ceil(dimensions.height / pixelSize) : 0

  return (
    <div 
      className="fixed inset-0 bg-black pointer-events-none" 
      style={{ 
        width: '100vw',
        height: '100vh',
        position: 'fixed',
        top: 0,
        left: 0,
        zIndex: 0,
      }}
    >
      <div 
        style={{
          display: 'grid',
          gridTemplateColumns: `repeat(${columns}, ${pixelSize}px)`,
          gridTemplateRows: `repeat(${rows}, ${pixelSize}px)`,
          gap: '0',
          width: '100vw',
          height: '100vh',
          position: 'absolute',
          top: 0,
          left: 0,
        }}
      >
        {pixels.map((pixel, index) => (
          <div
            key={`${pixel.x}-${pixel.y}-${index}`}
            style={{
              width: `${pixelSize}px`,
              height: `${pixelSize}px`,
              backgroundColor: pixel.color,
              animationDelay: `${(index % 100) * 0.01}s`,
            }}
            className="pixel-square"
          />
        ))}
      </div>
    </div>
  )
}

