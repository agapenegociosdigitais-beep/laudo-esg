'use client'

import { useEffect, useState } from 'react'
import { adminService } from '@/services/api'
import type { ResumoCARsProblematicos } from '@/types'
import { BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

const CORES = ['#ef4444', '#f97316', '#eab308', '#22c55e']

export default function TabResumo() {
  const [resumo, setResumo] = useState<ResumoCARsProblematicos | null>(null)
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState<string | null>(null)

  useEffect(() => {
    const carregarDados = async () => {
      try {
        setCarregando(true)
        setErro(null)
        const dados = await adminService.obterResumoCars()
        setResumo(dados)
      } catch (err) {
        setErro(err instanceof Error ? err.message : 'Erro ao carregar resumo de CARs')
      } finally {
        setCarregando(false)
      }
    }
    void carregarDados()
  }, [])

  if (carregando) {
    return <div className="text-center py-8 text-gray-500">Carregando resumo...</div>
  }

  if (!resumo) {
    return <div className="text-center py-8 text-gray-500">Nenhum dado disponivel</div>
  }

  return (
    <div className="space-y-8">
      {erro && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
          {erro}
        </div>
      )}

      <div className="grid grid-cols-3 gap-4">
        <div className="bg-gradient-to-br from-orange-50 to-orange-100 border-2 border-orange-300 rounded-lg p-6 shadow-md">
          <div className="text-sm text-orange-700 font-semibold uppercase tracking-wider">CARs com PRODES</div>
          <div className="text-4xl font-bold text-orange-800 mt-2">{resumo.total_prodes}</div>
          <div className="text-xs text-orange-600 mt-1">Desmatamento detectado</div>
        </div>

        <div className="bg-gradient-to-br from-red-50 to-red-100 border-2 border-red-300 rounded-lg p-6 shadow-md">
          <div className="text-sm text-red-700 font-semibold uppercase tracking-wider">CARs com Embargo SEMAS</div>
          <div className="text-4xl font-bold text-red-800 mt-2">{resumo.total_embargo_semas}</div>
          <div className="text-xs text-red-600 mt-1">Embargo ativo</div>
        </div>

        <div className="bg-gradient-to-br from-yellow-50 to-yellow-100 border-2 border-yellow-300 rounded-lg p-6 shadow-md">
          <div className="text-sm text-yellow-700 font-semibold uppercase tracking-wider">CARs com Desmatamento</div>
          <div className="text-4xl font-bold text-yellow-800 mt-2">{resumo.total_desmatamento}</div>
          <div className="text-xs text-yellow-600 mt-1">DETER / Alertas</div>
        </div>
      </div>

      {resumo.multiplos_problemas.length > 0 && (
        <div className="bg-red-50 border-2 border-red-400 rounded-lg p-6 shadow-lg">
          <div className="flex items-start gap-3 mb-4">
            <div className="text-2xl">!</div>
            <div>
              <h3 className="text-lg font-bold text-red-800">CARs com Multiplos Problemas</h3>
              <p className="text-sm text-red-700 mt-1">
                {resumo.multiplos_problemas.length} propriedade{resumo.multiplos_problemas.length !== 1 ? 's' : ''} aparecem em 2+ categorias de risco
              </p>
            </div>
          </div>

          <div className="space-y-2">
            {resumo.multiplos_problemas.map((car, idx) => (
              <div key={idx} className="bg-white border-l-4 border-red-500 p-3 rounded">
                <div className="flex justify-between items-start">
                  <div>
                    <div className="font-mono text-sm font-bold text-gray-800">{car.numero_car}</div>
                    <div className="text-xs text-gray-600">{car.municipio || '-'}</div>
                  </div>
                  <div className="flex gap-1 flex-wrap justify-end">
                    {car.flags.map(flag => (
                      <span key={flag} className="px-2 py-1 bg-red-100 text-red-800 text-xs font-semibold rounded">
                        {flag === 'prodes' && 'PRODES'}
                        {flag === 'embargo_semas' && 'SEMAS'}
                        {flag === 'embargo_ibama' && 'IBAMA'}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="grid grid-cols-2 gap-6">
        <div className="bg-white border border-gray-200 rounded-lg p-6 shadow">
          <h3 className="text-lg font-bold text-gray-900 mb-4">Evolucao Mensal</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={resumo.evolucao_mensal}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="mes" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="prodes" fill="#f97316" name="PRODES" />
              <Bar dataKey="embargo_semas" fill="#ef4444" name="Embargo SEMAS" />
              <Bar dataKey="desmatamento" fill="#eab308" name="Desmatamento" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white border border-gray-200 rounded-lg p-6 shadow">
          <h3 className="text-lg font-bold text-gray-900 mb-4">Distribuicao por Tipo</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={resumo.distribuicao_tipo}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={(entry) => `${entry.tipo}: ${entry.total}`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="total"
              >
                {resumo.distribuicao_tipo.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={CORES[index % CORES.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}
