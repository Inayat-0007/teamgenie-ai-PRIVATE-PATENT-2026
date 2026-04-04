import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' });

export const metadata: Metadata = {
  title: 'TeamGenie AI — Fantasy Sports Intelligence',
  description: 'AI-powered multi-agent system that generates optimal fantasy sports teams in <5 seconds. 70%+ prediction accuracy.',
  keywords: ['fantasy cricket', 'AI predictions', 'team generator', 'Dream11', 'fantasy sports'],
  authors: [{ name: 'Mohammed Inayat Hussain Qureshi' }],
  openGraph: {
    title: 'TeamGenie AI — Fantasy Sports Intelligence',
    description: 'Get AI-optimized fantasy teams in <5 seconds',
    url: 'https://teamgenie.app',
    siteName: 'TeamGenie AI',
    type: 'website',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${inter.variable} dark`}>
      <body className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950 text-white antialiased">
        {children}
      </body>
    </html>
  );
}
