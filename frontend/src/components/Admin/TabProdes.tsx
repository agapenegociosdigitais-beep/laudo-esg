'use client'

import { useEffect, useState } from 'react'
import { adminService } from '@/services/api'
import { exportarCSV } from '@/utils/exportCsv'
import type { CARProdes } from '@/types'

export default function TabProdes() {
  const [cars, setCars] = useState<CARProdes[]>([])
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState<string | null>(null)

  useEffect(() => {
    carregarDados()
  }, [])

  const carregarDados = async () => {
    try {
      setCarregando(true)
      setErro(null)
      const dados = await adminService.listarCarsProdes()
      setCars(dados)
    } catch (err) {
      setErro(err instanceof Error ? err.message : 'Erro ao carregar CARs com PRODES')
    } finally {
      setCarregando(false)
    }
  }

  const getCorSeveridade = (percentual?: number) => {
    if (!percentual) return 'bg-gray-50'
    if (percentual > 20) return 'bg-red-50'
    if (percentual > 10) return 'bg-orange-50'
    return 'bg-yellow-50'
  }

  const getBadgeSeveridade = (percentual?: number) => {
    if (!percentual) return 'bg-gray-100 text-gray-800'
    if (percentual > 20) return 'bg-red-100 text-red-800'
    if (percentual > 10) return 'bg-orange-100 text-orange-800'
    return 'bg-yellow-100 text-yellow-800'
  }

  if (carregando) {
    return <div className="text-center py-8 text-gray-500">Carregando CARs com PRODES...</div>
  }

  return (
    <div className="space-y-4">
      {erro && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
          {erro}
        </div>
      )}

      <div className="flex justify-between items-center">
        <span className="text-sm text-gray-600">
          Total: <strong>{cars.length}</strong> CAR{cars.length !== 1 ? 's' : ''} com desmatamento detectado
        </span>
        {cars.length > 0 && (
          <button
            onClick={() => exportarCSV(cars, 'CARs_PRODES')}
            className="px-4 py-2 bg-green-600 text-white rounded text-sm font-semibold hover:bg-green-700"
          >
            ↓ Exportar CSV
          </button>
        )}
      </div>

      {cars.length === 0 ? (
        <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg text-center">
          Nenhum CAR com desmatamento detectado no momento
        </div>
      ) : (
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200">
                  <th className="text-left py-3 px-4 font-semibold text-gray-700">CAR</th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-700">Município</th>
                  <th className="text-right py-3 px-4 font-semibold text-gray-700">Área Total (ha)</th>
                  <th className="text-right py-3 px-4 font-semibold text-gray-700">Área PRODES (ha)</th>
                  <th className="text-center py-3 px-4 font-semibold text-gray-700">% Afetada</th>
                  <th className="text-center py-3 px-4 font-semibold text-gray-700">Ano</th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-700">Bioma</th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-700">Cliente</th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-700">Data Pesquisa</th>
                </tr>
              </thead>
              <tbody>
                {cars.map((car, idx) => (
                  <tr key={idx} className={`border-b border-gray-100 ${getCorSeveridade(car.percentual_afetado)}`}>
                    <td className="py-3 px-4 font-mono text-xs text-gray-800">{car.numero_car}</td>
                    <td className="py-3 px-4 text-gray-700">{car.municipio || '-'}</td>
                    <td className="py-3 px-4 text-right font-semibold text-gray-800">
                      {car.area_total_ha ? car.area_total_ha.toFixed(2) : '-'}
                    </td>
                    <td className="py-3 px-4 text-right font-semibold text-red-700">
                      {car.area_desmatada_ha ? car.area_desmatada_ha.toFixed(2) : '-'}
                    </td>
                    <td className="py-3 px-4 text-center">
                      {car.percentual_afetado !== undefined ? (
                        <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${getBadgeSeveridade(car.percentual_afetado)}`}>
                          {car.percentual_afetado.toFixed(1)}%
                        </span>
                      ) : (
                        '-'
                      )}
                    </td>
                    <td className="py-3 px-4 text-center text-gray-600">{car.ano_deteccao || '-'}</td>
                    <td className="py-3 px-4 text-gray-700">{car.bioma || '-'}</td>
                    <td className="py-3 px-4 text-gray-600 text-xs">{car.usuario_email || '-'}</td>
                    <td className="py-3 px-4 text-gray-600 text-xs">
                      {new Date(car.criado_em).toLocaleDateString('pt-BR')}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
