'use client'

import { useState, useEffect } from 'react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface LearningStep {
  title: string
  description: string
}

interface Example {
  title: string
  url: string
  description: string
}

interface LearningResponse {
  plan: LearningStep[]
  examples: Example[]
}

export default function Home() {
  const [topic, setTopic] = useState('')
  const [learningData, setLearningData] = useState<LearningResponse | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  const handleLearn = async () => {
    if (!topic.trim()) {
      setError('Please enter a topic you want to learn about')
      return
    }

    if (topic.trim().length < 3) {
      setError('Please provide more details about what you want to learn')
      return
    }

    setIsLoading(true)
    setError(null)
    setLearningData(null)

    try {
      const response = await fetch(`${API_URL}/api/learn`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ topic: topic.trim() }),
      })

      if (!response.ok) {
        let errorText = ''
        try {
          errorText = await response.text()
          const errorJson = JSON.parse(errorText)
          if (errorJson.detail) {
            errorText = errorJson.detail
          }
        } catch {
          errorText = `Server returned ${response.status}`
        }
        throw new Error(errorText || `Failed to create learning plan (${response.status})`)
      }

      const data: LearningResponse = await response.json()
      setLearningData(data)
    } catch (err) {
      let errorMessage = 'An error occurred'
      if (err instanceof TypeError && err.message.includes('fetch')) {
        errorMessage = 'Failed to connect to the server. Please check your internet connection and try again.'
      } else if (err instanceof Error) {
        errorMessage = err.message
      }
      setError(errorMessage)
      console.error('Error creating learning plan:', err)
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !isLoading) {
      handleLearn()
    }
  }

  if (!mounted) {
    return null
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-black text-white">
      <main className="container mx-auto px-4 py-12 max-w-4xl">
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold mb-4 bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent">
            Learning Experience
          </h1>
          <p className="text-xl text-gray-300">
            Ask to learn about anything, and we'll create a personalized plan with real examples!
          </p>
        </div>

        <div className="bg-white/10 backdrop-blur-md rounded-xl p-8 shadow-2xl border border-white/20 mb-8">
          <div className="flex flex-col gap-4">
            <label htmlFor="topic" className="block text-white text-lg font-medium">
              What would you like to learn about? 🎓
            </label>
            <input
              id="topic"
              type="text"
              value={topic}
              onChange={(e) => {
                setTopic(e.target.value)
                setError(null)
              }}
              onKeyPress={handleKeyPress}
              placeholder="e.g., 'Python programming', 'Machine Learning', 'Web Development', 'Cooking Italian food'..."
              className="w-full px-5 py-4 rounded-lg text-white placeholder-white/40 border border-white/20 bg-white/10 backdrop-blur-sm focus:outline-none focus:ring-2 focus:ring-purple-400 focus:border-transparent transition-all text-lg"
              disabled={isLoading}
            />
            <button
              onClick={handleLearn}
              disabled={isLoading || !topic.trim()}
              className="w-full px-6 py-4 bg-gradient-to-r from-purple-600 to-blue-600 text-white font-bold rounded-lg hover:from-purple-700 hover:to-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all transform hover:scale-105 active:scale-95 text-lg shadow-lg"
            >
              {isLoading ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="animate-spin">⏳</span>
                  Creating your learning plan...
                </span>
              ) : (
                'Start Learning'
              )}
            </button>
          </div>

          {error && (
            <div className="mt-4 bg-red-500/20 border border-red-500/50 text-red-200 px-4 py-3 rounded-lg animate-fade-in">
              {error}
            </div>
          )}
        </div>

        {learningData && (
          <div className="space-y-8 animate-fade-in">
            {/* Learning Plan */}
            <div className="bg-white/10 backdrop-blur-md rounded-xl p-8 shadow-2xl border border-white/20">
              <h2 className="text-3xl font-bold mb-6 text-purple-300">Your Learning Plan</h2>
              <div className="space-y-6">
                {learningData.plan.map((step, index) => (
                  <div
                    key={index}
                    className="bg-white/5 rounded-lg p-6 border border-white/10 hover:bg-white/10 transition-all"
                  >
                    <div className="flex items-start gap-4">
                      <div className="flex-shrink-0 w-10 h-10 rounded-full bg-gradient-to-r from-purple-500 to-blue-500 flex items-center justify-center font-bold text-lg">
                        {index + 1}
                      </div>
                      <div className="flex-1">
                        <h3 className="text-xl font-semibold mb-2 text-purple-200">{step.title}</h3>
                        <p className="text-gray-300 leading-relaxed">{step.description}</p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Real Examples */}
            <div className="bg-white/10 backdrop-blur-md rounded-xl p-8 shadow-2xl border border-white/20">
              <h2 className="text-3xl font-bold mb-6 text-blue-300">Real Examples & Resources</h2>
              <div className="grid gap-4 md:grid-cols-2">
                {learningData.examples.map((example, index) => (
                  <a
                    key={index}
                    href={example.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block bg-white/5 rounded-lg p-5 border border-white/10 hover:bg-white/10 hover:border-purple-400/50 transition-all group"
                  >
                    <h3 className="text-lg font-semibold mb-2 text-purple-200 group-hover:text-purple-100 transition-colors">
                      {example.title}
                    </h3>
                    <p className="text-sm text-gray-400 mb-2">{example.description}</p>
                    <p className="text-xs text-blue-400 truncate">{example.url}</p>
                  </a>
                ))}
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
