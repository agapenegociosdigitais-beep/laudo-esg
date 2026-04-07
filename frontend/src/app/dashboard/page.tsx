'use client'

import dynamic from 'next/dynamic'
import { useRouter } from 'next/navigation'
import { useCallback, useEffect, useRef, useState } from 'react'
import { authStorage } from '@/services/auth'
import { analiseService, relatorioService } from '@/services/api'
import type { Analise, CARResultado } from '@/types'

import PropertySearch from '@/components/Dashboard/PropertySearch'
import PropertyInfo from '@/components/Dashboard/PropertyInfo'
import ComplianceStatus from '@/components/Dashboard/ComplianceStatus'

const MapComponent = dynamic(() => import('@/components/Map/MapComponent'), {
  ssr: false,
  loading: () => (
    <div className="h-[380px] rounded-xl bg-verde-50 flex items-center justify-center text-verde-600 text-sm">
      🗺 Carregando mapa...
    </div>
  ),
})

type EtapaDashboard = 'busca' | 'propriedade' | 'analisando' | 'resultado'

const POLLING_INTERVALO_MS = 3_000
const POLLING_MAX_TENTATIVAS = 60

export default function DashboardPage() {
  const router = useRouter()
  const usuario = authStorage.obterUsuario()

  const [etapa, setEtapa] = useState<EtapaDashboard>('busca')
  const [propriedade, setPropriedade] = useState<CARResultado | null>(null)
  const [analise, setAnalise] = useState<Analise | null>(null)
  const [mensagemStatus, setMensagemStatus] = useState('')
  const [erroAnalise, setErroAnalise] = useState('')
  const [gerandoRelatorio, setGerandoRelatorio] = useState(false)
  const [urlRelatorio, setUrlRelatorio] = useState('')

  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    if (!authStorage.estaAutenticado()) {
      router.push('/login')
    }
    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current)
    }
  }, [router])

  function handleLogout() {
    authStorage.limparSessao()
    router.push('/')
  }

  function handlePropriedadeEncontrada(resultado: CARResultado) {
    if (pollingRef.current) clearInterval(pollingRef.current)
    setPropriedade(resultado)
    setAnalise(null)
    setUrlRelatorio('')
    setErroAnalise('')
    setEtapa('propriedade')
  }

  const handleIniciarAnalise = useCallback(async () => {
    if (!propriedade?.id) {
      setErroAnalise('ID da propriedade não disponível. Tente buscar o CAR novamente.')
      return
    }

    if (pollingRef.current) clearInterval(pollingRef.current)
    setEtapa('analisando')
    setErroAnalise('')
    setMensagemStatus('Iniciando análise...')

    const hoje = new Date()
    const umAnoAtras = new Date(hoje)
    umAnoAtras.setFullYear(hoje.getFullYear() - 1)

    try {
      const analiseIniciada = await analiseService.iniciar({
        propriedade_id: propriedade.id,
        data_inicio: umAnoAtras.toISOString().split('T')[0],
        data_fim: hoje.toISOString().split('T')[0],
      })

      setAnalise(analiseIniciada)
      setMensagemStatus('Verificando embargos IBAMA e SEMAS...')

      let tentativas = 0
      pollingRef.current = setInterval(async () => {
        tentativas++

        const mensagens = [
          'Verificando embargos IBAMA e SEMAS...',
          'Consultando áreas protegidas (CNUC/FUNAI)...',
          'Verificando desmatamento (PRODES/INPE)...',
          'Avaliando conformidade ESG...',
          'Calculando score ambiental...',
          'Finalizando análise...',
        ]
        setMensagemStatus(mensagens[tentativas % mensagens.length])

        try {
          const analiseAtual = await analiseService.obterPorId(analiseIniciada.id)
          setAnalise(analiseAtual)

          if (analiseAtual.status === 'concluido') {
            clearInterval(pollingRef.current!)
            setEtapa('resultado')
          } else if (analiseAtual.status === 'erro') {
            clearInterval(pollingRef.current!)
            setErroAnalise(analiseAtual.erro_mensagem || 'Erro durante a análise.')
            setEtapa('propriedade')
          } else if (tentativas >= POLLING_MAX_TENTATIVAS) {
            clearInterval(pollingRef.current!)
            setErroAnalise('Tempo limite excedido. Tente recarregar a página.')
            setEtapa('propriedade')
          }
        } catch {
          // Mantém o polling em caso de falha pontual de rede
        }
      }, POLLING_INTERVALO_MS)

    } catch (err: unknown) {
      setErroAnalise(err instanceof Error ? err.message : 'Erro ao iniciar análise.')
      setEtapa('propriedade')
    }
  }, [propriedade])

  async function handleGerarRelatorio() {
    if (!analise || analise.status !== 'concluido') return

    setGerandoRelatorio(true)
    try {
      const rel = await relatorioService.gerar(analise.id)
      const token = document.cookie.split('; ').find(r => r.startsWith('token='))?.split('=')[1]

      const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const url = `${BASE_URL}/api/v1/relatorios/${rel.id}/download`
      const response = await fetch(url, {
        headers: { Authorization: `Bearer ${token}` }
      })
      if (!response.ok) throw new Error('Erro ao baixar PDF')
      const blob = await response.blob()
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      link.download = `relatorio_${analise.id.slice(0, 8)}.pdf`
      link.click()
      URL.revokeObjectURL(link.href)
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Erro ao gerar relatório.')
    } finally {
      setGerandoRelatorio(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">

      <header className="bg-verde-800 text-white px-6 py-3 flex items-center justify-between shadow-md sticky top-0 z-50">
        <div className="flex items-center gap-3">
          <span className="text-2xl">🌱</span>
          <div>
            <span className="font-bold text-base">Eureka Terra</span>
            <span className="text-verde-300 text-xs ml-2 hidden sm:inline">Dashboard</span>
          </div>
        </div>

        <div className="flex items-center gap-4">
          {usuario && (
            <span className="text-sm text-verde-200 hidden sm:block">
              Olá, <strong>{usuario.nome.split(' ')[0]}</strong>
            </span>
          )}
          <button
            onClick={handleLogout}
            className="text-sm text-verde-300 hover:text-white transition-colors"
          >
            Sair
          </button>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-6 space-y-5">

        <PropertySearch onEncontrada={handlePropriedadeEncontrada} />

        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
          <div className="px-5 py-3 border-b border-gray-100 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-gray-600">
              {propriedade
                ? `📍 ${propriedade.nome_propriedade || propriedade.numero_car} — ${propriedade.municipio}/${propriedade.estado}`
                : '🗺 Mapa Interativo'}
            </h2>
            <span className="text-xs text-gray-400">© OpenStreetMap</span>
          </div>
          <MapComponent geojson={propriedade?.geojson} altura="380px" />
        </div>

        {propriedade && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">

            <div className="lg:col-span-2">
              <PropertyInfo propriedade={propriedade} />
            </div>

            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 flex flex-col gap-4">
              <div>
                <h2 className="text-lg font-semibold text-gray-800 mb-1">Análise ESG</h2>
                <p className="text-sm text-gray-500">
                  Verifica embargos IBAMA/SEMAS, sobreposição com áreas protegidas,
                  desmatamento PRODES/INPE e conformidade com Moratória da Soja e EUDR.
                </p>
              </div>

              {erroAnalise && (
                <div className="text-sm text-red-700 bg-red-50 border border-red-200 rounded-xl p-3">
                  {erroAnalise}
                </div>
              )}

              {etapa === 'analisando' && (
                <div className="bg-verde-50 border border-verde-200 rounded-xl p-4 flex items-center gap-3">
                  <span className="text-xl animate-spin">⚙️</span>
                  <div>
                    <p className="text-sm font-medium text-verde-800">{mensagemStatus}</p>
                    <p className="text-xs text-verde-600 mt-0.5">
                      Aguardando processamento no servidor...
                    </p>
                  </div>
                </div>
              )}

              {etapa === 'propriedade' && (
                <button
                  onClick={handleIniciarAnalise}
                  disabled={!propriedade.id}
                  className="w-full py-3 bg-verde-700 hover:bg-verde-800 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold rounded-xl transition-colors flex items-center justify-center gap-2"
                >
                  🔍 Iniciar Análise
                </button>
              )}

              {etapa === 'resultado' && analise && (
                <div className="bg-verde-50 border border-verde-200 rounded-xl p-3 text-center">
                  <p className="text-sm font-semibold text-verde-800">✅ Análise concluída</p>
                  <p className="text-xs text-verde-600 mt-0.5">
                    Score ESG: <strong>{(analise.score_esg ?? 0).toFixed(0)}/100</strong> · Risco: <strong>{analise.nivel_risco ?? "N/A"}</strong>
                  </p>
                </div>
              )}

              {!propriedade.id && (
                <p className="text-xs text-amber-600 bg-amber-50 rounded-lg p-2 text-center">
                  ⚠ ID da propriedade pendente. Recarregue a busca pelo CAR.
                </p>
              )}
            </div>
          </div>
        )}

        {etapa === 'resultado' && analise && (
          <>
            <ComplianceStatus
              analise={analise}
              onGerarRelatorio={handleGerarRelatorio}
              gerandoRelatorio={gerandoRelatorio}
            />

            {urlRelatorio && (
              <div className="text-center py-2">
                <a
                  href={urlRelatorio}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 px-6 py-3 bg-verde-700 text-white rounded-xl font-semibold hover:bg-verde-800 transition-colors shadow-sm"
                >
                  ⬇ Baixar Relatório PDF
                </a>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}

