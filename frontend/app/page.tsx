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
  message?: string
}

interface ExpandedStep {
  additionalContext?: string
  practicalDetails?: string[]
  importantConsiderations?: string[]
  realWorldExamples?: string[]
  potentialChallenges?: string[]
}

export default function Home() {
  const [topic, setTopic] = useState('')
  const [learningData, setLearningData] = useState<LearningResponse | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [mounted, setMounted] = useState(false)
  const [expandedSteps, setExpandedSteps] = useState<Record<number, ExpandedStep>>({})
  const [expandingStep, setExpandingStep] = useState<number | null>(null)

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

  const handleExpandStep = async (index: number, step: LearningStep) => {
    // If already expanded, collapse it
    if (expandedSteps[index]) {
      const newExpanded = { ...expandedSteps }
      delete newExpanded[index]
      setExpandedSteps(newExpanded)
      return
    }

    // If already expanding, don't do anything
    if (expandingStep === index) {
      return
    }

    setExpandingStep(index)

    try {
      const response = await fetch(`${API_URL}/api/expand-step`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          topic: topic.trim(),
          step_title: step.title,
          step_description: step.description,
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to expand step')
      }

      const expanded: ExpandedStep = await response.json()
      setExpandedSteps({ ...expandedSteps, [index]: expanded })
    } catch (err) {
      console.error('Error expanding step:', err)
      setError('Failed to load detailed information. Please try again.')
    } finally {
      setExpandingStep(null)
    }
  }

  if (!mounted) {
    return null
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-950 via-purple-900 via-blue-900 to-slate-900 text-white relative overflow-hidden">
      {/* Animated background elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-blue-500/20 rounded-full blur-3xl animate-pulse delay-1000"></div>
        <div className="absolute top-1/2 right-0 w-72 h-72 bg-indigo-500/20 rounded-full blur-3xl animate-pulse delay-2000"></div>
      </div>

      <main className="container mx-auto px-4 py-16 max-w-5xl relative z-10">
        {/* Header Section */}
        <div className="text-center mb-16 animate-fade-in">
          <div className="inline-block mb-6">
            <h1 className="text-6xl md:text-7xl font-extrabold mb-4 bg-gradient-to-r from-purple-400 via-pink-400 to-blue-400 bg-clip-text text-transparent animate-gradient">
              Learning Experience
            </h1>
            <div className="h-1 w-24 bg-gradient-to-r from-purple-500 to-blue-500 mx-auto rounded-full"></div>
          </div>
          <p className="text-xl md:text-2xl text-gray-300 font-light max-w-2xl mx-auto leading-relaxed">
            Ask to learn about anything, and we'll create a personalized plan with real examples!
          </p>
        </div>

        {/* Input Card */}
        <div className="bg-white/5 backdrop-blur-xl rounded-2xl p-8 md:p-10 shadow-2xl border border-white/10 mb-12 hover:bg-white/10 transition-all duration-300 animate-fade-in hover:shadow-purple-500/20 hover:border-white/20">
          <div className="flex flex-col gap-6">
            <label htmlFor="topic" className="block text-white text-xl font-semibold flex items-center gap-2">
              <span className="text-2xl">🎓</span>
              What would you like to learn about?
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
              className="w-full px-6 py-5 rounded-xl text-white placeholder-white/30 border-2 border-white/20 bg-white/5 backdrop-blur-sm focus:outline-none focus:ring-4 focus:ring-purple-500/50 focus:border-purple-400 transition-all text-lg font-medium shadow-lg hover:bg-white/10"
              disabled={isLoading}
            />
            <button
              onClick={handleLearn}
              disabled={isLoading || !topic.trim()}
              className="w-full px-8 py-5 bg-gradient-to-r from-purple-600 via-pink-600 to-blue-600 text-white font-bold rounded-xl hover:from-purple-700 hover:via-pink-700 hover:to-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all transform hover:scale-[1.02] active:scale-[0.98] text-lg shadow-2xl hover:shadow-purple-500/50 relative overflow-hidden group"
            >
              <span className="relative z-10 flex items-center justify-center gap-3">
                {isLoading ? (
                  <>
                    <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Creating your learning plan...
                  </>
                ) : (
                  <>
                    <span>Start Learning</span>
                    <span className="text-xl">✨</span>
                  </>
                )}
              </span>
              <div className="absolute inset-0 bg-gradient-to-r from-white/0 via-white/20 to-white/0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000"></div>
            </button>
          </div>

          {error && (
            <div className="mt-6 bg-red-500/20 backdrop-blur-sm border-2 border-red-500/50 text-red-100 px-5 py-4 rounded-xl animate-shake shadow-lg">
              <div className="flex items-center gap-2">
                <span className="text-xl">⚠️</span>
                <span className="font-medium">{error}</span>
              </div>
            </div>
          )}
        </div>

        {learningData && (
          <div className="space-y-10 animate-fade-in">
            {/* Learning Plan */}
            <div className="bg-white/5 backdrop-blur-xl rounded-2xl p-8 md:p-10 shadow-2xl border border-white/10 hover:border-white/20 transition-all duration-300">
              <div className="flex items-center gap-3 mb-8">
                <div className="w-1 h-12 bg-gradient-to-b from-purple-500 to-blue-500 rounded-full"></div>
                <h2 className="text-4xl font-bold bg-gradient-to-r from-purple-300 to-blue-300 bg-clip-text text-transparent">
                  Your Learning Plan
                </h2>
              </div>
              <div className="space-y-5">
                {learningData.plan.map((step, index) => {
                  const isExpanded = expandedSteps[index] !== undefined
                  const isLoading = expandingStep === index
                  
                  return (
                    <div
                      key={index}
                      className="bg-gradient-to-br from-white/5 to-white/0 rounded-xl p-6 md:p-7 border border-white/10 hover:border-purple-400/50 hover:bg-white/10 transition-all duration-300 group hover:shadow-xl hover:shadow-purple-500/10 animate-slide-in"
                      style={{ animationDelay: `${index * 100}ms` }}
                    >
                      <div className="flex items-start gap-5">
                        <div className="flex-shrink-0 w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500 via-pink-500 to-blue-500 flex items-center justify-center font-bold text-xl shadow-lg group-hover:scale-110 transition-transform duration-300">
                          {index + 1}
                        </div>
                        <div className="flex-1 pt-1">
                          <div className="flex items-start justify-between gap-4 mb-3">
                            <div className="flex-1">
                              <h3 className="text-xl md:text-2xl font-bold mb-2 text-purple-200 group-hover:text-purple-100 transition-colors">
                                {step.title}
                              </h3>
                              <p className="text-gray-300 leading-relaxed text-base md:text-lg">{step.description}</p>
                            </div>
                            <button
                              onClick={() => handleExpandStep(index, step)}
                              disabled={isLoading}
                              className="flex-shrink-0 px-4 py-2 rounded-lg bg-white/10 hover:bg-white/20 border border-white/20 hover:border-purple-400/50 text-sm font-medium text-purple-200 hover:text-purple-100 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                              {isLoading ? (
                                <span className="flex items-center gap-2">
                                  <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                  </svg>
                                  Loading...
                                </span>
                              ) : isExpanded ? (
                                <span className="flex items-center gap-2">
                                  <span>Show Less</span>
                                  <span className="transform rotate-180 transition-transform">▼</span>
                                </span>
                              ) : (
                                <span className="flex items-center gap-2">
                                  <span>Dive Deeper</span>
                                  <span>▼</span>
                                </span>
                              )}
                            </button>
                          </div>

                          {/* Expanded Content */}
                          {isExpanded && expandedSteps[index] && (
                            <div className="mt-6 pt-6 border-t border-white/10 animate-fade-in space-y-6">
                              {/* Additional Context */}
                              {expandedSteps[index].additionalContext && (
                                <div>
                                  <h4 className="text-lg font-semibold text-blue-300 mb-2">💭 Additional Context</h4>
                                  <p className="text-gray-300 leading-relaxed">{expandedSteps[index].additionalContext}</p>
                                </div>
                              )}

                              {/* Practical Details */}
                              {expandedSteps[index].practicalDetails && expandedSteps[index].practicalDetails!.length > 0 && (
                                <div>
                                  <h4 className="text-lg font-semibold text-blue-300 mb-3">🔧 Practical Implementation Details</h4>
                                  <ul className="space-y-2">
                                    {expandedSteps[index].practicalDetails!.map((detail, detailIndex) => (
                                      <li key={detailIndex} className="flex items-start gap-2 text-gray-300">
                                        <span className="text-purple-400 mt-1">•</span>
                                        <span>{detail}</span>
                                      </li>
                                    ))}
                                  </ul>
                                </div>
                              )}

                              {/* Important Considerations */}
                              {expandedSteps[index].importantConsiderations && expandedSteps[index].importantConsiderations!.length > 0 && (
                                <div>
                                  <h4 className="text-lg font-semibold text-blue-300 mb-3">⚠️ Important Considerations</h4>
                                  <ul className="space-y-2">
                                    {expandedSteps[index].importantConsiderations!.map((consideration, considerationIndex) => (
                                      <li key={considerationIndex} className="flex items-start gap-2 text-gray-300">
                                        <span className="text-yellow-400 mt-1">•</span>
                                        <span>{consideration}</span>
                                      </li>
                                    ))}
                                  </ul>
                                </div>
                              )}

                              {/* Real-World Examples */}
                              {expandedSteps[index].realWorldExamples && expandedSteps[index].realWorldExamples!.length > 0 && (
                                <div>
                                  <h4 className="text-lg font-semibold text-blue-300 mb-3">🌍 Real-World Applications</h4>
                                  <ul className="space-y-2">
                                    {expandedSteps[index].realWorldExamples!.map((example, exampleIndex) => (
                                      <li key={exampleIndex} className="flex items-start gap-2 text-gray-300">
                                        <span className="text-green-400 mt-1">•</span>
                                        <span>{example}</span>
                                      </li>
                                    ))}
                                  </ul>
                                </div>
                              )}

                              {/* Potential Challenges */}
                              {expandedSteps[index].potentialChallenges && expandedSteps[index].potentialChallenges!.length > 0 && (
                                <div>
                                  <h4 className="text-lg font-semibold text-blue-300 mb-3">🚧 Potential Challenges & Solutions</h4>
                                  <ul className="space-y-2">
                                    {expandedSteps[index].potentialChallenges!.map((challenge, challengeIndex) => (
                                      <li key={challengeIndex} className="flex items-start gap-2 text-gray-300">
                                        <span className="text-orange-400 mt-1">•</span>
                                        <span>{challenge}</span>
                                      </li>
                                    ))}
                                  </ul>
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Real Examples */}
            <div className="bg-white/5 backdrop-blur-xl rounded-2xl p-8 md:p-10 shadow-2xl border border-white/10 hover:border-white/20 transition-all duration-300">
              <div className="flex items-center gap-3 mb-8">
                <div className="w-1 h-12 bg-gradient-to-b from-blue-500 to-cyan-500 rounded-full"></div>
                <h2 className="text-4xl font-bold bg-gradient-to-r from-blue-300 to-cyan-300 bg-clip-text text-transparent">
                  Real Examples & Resources
                </h2>
              </div>
              {learningData.message && (
                <div className="mb-6 bg-blue-500/20 backdrop-blur-sm border-2 border-blue-500/50 text-blue-100 px-5 py-4 rounded-xl animate-fade-in shadow-lg">
                  <div className="flex items-center gap-2">
                    <span className="text-xl">ℹ️</span>
                    <span className="font-medium">{learningData.message}</span>
                  </div>
                </div>
              )}
              <div className="grid gap-5 md:grid-cols-2">
                {learningData.examples.map((example, index) => (
                  <a
                    key={index}
                    href={example.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block bg-gradient-to-br from-white/5 to-white/0 rounded-xl p-6 border border-white/10 hover:border-blue-400/50 hover:bg-white/10 transition-all duration-300 group hover:shadow-xl hover:shadow-blue-500/10 animate-slide-in hover:scale-[1.02]"
                    style={{ animationDelay: `${index * 100}ms` }}
                  >
                    <div className="flex items-start gap-3 mb-3">
                      <span className="text-2xl">🔗</span>
                      <h3 className="text-lg font-bold text-purple-200 group-hover:text-purple-100 transition-colors line-clamp-2">
                        {example.title}
                      </h3>
                    </div>
                    <p className="text-sm text-gray-400 mb-3 line-clamp-2">{example.description}</p>
                    <p className="text-xs text-blue-400 truncate font-mono group-hover:text-blue-300 transition-colors">
                      {example.url}
                    </p>
                    <div className="mt-4 flex items-center gap-2 text-blue-400 text-sm font-medium opacity-0 group-hover:opacity-100 transition-opacity">
                      <span>Visit resource</span>
                      <span className="transform group-hover:translate-x-1 transition-transform">→</span>
                    </div>
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
