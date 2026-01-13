'use client'

import { useState, useEffect, useRef } from 'react'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

type SpaceView = 'stars' | 'nebula' | 'galaxy' | 'planets' | 'cosmic'

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [animationKey, setAnimationKey] = useState(0)
  const [currentSpaceView, setCurrentSpaceView] = useState<SpaceView>('stars')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const progressIntervalRef = useRef<NodeJS.Timeout | null>(null)
  const spaceContainerRef = useRef<HTMLDivElement>(null)
  const floatingObjectsRef = useRef<HTMLDivElement>(null)

  // Generate space view based on current view type
  const generateSpaceView = (viewType: SpaceView) => {
    const spaceContainer = spaceContainerRef.current
    if (!spaceContainer) return

    spaceContainer.innerHTML = ''
    
    // Update background class
    spaceContainer.className = `space-bg space-view-${viewType}`

    if (viewType === 'stars') {
      // Realistic night sky with proper star distribution
      const starCount = 500
      // Create star clusters for realism
      const clusters = 8
      for (let c = 0; c < clusters; c++) {
        const clusterX = Math.random() * 100
        const clusterY = Math.random() * 100
        const clusterSize = Math.random() * 15 + 10
        
        for (let i = 0; i < starCount / clusters; i++) {
          const star = document.createElement('div')
          const size = Math.random()
          let starClass = 'star star-small'
          const distance = Math.random() * clusterSize
          const angle = Math.random() * Math.PI * 2
          
          if (size > 0.85) {
            starClass = 'star star-large'
            star.style.width = `${Math.random() * 1.2 + 1.8}px`
            star.style.height = star.style.width
          } else if (size > 0.6) {
            starClass = 'star star-medium'
            star.style.width = `${Math.random() * 0.7 + 1}px`
            star.style.height = star.style.width
          } else {
            star.style.width = `${Math.random() * 0.4 + 0.4}px`
            star.style.height = star.style.width
          }
          
          star.className = starClass
          star.style.left = `${Math.max(0, Math.min(100, clusterX + Math.cos(angle) * distance))}%`
          star.style.top = `${Math.max(0, Math.min(100, clusterY + Math.sin(angle) * distance))}%`
          star.style.animationDelay = `${Math.random() * 4}s`
          spaceContainer.appendChild(star)
        }
      }
      
      // Add some scattered stars for depth
      for (let i = 0; i < 100; i++) {
        const star = document.createElement('div')
        star.className = 'star star-small'
        star.style.width = `${Math.random() * 0.5 + 0.3}px`
        star.style.height = star.style.width
        star.style.left = `${Math.random() * 100}%`
        star.style.top = `${Math.random() * 100}%`
        star.style.opacity = `${Math.random() * 0.5 + 0.3}`
        spaceContainer.appendChild(star)
      }
    } else if (viewType === 'nebula') {
      // Realistic nebula with cloud formations
      // Create nebula cloud layers
      for (let layer = 0; layer < 5; layer++) {
        const cloudX = Math.random() * 100
        const cloudY = Math.random() * 100
        const cloudSize = Math.random() * 30 + 20
        const hue = Math.random() * 60 + 250
        
        for (let i = 0; i < 80; i++) {
          const particle = document.createElement('div')
          const distance = Math.random() * cloudSize
          const angle = Math.random() * Math.PI * 2
          const size = Math.random() * 3 + 1
          
          particle.style.width = `${size}px`
          particle.style.height = `${size}px`
          particle.style.left = `${Math.max(0, Math.min(100, cloudX + Math.cos(angle) * distance))}%`
          particle.style.top = `${Math.max(0, Math.min(100, cloudY + Math.sin(angle) * distance))}%`
          particle.style.background = `hsla(${hue}, ${70 + Math.random() * 20}%, ${60 + Math.random() * 20}%, ${0.3 + Math.random() * 0.4})`
          particle.style.borderRadius = '50%'
          particle.style.boxShadow = `0 0 ${size * 3}px hsla(${hue}, 70%, 70%, 0.6)`
          particle.style.filter = 'blur(0.5px)'
          spaceContainer.appendChild(particle)
        }
      }
      
      // Add background stars
      for (let i = 0; i < 150; i++) {
        const star = document.createElement('div')
        star.className = 'star star-small'
        star.style.width = `${Math.random() * 0.8 + 0.4}px`
        star.style.height = star.style.width
        star.style.left = `${Math.random() * 100}%`
        star.style.top = `${Math.random() * 100}%`
        star.style.opacity = `${Math.random() * 0.6 + 0.2}`
        spaceContainer.appendChild(star)
      }
    } else if (viewType === 'galaxy') {
      // Realistic spiral galaxy
      const centerX = 50
      const centerY = 50
      const arms = 2
      
      for (let arm = 0; arm < arms; arm++) {
        const armAngle = (arm * Math.PI * 2) / arms
        for (let i = 0; i < 200; i++) {
          const star = document.createElement('div')
          const distance = Math.random() * 45
          const spiral = distance * 0.15
          const angle = armAngle + spiral + (Math.random() - 0.5) * 0.5
          const x = centerX + Math.cos(angle) * distance
          const y = centerY + Math.sin(angle) * distance
          
          if (x >= 0 && x <= 100 && y >= 0 && y <= 100) {
            const size = Math.random() * 1.2 + 0.5
            star.style.width = `${size}px`
            star.style.height = `${size}px`
            star.style.left = `${x}%`
            star.style.top = `${y}%`
            const brightness = Math.max(0.3, 1 - distance / 50)
            star.style.background = `rgba(255, 255, 255, ${brightness})`
            star.style.boxShadow = `0 0 ${size * 2}px rgba(255, 255, 255, ${brightness * 0.5})`
            spaceContainer.appendChild(star)
          }
        }
      }
      
      // Add central bulge
      for (let i = 0; i < 100; i++) {
        const star = document.createElement('div')
        const distance = Math.random() * 8
        const angle = Math.random() * Math.PI * 2
        const x = centerX + Math.cos(angle) * distance
        const y = centerY + Math.sin(angle) * distance
        
        star.style.width = `${Math.random() * 1.5 + 1}px`
        star.style.height = star.style.width
        star.style.left = `${x}%`
        star.style.top = `${y}%`
        star.style.background = `rgba(255, 255, 200, ${Math.random() * 0.5 + 0.5})`
        star.style.boxShadow = `0 0 4px rgba(255, 255, 200, 0.8)`
        spaceContainer.appendChild(star)
      }
    } else if (viewType === 'planets') {
      // Realistic starfield background
      for (let i = 0; i < 200; i++) {
        const star = document.createElement('div')
        star.className = 'star star-small'
        star.style.width = `${Math.random() * 0.8 + 0.4}px`
        star.style.height = star.style.width
        star.style.left = `${Math.random() * 100}%`
        star.style.top = `${Math.random() * 100}%`
        star.style.opacity = `${Math.random() * 0.7 + 0.3}`
        spaceContainer.appendChild(star)
      }
      
      // Add realistic planets with textures
      const planets = [
        { 
          size: 140, 
          left: '15%', 
          top: '25%', 
          color: 'linear-gradient(135deg, rgba(100, 120, 180, 0.8) 0%, rgba(60, 80, 140, 0.9) 100%)',
          glow: 'rgba(100, 150, 255, 0.4)',
          rings: true
        },
        { 
          size: 100, 
          left: '75%', 
          top: '55%', 
          color: 'linear-gradient(135deg, rgba(200, 150, 100, 0.7) 0%, rgba(150, 100, 60, 0.8) 100%)',
          glow: 'rgba(255, 180, 100, 0.3)',
          rings: false
        },
        { 
          size: 80, 
          left: '45%', 
          top: '75%', 
          color: 'linear-gradient(135deg, rgba(150, 200, 255, 0.6) 0%, rgba(100, 150, 200, 0.7) 100%)',
          glow: 'rgba(150, 200, 255, 0.3)',
          rings: false
        },
      ]
      
      planets.forEach((planet) => {
        const planetEl = document.createElement('div')
        planetEl.className = 'planet planet-pulse'
        planetEl.style.width = `${planet.size}px`
        planetEl.style.height = `${planet.size}px`
        planetEl.style.left = planet.left
        planetEl.style.top = planet.top
        planetEl.style.background = planet.color
        planetEl.style.boxShadow = `0 0 ${planet.size}px ${planet.glow}, inset -20px -20px 40px rgba(0, 0, 0, 0.5)`
        planetEl.style.borderRadius = '50%'
        
        // Add planet texture
        const texture = document.createElement('div')
        texture.style.position = 'absolute'
        texture.style.width = '100%'
        texture.style.height = '100%'
        texture.style.borderRadius = '50%'
        texture.style.background = `radial-gradient(circle at 30% 30%, rgba(255, 255, 255, 0.1) 0%, transparent 50%)`
        texture.style.opacity = '0.6'
        planetEl.appendChild(texture)
        
        spaceContainer.appendChild(planetEl)
        
        // Add rings if specified
        if (planet.rings) {
          const ring = document.createElement('div')
          ring.style.position = 'absolute'
          ring.style.width = `${planet.size * 1.6}px`
          ring.style.height = `${planet.size * 0.3}px`
          ring.style.left = `calc(${planet.left} - ${planet.size * 0.3}px)`
          ring.style.top = `calc(${planet.top} + ${planet.size * 0.35}px)`
          ring.style.border = `2px solid rgba(200, 200, 255, 0.3)`
          ring.style.borderRadius = '50%'
          ring.style.boxShadow = `0 0 20px rgba(200, 200, 255, 0.2)`
          spaceContainer.appendChild(ring)
        }
      })
    } else if (viewType === 'cosmic') {
      // Realistic cosmic view with depth
      // Background stars (dimmer, smaller)
      for (let i = 0; i < 300; i++) {
        const star = document.createElement('div')
        star.className = 'star star-small'
        star.style.width = `${Math.random() * 0.6 + 0.3}px`
        star.style.height = star.style.width
        star.style.left = `${Math.random() * 100}%`
        star.style.top = `${Math.random() * 100}%`
        star.style.opacity = `${Math.random() * 0.4 + 0.2}`
        spaceContainer.appendChild(star)
      }
      
      // Foreground stars (brighter, colorful)
      for (let i = 0; i < 150; i++) {
        const star = document.createElement('div')
        const size = Math.random()
        if (size > 0.7) {
          star.className = 'star star-large'
          star.style.width = `${Math.random() * 1.5 + 1.5}px`
          star.style.height = star.style.width
        } else {
          star.className = 'star star-medium'
          star.style.width = `${Math.random() * 1 + 0.8}px`
          star.style.height = star.style.width
        }
        
        star.style.left = `${Math.random() * 100}%`
        star.style.top = `${Math.random() * 100}%`
        const hue = Math.random() * 60 + 200 // Blue to purple range
        const saturation = 60 + Math.random() * 30
        const lightness = 60 + Math.random() * 20
        star.style.background = `hsl(${hue}, ${saturation}%, ${lightness}%)`
        star.style.boxShadow = `0 0 ${parseFloat(star.style.width) * 3}px hsl(${hue}, ${saturation}%, ${lightness}%)`
        spaceContainer.appendChild(star)
      }
    }
  }

  // Initialize space view
  useEffect(() => {
    generateSpaceView(currentSpaceView)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentSpaceView])

  // Create floating space objects that are always present
  useEffect(() => {
    const floatingContainer = floatingObjectsRef.current
    if (!floatingContainer) return

    floatingContainer.innerHTML = ''

    // Create floating asteroids
    for (let i = 0; i < 20; i++) {
      const asteroid = document.createElement('div')
      asteroid.className = 'floating-asteroid'
      const size = Math.random() * 25 + 10
      const gray1 = Math.floor(Math.random() * 100 + 100)
      const gray2 = Math.floor(Math.random() * 50)
      
      asteroid.style.setProperty('--size', `${size}px`)
      asteroid.style.width = `${size}px`
      asteroid.style.height = `${size}px`
      asteroid.style.left = `${Math.random() * 100}%`
      asteroid.style.top = `${Math.random() * 100}%`
      asteroid.style.background = `linear-gradient(135deg, rgb(${gray1}, ${gray1}, ${gray1}) 0%, rgb(${gray2}, ${gray2}, ${gray2}) 100%)`
      asteroid.style.animationDuration = `${Math.random() * 20 + 15}s`
      asteroid.style.animationDelay = `${Math.random() * 5}s`
      floatingContainer.appendChild(asteroid)
    }

    // Create floating small planets
    const planetColors = [
      { color: 'linear-gradient(135deg, rgba(100, 150, 200, 0.7) 0%, rgba(60, 100, 150, 0.7) 100%)', glow: 'rgba(100, 150, 255, 0.4)' },
      { color: 'linear-gradient(135deg, rgba(200, 150, 100, 0.7) 0%, rgba(150, 100, 60, 0.7) 100%)', glow: 'rgba(255, 180, 100, 0.4)' },
      { color: 'linear-gradient(135deg, rgba(150, 200, 255, 0.7) 0%, rgba(100, 150, 200, 0.7) 100%)', glow: 'rgba(150, 200, 255, 0.4)' },
      { color: 'linear-gradient(135deg, rgba(255, 200, 150, 0.7) 0%, rgba(200, 150, 100, 0.7) 100%)', glow: 'rgba(255, 200, 150, 0.4)' },
    ]

    for (let i = 0; i < 8; i++) {
      const planet = document.createElement('div')
      planet.className = 'floating-planet'
      const size = Math.random() * 60 + 40
      const planetData = planetColors[Math.floor(Math.random() * planetColors.length)]
      
      planet.style.setProperty('--size', `${size}px`)
      planet.style.setProperty('--glow', planetData.glow)
      planet.style.setProperty('--bg-color', planetData.color)
      planet.style.width = `${size}px`
      planet.style.height = `${size}px`
      planet.style.background = planetData.color
      planet.style.left = `${Math.random() * 100}%`
      planet.style.top = `${Math.random() * 100}%`
      planet.style.animationDuration = `${Math.random() * 25 + 20}s`
      planet.style.animationDelay = `${Math.random() * 5}s`
      floatingContainer.appendChild(planet)
    }

    // Create floating nebula clouds
    for (let i = 0; i < 10; i++) {
      const nebula = document.createElement('div')
      nebula.className = 'floating-nebula'
      const size = Math.random() * 300 + 150
      const hues = [250, 280, 300, 320]
      const hue = hues[Math.floor(Math.random() * hues.length)]
      
      nebula.style.setProperty('--size', `${size}px`)
      nebula.style.setProperty('--color', `hsla(${hue}, 70%, 60%, 0.3)`)
      nebula.style.width = `${size}px`
      nebula.style.height = `${size}px`
      nebula.style.left = `${Math.random() * 100}%`
      nebula.style.top = `${Math.random() * 100}%`
      nebula.style.animationDuration = `${Math.random() * 30 + 25}s`
      nebula.style.animationDelay = `${Math.random() * 5}s`
      floatingContainer.appendChild(nebula)
    }

    // Create floating space debris
    for (let i = 0; i < 15; i++) {
      const debris = document.createElement('div')
      debris.className = 'floating-debris'
      const size = Math.random() * 8 + 3
      debris.style.width = `${size}px`
      debris.style.height = `${size}px`
      debris.style.left = `${Math.random() * 100}%`
      debris.style.top = `${Math.random() * 100}%`
      debris.style.background = `rgba(150, 150, 150, ${Math.random() * 0.5 + 0.3})`
      debris.style.animationDuration = `${Math.random() * 15 + 10}s`
      debris.style.animationDelay = `${Math.random() * 5}s`
      floatingContainer.appendChild(debris)
    }

    return () => {
      floatingContainer.innerHTML = ''
    }
  }, [])

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Progress bar animation
  useEffect(() => {
    if (loading) {
      setProgress(0)
      progressIntervalRef.current = setInterval(() => {
        setProgress((prev) => {
          if (prev >= 95) return prev
          return prev + Math.random() * 3
        })
      }, 100)
    } else {
      if (progressIntervalRef.current) {
        clearInterval(progressIntervalRef.current)
        progressIntervalRef.current = null
      }
      setProgress(100)
      setTimeout(() => setProgress(0), 500)
    }

    return () => {
      if (progressIntervalRef.current) {
        clearInterval(progressIntervalRef.current)
      }
    }
  }, [loading])

  const sendMessage = async () => {
    if (!input.trim() || loading) return

    const userMessage = input.trim()
    setInput('')
    setMessages((prev) => [...prev, { role: 'user', content: userMessage }])
    setLoading(true)

    try {
      // Use localhost only when actually on localhost, otherwise use current origin (Vercel)
      const apiUrl = typeof window !== 'undefined' && window.location.hostname === 'localhost'
        ? 'http://localhost:8000'
        : ''
      const response = await fetch(`${apiUrl}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: userMessage }),
      })

      if (!response.ok) {
        throw new Error('Failed to get response')
      }

      const data = await response.json()
      setMessages((prev) => [...prev, { role: 'assistant', content: data.reply }])
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: 'Error: Failed to connect to the backend. Make sure the server is running on http://localhost:8000' },
      ])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <main className="relative h-screen w-screen overflow-hidden bg-black">
      {/* Space Background */}
      <div ref={spaceContainerRef} className="space-bg"></div>

      {/* Floating Space Objects */}
      <div ref={floatingObjectsRef} className="floating-objects-container"></div>

      {/* Main Content */}
      <div className="relative z-10 flex h-full flex-col">
        {/* Header */}
        <header className="border-b-2 border-cyan-400 bg-black bg-opacity-80 p-4 backdrop-blur-sm">
          <h1 className="glitch-text text-center text-3xl font-bold text-cyan-400">
            &gt; STELLAR_AI
          </h1>
          <p className="text-center text-sm text-cyan-300">Personal Assistant from Space 🚀</p>
        </header>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="mx-auto max-w-4xl space-y-4">
            {messages.length === 0 && (
              <div className="text-center text-cyan-400">
                <p className="text-lg">[SYSTEM] STELLAR_AI initialized...</p>
                <p className="mt-2 text-sm opacity-70">Ready to assist. Type a message to begin</p>
              </div>
            )}
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`rounded border-2 p-4 ${
                  msg.role === 'user'
                    ? 'ml-auto max-w-[80%] border-purple-500 bg-purple-900 bg-opacity-30 text-purple-200'
                    : 'mr-auto max-w-[80%] border-cyan-500 bg-cyan-900 bg-opacity-30 text-cyan-200'
                }`}
              >
                <div className="mb-1 text-xs opacity-70">
                  {msg.role === 'user' ? '[USER]' : '[ASSISTANT]'}
                </div>
                <div className="whitespace-pre-wrap">{msg.content}</div>
              </div>
            ))}
            {loading && (
              <div className="mr-auto max-w-[80%] rounded border-2 border-cyan-500 bg-cyan-900 bg-opacity-30 p-4 text-cyan-200">
                <div className="mb-1 text-xs opacity-70">[SYSTEM] Processing across quantum networks...</div>
                <div className="text-sm">Awaiting response from STELLAR_AI...</div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Progress Bar */}
        {loading && (
          <div className="border-t-2 border-cyan-500 bg-black bg-opacity-80 p-2 backdrop-blur-sm">
            <div className="mx-auto max-w-4xl">
              <div className="mb-1 text-xs text-cyan-400">[QUANTUM_PROCESSING]</div>
              <div className="h-2 w-full overflow-hidden rounded bg-black border border-cyan-500">
                <div
                  className="h-full bg-gradient-to-r from-cyan-500 via-blue-500 to-purple-500 transition-all duration-100"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <div className="mt-1 text-right text-xs text-cyan-400">
                {Math.round(progress)}% - Neural networks active
              </div>
            </div>
          </div>
        )}

        {/* Input Area */}
        <div className="border-t-2 border-cyan-500 bg-black bg-opacity-80 p-4 backdrop-blur-sm">
          <div className="mx-auto flex max-w-4xl gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your message... (Press Enter to send)"
              disabled={loading}
              className="flex-1 rounded border-2 border-cyan-500 bg-black p-3 text-cyan-400 placeholder-cyan-600 focus:border-cyan-300 focus:outline-none focus:ring-2 focus:ring-cyan-500 disabled:opacity-50"
            />
            <button
              onClick={sendMessage}
              disabled={loading || !input.trim()}
              className="rounded border-2 border-cyan-500 bg-cyan-900 bg-opacity-30 px-6 py-3 font-bold text-cyan-400 transition-all hover:bg-cyan-800 hover:text-cyan-300 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              &gt; LAUNCH
            </button>
          </div>
        </div>
      </div>
    </main>
  )
}