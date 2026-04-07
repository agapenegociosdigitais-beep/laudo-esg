import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Eureka Terra - Analise ESG de Propriedades Rurais',
  description:
    'Plataforma SaaS para analise de conformidade ambiental (Moratoria da Soja, EUDR) ' +
    'com dados de satelite para propriedades rurais brasileiras.',
  keywords: ['CAR', 'IBAMA', 'ESG', 'EUDR', 'Moratoria da Soja', 'propriedade rural', 'geoespacial'],
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </head>
      <body className={inter.className}>{children}</body>
    </html>
  )
}