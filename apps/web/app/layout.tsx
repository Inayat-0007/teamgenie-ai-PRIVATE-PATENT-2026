import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { Navigation } from '@/components/Navigation'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'TeamGenie AI 🧞‍♂️ | Multi-Agent Team Generator',
  description: 'A Hyper-Optimized, Multi-Agent Fantasy Sports Intelligence Framework.',
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
