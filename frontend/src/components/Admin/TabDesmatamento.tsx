'use client'

import { useEffect, useState } from 'react'
import { adminService } from '@/services/api'
import { exportarCSV } from '@/utils/exportCsv'
import type { CARProdes } from '@/types'

export default function TabDesmatamento() {
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
      // Reutiliza endpoint PRODES (desmatamento_detectado = true)
      const dados = await adminService.listarCarsProdes()
      setCars(dados)
    } catch (err) {
      setErro(err instanceof Error ? err.message : 'Erro ao carregar CARs com desmatamento')
    } finally {
      setCarregando(false)
    }
  }

  if (carregando) {
    return <div className="text-center py-8 text-gray-500">Carregando CARs com desmatamento...</div>
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
          Total: <strong>{cars.length}</strong> CAR{cars.length !== 1 ? 's' : ''} com desmatamento registrado
        </span>
        {cars.length > 0 && (
          <button
            onClick={() => {
              const dados = cars.map(car => ({
                numero_car: car.numero_car,
                municipio: car.municipio,
                area_desmatada_ha: car.area_desmatada_ha,
                ano_deteccao: car.ano_deteccao,
                bioma: car.bioma,
                usuario_email: car.usuario_email,
                criado_em: car.criado_em,
              }))
              exportarCSV(dados, 'CARs_Desmatamento')
            }}
            className="px-4 py-2 bg-green-600 text-white rounded text-sm font-semibold hover:bg-green-700"
          >
            ↓ Exportar CSV
          </button>
        )}
      </div>

      {cars.length === 0 ? (
        <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg text-center">
          Nenhum CAR com desmatamento registrado no momento
        </div>
      ) : (
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200">
                  <th className="text-left py-3 px-4 font-semibold text-gray-700">CAR</th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-700">Município</th>
                  <th className="text-right py-3 px-4 font-semibold text-gray-700">Área Desmatada (ha)</th>
                  <th className="text-center py-3 px-4 font-semibold text-gray-700">Período Detecção</th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-700">Bioma</th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-700">Cliente</th>
                  <th className="text-left py-3 px-4 font-semibold text-gray-700">Data Pesquisa</th>
                </tr>
              </thead>
              <tbody>
                {cars.map((car, idx) => (
                  <tr key={idx} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-3 px-4 font-mono text-xs text-gray-800">{car.numero_car}</td>
                    <td className="py-3 px-4 text-gray-700">{car.municipio || '-'}</td>
                    <td className="py-3 px-4 text-right font-bold text-orange-700">
                      {car.area_desmatada_ha ? car.area_desmatada_ha.toFixed(2) : '-'}
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
