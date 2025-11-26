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

  // Comprehensive image upload validation
  const validateImageFile = (file: File): { valid: boolean; error?: string } => {
    // 1. Check if file exists
    if (!file) {
      return { valid: false, error: 'No file selected. Please choose an image file.' }
    }

    // 2. Check for empty files
    if (file.size === 0) {
      return { valid: false, error: 'The selected file is empty. Please choose a valid image file.' }
    }

    // 3. Check minimum file size (files smaller than 100 bytes are likely corrupted)
    if (file.size < 100) {
      return { valid: false, error: 'The file is too small and may be corrupted. Please choose a valid image file.' }
    }

    // 4. Check maximum file size (10MB)
    const maxSize = 10 * 1024 * 1024 // 10MB
    if (file.size > maxSize) {
      const sizeMB = (file.size / (1024 * 1024)).toFixed(2)
      return { valid: false, error: `Image file is too large (${sizeMB}MB). Please upload an image smaller than 10MB.` }
    }

    // 5. Validate file extension
    const validExtensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg']
    const fileName = file.name.toLowerCase()
    const hasValidExtension = validExtensions.some(ext => fileName.endsWith(ext))
    
    if (!hasValidExtension) {
      return { valid: false, error: 'Invalid file type. Please upload a JPEG, PNG, GIF, WebP, BMP, or SVG image.' }
    }

    // 6. Validate MIME type (more specific than just 'image/')
    const validMimeTypes = [
      'image/jpeg',
      'image/jpg',
      'image/png',
      'image/gif',
      'image/webp',
      'image/bmp',
      'image/svg+xml',
      'image/x-icon',
      'image/vnd.microsoft.icon'
    ]
    
    // Check if MIME type is valid or if file type is empty (some browsers don't set it)
    if (file.type && !validMimeTypes.includes(file.type.toLowerCase())) {
      // If MIME type is set but invalid, reject it
      if (file.type.startsWith('image/')) {
        // Some browsers report generic 'image/*' - allow if extension is valid
        if (file.type === 'image/*' && hasValidExtension) {
          // Allow through, will validate by loading image
        } else {
          return { valid: false, error: `Unsupported image format (${file.type}). Please use JPEG, PNG, GIF, or WebP.` }
        }
      } else {
        return { valid: false, error: 'Please upload an image file (JPEG, PNG, GIF, WebP, etc.)' }
      }
    }

    // 7. Check for suspicious file names (potential security issue)
    if (fileName.includes('..') || fileName.includes('/') || fileName.includes('\\')) {
      return { valid: false, error: 'Invalid file name. Please use a valid image file.' }
    }

    // 8. Check for extremely long file names (potential DoS)
    if (file.name.length > 255) {
      return { valid: false, error: 'File name is too long. Please rename the file and try again.' }
    }

    return { valid: true }
  }

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    
    // Validate file
    const validation = validateImageFile(file)
    if (!validation.valid) {
      setError(validation.error || 'Invalid file. Please try again.')
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
      return
    }

    setError(null)
    setIsGenerating(true)

    // Create image object to validate it's actually an image and get dimensions
    const img = new Image()
    const reader = new FileReader()

    // Set up image load handler (validates the image can actually be loaded)
    img.onload = () => {
      // 9. Validate image dimensions
      const maxDimension = 10000 // 10,000 pixels max per side
      const minDimension = 1 // At least 1 pixel
      
      if (img.width < minDimension || img.height < minDimension) {
        setError('Image dimensions are too small. Please upload a valid image.')
        setIsGenerating(false)
        if (fileInputRef.current) {
          fileInputRef.current.value = ''
        }
        return
      }

      if (img.width > maxDimension || img.height > maxDimension) {
        setError(`Image dimensions are too large (${img.width}x${img.height}). Maximum size is 10,000x10,000 pixels.`)
        setIsGenerating(false)
        if (fileInputRef.current) {
          fileInputRef.current.value = ''
        }
        return
      }

      // 10. Check for extremely large images that might cause memory issues
      // Estimate memory usage: width * height * 4 bytes (RGBA)
      const estimatedMemoryMB = (img.width * img.height * 4) / (1024 * 1024)
      if (estimatedMemoryMB > 500) { // 500MB memory limit
        setError('Image is too large and may cause performance issues. Please use a smaller image.')
        setIsGenerating(false)
        if (fileInputRef.current) {
          fileInputRef.current.value = ''
        }
        return
      }

      // Image is valid, set it
      if (reader.result && typeof reader.result === 'string') {
        setImageUrl(reader.result)
        setIsGenerating(false)
      }
    }

    img.onerror = () => {
      // 11. Handle corrupted or invalid image files
      setError('The file appears to be corrupted or is not a valid image. Please try a different file.')
      setIsGenerating(false)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }

    // Set up FileReader handlers
    reader.onload = (e) => {
      const result = e.target?.result
      if (typeof result === 'string') {
        // Try to load the image to validate it's actually an image
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
      // 12. Handle FileReader errors
      setError('Failed to read the image file. The file may be corrupted or inaccessible.')
      setIsGenerating(false)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }

    reader.onabort = () => {
      // 13. Handle user cancellation
      setError('File upload was cancelled.')
      setIsGenerating(false)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }

    // Start reading the file
    try {
      reader.readAsDataURL(file)
    } catch (error) {
      // 14. Handle unexpected errors during file reading
      console.error('Error reading file:', error)
      setError('An unexpected error occurred while reading the file. Please try again.')
      setIsGenerating(false)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
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
                    onKeyPress={handleKeyPress}
                    placeholder="Describe your ideal background... Try: 'serene mountain landscape at sunset', 'futuristic cityscape with neon lights', 'tropical beach with palm trees', 'cozy coffee shop interior'..."
                    className="w-full px-5 py-4 rounded-lg bg-white/10 text-white placeholder-white/40 border border-white/20 focus:outline-none focus:ring-2 focus:ring-white/50 focus:border-transparent transition-all text-lg"
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
                    accept="image/jpeg,image/jpg,image/png,image/gif,image/webp,image/bmp,image/svg+xml"
                    multiple={false}
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
                    Supports JPEG, PNG, GIF, WebP, BMP, SVG (max 10MB, max 10,000x10,000px)
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

