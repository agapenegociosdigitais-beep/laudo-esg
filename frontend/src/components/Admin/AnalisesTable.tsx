'use client'

import { useEffect, useState } from 'react'
import { adminService } from '@/services/api'
import type { AnaliseAdmin } from '@/types'

const statusCores: Record<string, string> = {
  pendente: 'bg-yellow-100 text-yellow-800',
  processando: 'bg-blue-100 text-blue-800',
  concluido: 'bg-green-100 text-green-800',
  erro: 'bg-red-100 text-red-800',
}

const riscoCores: Record<string, string> = {
  BAIXO: 'bg-green-100 text-green-800',
  MEDIO: 'bg-yellow-100 text-yellow-800',
  ALTO: 'bg-orange-100 text-orange-800',
  CRITICO: 'bg-red-100 text-red-800',
}

export default function AnalisesTable() {
  const [analises, setAnalises] = useState<AnaliseAdmin[]>([])
  const [statusFiltro, setStatusFiltro] = useState<string>('')
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState<string | null>(null)
  const [refrescando, setRefrescando] = useState(false)

  const carregarAnalises = async () => {
    try {
      setCarregando(true)
      setErro(null)
      const dados = await adminService.listarAnalises(statusFiltro || undefined, 1)
      setAnalises(dados)
    } catch (err) {
      setErro(err instanceof Error ? err.message : 'Erro ao carregar análises')
    } finally {
      setCarregando(false)
    }
  }

  useEffect(() => {
    carregarAnalises()
  }, [statusFiltro])

  useEffect(() => {
    // Auto-refresh a cada 30s se houver análises processando
    const temProcessando = analises.some((a) => a.status === 'processando')
    if (temProcessando) {
      const intervalo = setInterval(async () => {
        setRefrescando(true)
        try {
          const dados = await adminService.listarAnalises(statusFiltro || undefined, 1)
          setAnalises(dados)
        } finally {
          setRefrescando(false)
        }
      }, 30000) // 30s
      return () => clearInterval(intervalo)
    }
  }, [analises, statusFiltro])

  if (carregando) {
    return <div className="text-center py-8 text-gray-500">Carregando análises...</div>
  }

  return (
    <div className="space-y-4">
      {erro && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
          {erro}
        </div>
      )}

      <div className="flex gap-2 flex-wrap">
        <button
          onClick={() => setStatusFiltro('')}
          className={`px-3 py-1 rounded text-sm font-semibold transition-colors ${
            statusFiltro === ''
              ? 'bg-gray-800 text-white'
              : 'bg-gray-200 text-gray-800 hover:bg-gray-300'
          }`}
        >
          Todas
        </button>
        {['pendente', 'processando', 'concluido', 'erro'].map((s) => (
          <button
            key={s}
            onClick={() => setStatusFiltro(s)}
            className={`px-3 py-1 rounded text-sm font-semibold transition-colors ${
              statusFiltro === s
                ? `${statusCores[s]} border-2 border-current`
                : 'bg-gray-200 text-gray-800 hover:bg-gray-300'
            }`}
          >
            {s.charAt(0).toUpperCase() + s.slice(1)}
          </button>
        ))}
      </div>

      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                <th className="text-left py-3 px-4 font-semibold text-gray-700">CAR</th>
                <th className="text-left py-3 px-4 font-semibold text-gray-700">Propriedade</th>
                <th className="text-left py-3 px-4 font-semibold text-gray-700">Usuário</th>
                <th className="text-center py-3 px-4 font-semibold text-gray-700">Status</th>
                <th className="text-center py-3 px-4 font-semibold text-gray-700">Score ESG</th>
                <th className="text-center py-3 px-4 font-semibold text-gray-700">Risco</th>
                <th className="text-left py-3 px-4 font-semibold text-gray-700">Data</th>
              </tr>
            </thead>
            <tbody>
              {analises.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-gray-500">
                    Nenhuma análise encontrada
                  </td>
                </tr>
              ) : (
                analises.map((analise) => (
                  <tr key={analise.id} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-3 px-4 font-mono text-xs text-gray-800">{analise.numero_car}</td>
                    <td className="py-3 px-4 text-gray-700 truncate">{analise.nome_propriedade || '-'}</td>
                    <td className="py-3 px-4 text-gray-600 text-xs truncate">{analise.usuario_email || '-'}</td>
                    <td className="py-3 px-4 text-center">
                      <span
                        className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                          statusCores[analise.status] || 'bg-gray-100 text-gray-800'
                        }`}
                      >
                        {analise.status.charAt(0).toUpperCase() + analise.status.slice(1)}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-center font-bold text-gray-800">
                      {analise.score_esg !== null ? `${analise.score_esg.toFixed(1)}` : '-'}
                    </td>
                    <td className="py-3 px-4 text-center">
                      {analise.nivel_risco ? (
                        <span
                          className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                            riscoCores[analise.nivel_risco] || 'bg-gray-100 text-gray-800'
                          }`}
                        >
                          {analise.nivel_risco}
                        </span>
                      ) : (
                        '-'
                      )}
                    </td>
                    <td className="py-3 px-4 text-gray-600 text-xs">
                      {new Date(analise.criado_em).toLocaleDateString('pt-BR')}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {analises.some((a) => a.status === 'processando') && (
        <p className="text-center text-sm text-gray-500">
          {refrescando ? 'Atualizando...' : 'Auto-atualiza a cada 30s'}
        </p>
      )}
    </div>
  )
}
