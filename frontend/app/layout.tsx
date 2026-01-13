import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Stellar AI - Personal Assistant from Space',
  description: 'AI Personal Assistant Chat Interface',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}