import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { Navigation } from '@/components/Navigation'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'TeamGenie AI 🧞‍♂️ | Multi-Agent Team Generator',
  description: 'Dominate Fantasy Sports with Multi-Agent AI. Real-time pitch analysis, DuckDuckGo injury scraper, and OR-Tools ILP optimization.',
  keywords: ['Fantasy Cricket', 'AI Team Generator', 'Dream11', 'IPL 2026', 'Sports Analytics', 'CrewAI'],
  authors: [{ name: 'Mohammed Inayat Hussain Qureshi' }],
  openGraph: {
    title: 'TeamGenie AI 🧞‍♂️ | Multi-Agent Team Generator',
    description: 'A Hyper-Optimized, Multi-Agent Fantasy Sports Intelligence Framework.',
    url: 'https://teamgenie.app',
    siteName: 'TeamGenie AI',
    images: [{ url: '/og-image.png', width: 1200, height: 630 }],
    locale: 'en_IN',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'TeamGenie AI 🧞‍♂️ | Multi-Agent Team Generator',
    description: 'A Hyper-Optimized, Multi-Agent Fantasy Sports Intelligence Framework.',
  },
  metadataBase: new URL('https://teamgenie.app'),
  alternates: {
    canonical: '/',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} min-h-screen bg-slate-950 text-slate-50 overflow-x-hidden`}>
        <Navigation />
        <main className="pt-16 min-h-screen">
          {children}
        </main>
      </body>
    </html>
  )
}
