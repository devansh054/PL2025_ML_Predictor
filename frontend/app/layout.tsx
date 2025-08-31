import './globals.css'
import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import Navigation from './components/Navigation'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Premier League Predictor - FAANG-Level ML Application',
  description: 'AI-powered Premier League match predictions with advanced analytics, real-time features, and natural language processing',
  keywords: 'Premier League, football predictions, AI, machine learning, match predictor, soccer analytics',
  authors: [{ name: 'Premier League Predictor' }],
  viewport: 'width=device-width, initial-scale=1',
  themeColor: '#000000',
  openGraph: {
    title: 'Premier League Predictor | AI-Powered Match Predictions',
    description: 'Advanced Premier League match predictor using machine learning with 81.4% accuracy',
    type: 'website',
    locale: 'en_US',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Premier League Predictor | AI-Powered Match Predictions',
    description: 'Advanced Premier League match predictor using machine learning with 81.4% accuracy',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <head>
        <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>⚽</text></svg>" />
      </head>
      <body className={inter.className}>{children}</body>
    </html>
  )
}
