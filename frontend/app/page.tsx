'use client'

import { useState, useEffect, useRef } from 'react'
import BackgroundImage from './components/PixelatedBackground'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Validate if prompt makes sense
const validatePrompt = (prompt: string): { valid: boolean; error?: string } => {
  const trimmed = prompt.trim()
  
  if (trimmed.length < 3) {
    return { valid: false, error: 'Prompt is too short. Please describe what you want in more detail.' }
  }
  
  if (trimmed.length > 1000) {
    return { valid: false, error: 'Prompt is too long. Please keep it under 1000 characters.' }
  }
  
  // Check for repeated characters (like "aaaa" or "1111")
  const repeatedCharPattern = /^(.)\1{10,}$/
  if (repeatedCharPattern.test(trimmed)) {
    return { valid: false, error: 'Please enter a meaningful description, not just repeated characters.' }
  }
  
  // Check for only special characters or numbers
  const onlySpecialChars = /^[^a-zA-Z\s]{3,}$/
  if (onlySpecialChars.test(trimmed)) {
    return { valid: false, error: 'Please use words to describe your background, not just symbols or numbers.' }
  }
  
  // Basic word count check
  const wordCount = trimmed.split(/\s+/).filter(word => word.length > 0).length
  if (wordCount < 2) {
    return { valid: false, error: 'Please provide more details about what you want to see.' }
  }
  
  // All other validation (checking if it can be visualized) happens on the backend using AI
  // The backend uses GPT to intelligently determine if the prompt describes something visual
  return { valid: true }
}

