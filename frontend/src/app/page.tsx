'use client'

import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'
import { authStorage } from '@/services/auth'

export default function Home() {
  const router = useRouter()

  // Redireciona para o dashboard se já estiver logado
  useEffect(() => {
    if (authStorage.estaAutenticado()) {
      router.push('/dashboard')
    }
  }, [router])

  return (
    <main className="min-h-screen bg-gradient-to-br from-verde-900 via-verde-800 to-verde-700">
      {/* Header */}
      <header className="flex items-center justify-between px-8 py-5">
        <div className="flex items-center gap-3">
          <span className="text-3xl">🌱</span>
          <div>
            <h1 className="text-white text-xl font-bold tracking-wide">Eureka Terra</h1>
            <p className="text-verde-200 text-xs">Análise ESG de Propriedades Rurais</p>
          </div>
        </div>
        <div className="flex gap-3">
          <Link
            href="/login"
            className="px-5 py-2 text-sm text-white border border-verde-300 rounded-lg hover:bg-verde-700 transition-colors"
          >
            Entrar
          </Link>
          <Link
            href="/register"
            className="px-5 py-2 text-sm bg-white text-verde-800 rounded-lg font-semibold hover:bg-verde-50 transition-colors"
          >
            Criar conta
          </Link>
        </div>
      </header>

      {/* Hero */}
      <section className="flex flex-col items-center justify-center px-6 pt-16 pb-24 text-center">
        <span className="inline-block bg-verde-700/60 text-verde-200 text-xs font-semibold px-4 py-1.5 rounded-full mb-6 border border-verde-500/40">
          🛡 Embargos · Áreas Protegidas · Moratória da Soja · EUDR · PRODES/INPE
        </span>

        <h2 className="text-4xl md:text-5xl font-bold text-white max-w-3xl leading-tight mb-6">
          Conformidade ambiental para o agronegócio brasileiro
        </h2>

        <p className="text-verde-200 text-lg max-w-2xl mb-10 leading-relaxed">
          Analise propriedades rurais pelo número do CAR, verifique embargos IBAMA/SEMAS,
          sobreposição com áreas protegidas e gere relatórios de conformidade com Moratória
          da Soja e EUDR em minutos.
        </p>

        <div className="flex flex-col sm:flex-row gap-4">
          <Link
            href="/register"
            className="px-8 py-3.5 bg-white text-verde-800 rounded-xl font-bold text-lg hover:bg-verde-50 transition-colors shadow-lg"
          >
            Começar gratuitamente
          </Link>
          <Link
            href="/login"
            className="px-8 py-3.5 border border-verde-300 text-white rounded-xl font-semibold text-lg hover:bg-verde-700/50 transition-colors"
          >
            Já tenho conta
          </Link>
        </div>
      </section>

      {/* Features */}
      <section className="bg-white/5 backdrop-blur-sm py-16 px-6">
        <div className="max-w-5xl mx-auto grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {[
            { icon: '🗺', titulo: 'Mapa Interativo', desc: 'Visualize o polígono do CAR no mapa com OpenStreetMap' },
            { icon: '🛡', titulo: 'Embargos e Áreas Protegidas', desc: 'Verifica embargos IBAMA/SEMAS e sobreposição com UCs e Terras Indígenas' },
            { icon: '⚖️', titulo: 'Conformidade ESG', desc: 'Moratória da Soja (2008) e EUDR (Regulamento UE 2023/1115)' },
            { icon: '📄', titulo: 'Relatório PDF', desc: 'Relatório completo gerado automaticamente para auditoria' },
          ].map((f) => (
            <div key={f.titulo} className="bg-white/10 rounded-2xl p-6 text-white">
              <div className="text-3xl mb-3">{f.icon}</div>
              <h3 className="font-semibold text-base mb-2">{f.titulo}</h3>
              <p className="text-verde-200 text-sm leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="text-center py-8 text-verde-300 text-xs">
        <p>© 2024 Eureka Terra · Dados: SICAR/MAPA · PRODES/INPE · Copernicus/ESA · MapBiomas</p>
      </footer>
    </main>
  )
}
