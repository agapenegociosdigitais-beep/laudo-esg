'use client'

import { useEffect, useState } from 'react'
import { adminService } from '@/services/api'
import type { AlertaAnalise } from '@/types'

export default function AlertasPanel() {
  const [alertas, setAlertas] = useState<AlertaAnalise[]>([])
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState<string | null>(null)
  const [refrescando, setRefrescando] = useState(false)

  const carregarAlertas = async () => {
    try {
      setCarregando(true)
      setErro(null)
      const dados = await adminService.listarAlertas()
      setAlertas(dados)
    } catch (err) {
      setErro(err instanceof Error ? err.message : 'Erro ao carregar alertas')
    } finally {
      setCarregando(false)
    }
  }

  useEffect(() => {
    carregarAlertas()
  }, [])

  useEffect(() => {
    // Auto-refresh a cada 60s
    const intervalo = setInterval(async () => {
      setRefrescando(true)
      try {
        const dados = await adminService.listarAlertas()
        setAlertas(dados)
      } finally {
        setRefrescando(false)
      }
    }, 60000)
    return () => clearInterval(intervalo)
  }, [])

  if (carregando) {
    return <div className="text-center py-8 text-gray-500">Carregando alertas...</div>
  }

  return (
    <div className="space-y-4">
      {erro && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
          {erro}
        </div>
      )}

      {alertas.length === 0 ? (
        <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg text-center">
          ✓ Nenhuma propriedade com alertas no momento
        </div>
      ) : (
        <div className="space-y-4">
          <div className="text-sm text-red-600 font-semibold">
            ⚠️ {alertas.length} propriedade{alertas.length !== 1 ? 's' : ''} com alertas críticos
          </div>

          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-red-50 border-b border-red-200">
                    <th className="text-left py-3 px-4 font-semibold text-red-800">CAR</th>
                    <th className="text-left py-3 px-4 font-semibold text-red-800">Propriedade</th>
                    <th className="text-center py-3 px-4 font-semibold text-red-800">Score ESG</th>
                    <th className="text-center py-3 px-4 font-semibold text-red-800">Risco</th>
                    <th className="text-left py-3 px-4 font-semibold text-red-800">Alertas</th>
                    <th className="text-left py-3 px-4 font-semibold text-red-800">Data</th>
                  </tr>
                </thead>
                <tbody>
                  {alertas.map((alerta) => (
                    <tr key={alerta.id} className="border-b border-red-100 hover:bg-red-50">
                      <td className="py-3 px-4 font-mono text-xs text-gray-800">{alerta.numero_car}</td>
                      <td className="py-3 px-4 text-gray-700 truncate">{alerta.nome_propriedade || '-'}</td>
                      <td className="py-3 px-4 text-center font-bold text-gray-800">
                        {alerta.score_esg !== null && alerta.score_esg !== undefined ? `${alerta.score_esg.toFixed(1)}` : '-'}
                      </td>
                      <td className="py-3 px-4 text-center">
                        {alerta.nivel_risco ? (
                          <span
                            className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                              alerta.nivel_risco === 'CRÍTICO'
                                ? 'bg-red-100 text-red-800'
                                : alerta.nivel_risco === 'ALTO'
                                  ? 'bg-orange-100 text-orange-800'
                                  : alerta.nivel_risco === 'MÉDIO'
                                    ? 'bg-yellow-100 text-yellow-800'
                                    : 'bg-green-100 text-green-800'
                            }`}
                          >
                            {alerta.nivel_risco}
                          </span>
                        ) : (
                          '-'
                        )}
                      </td>
                      <td className="py-3 px-4 text-sm">
                        <div className="flex flex-wrap gap-1">
                          {alerta.tem_embargo_ibama && (
                            <span className="inline-flex items-center gap-1 bg-red-100 text-red-800 px-2.5 py-0.5 rounded-full text-xs font-semibold">
                              🔴 IBAMA
                            </span>
                          )}
                          {alerta.tem_embargo_semas && (
                            <span className="inline-flex items-center gap-1 bg-red-100 text-red-800 px-2.5 py-0.5 rounded-full text-xs font-semibold">
                              🔴 SEMAS
                            </span>
                          )}
                          {alerta.tem_desmatamento && (
                            <span className="inline-flex items-center gap-1 bg-orange-100 text-orange-800 px-2.5 py-0.5 rounded-full text-xs font-semibold">
                              🟠 PRODES
                              {alerta.area_desmatada_ha ? ` ${alerta.area_desmatada_ha.toFixed(1)}ha` : ''}
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="py-3 px-4 text-gray-600 text-xs">
                        {new Date(alerta.criado_em).toLocaleDateString('pt-BR')}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {refrescando && <p className="text-center text-sm text-gray-500">Atualizando...</p>}
        </div>
      )}
    </div>
  )
}
