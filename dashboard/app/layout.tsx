import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Cryptosion',
  description: 'Token scanner dashboard',
  viewport: 'width=device-width, initial-scale=1',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr" style={{ background: '#07070f', color: '#e2e8f0' }}>
      <head>
        <style>{`
          *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
          html, body { background: #07070f; color: #e2e8f0; font-family: Inter, sans-serif; min-height: 100vh; }
          table { border-collapse: collapse; width: 100%; }
          a { color: inherit; }
          input { background: transparent; }
        `}</style>
      </head>
      <body className={inter.className}>{children}</body>
    </html>
  )
}
