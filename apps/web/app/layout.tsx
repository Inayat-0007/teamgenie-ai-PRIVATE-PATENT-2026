import type { Metadata, Viewport } from 'next';
import './globals.css';

export const viewport: Viewport = {
  themeColor: '#0f172a',
  width: 'device-width',
  initialScale: 1,
};

export const metadata: Metadata = {
  metadataBase: new URL('https://teamgenie.app'),
  title: {
    default: 'TeamGenie AI — Fantasy Sports Intelligence',
    template: '%s | TeamGenie AI',
  },
  description:
    'AI-powered multi-agent system that generates optimal fantasy sports teams in <5 seconds. 72% prediction accuracy, backed by data.',
  keywords: [
    'fantasy cricket',
    'AI predictions',
    'team generator',
    'Dream11',
    'fantasy sports',
    'cricket AI',
    'fantasy team optimizer',
  ],
  authors: [{ name: 'Mohammed Inayat Hussain Qureshi' }],
  creator: 'Mohammed Inayat Hussain Qureshi',
  publisher: 'TeamGenie AI',
  robots: {
    index: true,
    follow: true,
    googleBot: { index: true, follow: true },
  },
  openGraph: {
    title: 'TeamGenie AI — Fantasy Sports Intelligence',
    description: 'Get AI-optimized fantasy teams in <5 seconds',
    url: 'https://teamgenie.app',
    siteName: 'TeamGenie AI',
    type: 'website',
    locale: 'en_IN',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'TeamGenie AI — Fantasy Sports Intelligence',
    description: 'Get AI-optimized fantasy teams in <5 seconds',
    creator: '@Inayat0007',
  },
  alternates: {
    canonical: 'https://teamgenie.app',
  },
  manifest: '/manifest.json',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <head>
        <link rel="icon" href="/favicon.ico" sizes="any" />
        <link rel="apple-touch-icon" href="/apple-touch-icon.png" />
      </head>
      <body className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950 text-white antialiased">
        {children}
      </body>
    </html>
  );
}
