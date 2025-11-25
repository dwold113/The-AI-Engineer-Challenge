'use client'

import { useState, useEffect } from 'react'
import PixelatedBackground from './components/PixelatedBackground'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function Home() {
  const [prompt, setPrompt] = useState('')
  const [imageUrl, setImageUrl] = useState<string | null>(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  const handleGenerate = async () => {
    if (!prompt.trim()) {
      setError('Please enter a prompt')
      return
    }

    setIsGenerating(true)
    setError(null)
    setImageUrl(null) // Clear previous image

    try {
      console.log('Calling API:', `${API_URL}/api/generate-image`)
      const response = await fetch(`${API_URL}/api/generate-image`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ prompt }),
      })

      console.log('Response status:', response.status, response.ok)

      if (!response.ok) {
        const errorText = await response.text()
        console.error('API error response:', errorText)
        throw new Error(`Failed to generate image: ${response.status} ${errorText}`)
      }

      const data = await response.json()
      console.log('Image URL received:', data.image_url)
      setImageUrl(data.image_url)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An error occurred'
      setError(errorMessage)
      console.error('Error generating image:', err)
    } finally {
      setIsGenerating(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !isGenerating) {
      handleGenerate()
    }
  }

  if (!mounted) {
    return null
  }

  return (
    <div style={{ position: 'relative', minHeight: '100vh', width: '100vw' }}>
      <PixelatedBackground imageUrl={imageUrl} pixelSize={6} />
      <main className="relative min-h-screen" style={{ backgroundColor: 'transparent', position: 'relative', zIndex: 1 }}>
        <div className="relative z-10 flex flex-col items-center justify-center min-h-screen p-8" style={{ minHeight: '100vh' }}>
        <div className="w-full max-w-2xl">
          <h1 className="text-5xl font-bold text-white mb-8 text-center drop-shadow-2xl">
            Pixelated Background Generator
          </h1>
          
          <div className="bg-black/80 backdrop-blur-md rounded-xl p-8 shadow-2xl border border-white/10 animate-fade-in">
            <div className="flex flex-col gap-5">
              <div>
                <label htmlFor="prompt" className="block text-white text-sm font-medium mb-3">
                  What should your pixelated world look like? 🎨
                </label>
                <input
                  id="prompt"
                  type="text"
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="✨ Describe your dream background! Try: 'cyberpunk city at night', 'magical forest with fireflies', 'underwater coral reef', 'neon-soaked retro arcade'..."
                  className="w-full px-5 py-4 rounded-lg bg-white/10 text-white placeholder-white/40 border border-white/20 focus:outline-none focus:ring-2 focus:ring-white/50 focus:border-transparent transition-all text-lg"
                  disabled={isGenerating}
                />
              </div>
              
              {error && (
                <div className="bg-red-500/20 border border-red-500/50 text-red-200 px-4 py-3 rounded-lg animate-fade-in">
                  {error}
                </div>
              )}
              
              <button
                onClick={handleGenerate}
                disabled={isGenerating || !prompt.trim()}
                className="w-full px-6 py-4 bg-white text-black font-bold rounded-lg hover:bg-white/90 disabled:opacity-50 disabled:cursor-not-allowed transition-all transform hover:scale-105 active:scale-95 text-lg shadow-lg"
              >
                {isGenerating ? (
                  <span className="flex items-center justify-center gap-2">
                    <span className="animate-spin">⏳</span>
                    Generating...
                  </span>
                ) : (
                  'Generate Pixelated Background'
                )}
              </button>
            </div>
          </div>
          
        </div>
      </div>
      </main>
    </div>
  )
}

