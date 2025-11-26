import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'AI Learning Experience',
  description: 'Create personalized learning plans with real examples',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" style={{ backgroundColor: 'transparent', margin: 0, padding: 0 }}>
      <body style={{ 
        backgroundColor: 'transparent', 
        margin: 0, 
        padding: 0,
        background: 'linear-gradient(to bottom right, #581c87, #1e3a8a, #000000)',
        minHeight: '100vh',
        width: '100vw',
      }}>
        {children}
      </body>
    </html>
  )
}