export default function Home() {
  const [prompt, setPrompt] = useState('')
  const [imageUrl, setImageUrl] = useState<string | null>(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [mounted, setMounted] = useState(false)
  const [mode, setMode] = useState<'generate' | 'upload'>('generate')
  const [isInputFocused, setIsInputFocused] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    setMounted(true)
  }, [])

  const handleGenerate = async () => {
    if (!prompt.trim()) {
      setError('Please enter a prompt')
      return
    }

    // Validate prompt
    const validation = validatePrompt(prompt)
    if (!validation.valid) {
      setError(validation.error || 'Please enter a valid prompt')
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
        let errorText = ''
        try {
          errorText = await response.text()
          // Try to parse as JSON for better error messages
          try {
            const errorJson = JSON.parse(errorText)
            if (errorJson.detail) {
              errorText = errorJson.detail
            }
          } catch {
            // Not JSON, use as-is
          }
        } catch {
          errorText = `Server returned ${response.status}`
        }
        
        console.error('API error response:', errorText)
        
        // Check for OpenAI-specific errors
        if (errorText.includes('content_policy_violation') || errorText.includes('safety')) {
          throw new Error('This prompt may violate content policies. Please try a different description.')
        }
        
        // Check for validation errors
        if (errorText.includes("doesn't clearly describe") || errorText.includes("doesn't make sense")) {
          throw new Error('This prompt doesn\'t clearly describe a visual scene. Please describe what you want to see, like "a sunset over mountains" or "abstract geometric patterns".')
        }
        
        throw new Error(errorText || `Failed to generate image (${response.status})`)
      }

      const data = await response.json()
      console.log('Image URL received:', data.image_url)
      setImageUrl(data.image_url)
    } catch (err) {
      let errorMessage = 'An error occurred'
      
      if (err instanceof TypeError && err.message.includes('fetch')) {
        // Network error - failed to fetch
        errorMessage = 'Failed to connect to the server. Please check your internet connection and try again.'
      } else if (err instanceof Error) {
        errorMessage = err.message
      }
      
      setError(errorMessage)
      console.error('Error generating image:', err)
    } finally {
      setIsGenerating(false)
    }
  }

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    // Edge case: Empty file
    if (file.size === 0) {
      setError('The selected file is empty. Please choose a valid image file.')
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
      return
    }

    // Edge case: File too small (likely corrupted)
    if (file.size < 100) {
      setError('The file is too small and may be corrupted. Please choose a valid image file.')
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
      return
    }

    // Validate file type
    if (!file.type.startsWith('image/')) {
      setError('Please upload an image file (JPEG, PNG, GIF, etc.)')
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
      return
    }

    // Validate file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      setError('Image file is too large. Please upload an image smaller than 10MB.')
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
      return
    }

    setError(null)
    setIsGenerating(true)

    const reader = new FileReader()
    reader.onload = (e) => {
      const result = e.target?.result
      if (typeof result === 'string') {
        // Edge case: Validate image can actually load (catches corrupted files)
        const img = new Image()
        img.onload = () => {
          setImageUrl(result)
          setIsGenerating(false)
        }
        img.onerror = () => {
          setError('The file appears to be corrupted or is not a valid image. Please try a different file.')
          setIsGenerating(false)
          if (fileInputRef.current) {
            fileInputRef.current.value = ''
          }
        }
        img.src = result
      } else {
        setError('Failed to read the image file. Please try again.')
        setIsGenerating(false)
        if (fileInputRef.current) {
          fileInputRef.current.value = ''
        }
      }
    }
    reader.onerror = () => {
      setError('Failed to read the image file. Please try again.')
      setIsGenerating(false)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
    reader.readAsDataURL(file)
  }

  const handleUploadClick = () => {
    fileInputRef.current?.click()
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
      <BackgroundImage imageUrl={imageUrl} />
      <main className="relative min-h-screen" style={{ backgroundColor: 'transparent', position: 'relative', zIndex: 1 }}>
        <div className="relative z-10 flex flex-col items-center justify-center min-h-screen p-8" style={{ minHeight: '100vh' }}>
        <div className="w-full max-w-2xl">
          <h1 className="text-5xl font-bold text-white mb-8 text-center drop-shadow-2xl">
            AI Background Generator
          </h1>
          
          <div className="bg-black/80 backdrop-blur-md rounded-xl p-8 shadow-2xl border border-white/10 animate-fade-in">
            <div className="flex flex-col gap-5">
              {/* Mode Toggle */}
              <div className="flex gap-2 mb-2">
                <button
                  onClick={() => {
                    setMode('generate')
                    setError(null)
                    setImageUrl(null)
                  }}
                  className={`flex-1 px-4 py-2 rounded-lg font-medium transition-all ${
                    mode === 'generate'
                      ? 'bg-white text-black'
                      : 'bg-white/10 text-white hover:bg-white/20'
                  }`}
                >
                  Generate with AI
                </button>
                <button
                  onClick={() => {
                    setMode('upload')
                    setError(null)
                    setImageUrl(null)
                  }}
                  className={`flex-1 px-4 py-2 rounded-lg font-medium transition-all ${
                    mode === 'upload'
                      ? 'bg-white text-black'
                      : 'bg-white/10 text-white hover:bg-white/20'
                  }`}
                >
                  Upload Image
                </button>
              </div>

              {/* Generate Mode */}
              {mode === 'generate' && (
                <div>
                  <label htmlFor="prompt" className="block text-white text-sm font-medium mb-3">
                    What background would you like to create? 🎨
                  </label>
                  <input
                    id="prompt"
                    type="text"
                    value={prompt}
                    onChange={(e) => {
                      setPrompt(e.target.value)
                      setError(null) // Clear error when user types
                    }}
                    onFocus={() => setIsInputFocused(true)}
                    onBlur={() => setIsInputFocused(false)}
                    onKeyPress={handleKeyPress}
                    placeholder="Describe your ideal background... Try: 'serene mountain landscape at sunset', 'futuristic cityscape with neon lights', 'tropical beach with palm trees', 'cozy coffee shop interior'..."
                    className={`w-full px-5 py-4 rounded-lg text-white placeholder-white/40 border border-white/20 focus:outline-none focus:ring-2 focus:ring-white/50 focus:border-transparent transition-all text-lg ${
                      imageUrl && !isInputFocused && !prompt.trim()
                        ? 'bg-transparent backdrop-blur-sm'
                        : 'bg-white/10 backdrop-blur-sm'
                    }`}
                    disabled={isGenerating}
                  />
                  <button
                    onClick={handleGenerate}
                    disabled={isGenerating || !prompt.trim()}
                    className="w-full mt-4 px-6 py-4 bg-white text-black font-bold rounded-lg hover:bg-white/90 disabled:opacity-50 disabled:cursor-not-allowed transition-all transform hover:scale-105 active:scale-95 text-lg shadow-lg"
                  >
                    {isGenerating ? (
                      <span className="flex items-center justify-center gap-2">
                        <span className="animate-spin">⏳</span>
                        Generating...
                      </span>
                    ) : (
                      'Generate Background'
                    )}
                  </button>
                </div>
              )}

              {/* Upload Mode */}
              {mode === 'upload' && (
                <div>
                  <label htmlFor="file-upload" className="block text-white text-sm font-medium mb-3">
                    Upload your own background image 📸
                  </label>
                  <input
                    ref={fileInputRef}
                    id="file-upload"
                    type="file"
                    accept="image/*"
                    onChange={handleFileUpload}
                    className="hidden"
                    disabled={isGenerating}
                  />
                  <button
                    onClick={handleUploadClick}
                    disabled={isGenerating}
                    className="w-full px-6 py-4 bg-white text-black font-bold rounded-lg hover:bg-white/90 disabled:opacity-50 disabled:cursor-not-allowed transition-all transform hover:scale-105 active:scale-95 text-lg shadow-lg"
                  >
                    {isGenerating ? (
                      <span className="flex items-center justify-center gap-2">
                        <span className="animate-spin">⏳</span>
                        Processing...
                      </span>
                    ) : (
                      'Choose Image File'
                    )}
                  </button>
                  <p className="text-white/60 text-sm mt-2 text-center">
                    Supports JPEG, PNG, GIF (max 10MB)
                  </p>
                </div>
              )}
              
              {error && (
                <div className="bg-red-500/20 border border-red-500/50 text-red-200 px-4 py-3 rounded-lg animate-fade-in">
                  {error}
                </div>
              )}
            </div>
          </div>
          
        </div>
      </div>
      </main>
    </div>
  )
}

