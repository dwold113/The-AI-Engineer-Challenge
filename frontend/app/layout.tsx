import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Pixelated Background Generator',
  description: 'Generate pixelated backgrounds from AI-generated images',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" style={{ backgroundColor: 'transparent' }}>
      <body style={{ backgroundColor: 'transparent' }}>{children}</body>
    </html>
  )
}

