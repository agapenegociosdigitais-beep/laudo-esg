'use client'

import { useEffect, useState } from 'react'
import { adminService } from '@/services/api'
import { exportarCSV } from '@/utils/exportCsv'
import type { CAREmbargoSemas } from '@/types'

export default function TabEmbargoSemas() {
  const [cars, setCars] = useState<CAREmbargoSemas[]>([])
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState<string | null>(null)

  useEffect(() => {
    carregarDados()
  }, [])

  const carregarDados = async () => {
    try {
      setCarregando(true)
      setErro(null)
      const dados = await adminService.listarCarsEmbargoSemas()
      setCars(dados)
    } catch (err) {
      setErro(err instanceof Error ? err.message : 'Erro ao carregar CARs com embargo SEMAS')
    } finally {
      setCarregando(false)
    }
  }

  if (carregando) {
    return <div className="text-center py-8 text-gray-500">Carregando CARs com embargo SEMAS...</div>
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
          Total: <strong className="text-red-700">{cars.length}</strong> CAR{cars.length !== 1 ? 's' : ''} com embargo ativo
        </span>
        {cars.length > 0 && (
          <button
            onClick={() => exportarCSV(cars, 'CARs_Embargo_SEMAS')}
            className="px-4 py-2 bg-green-600 text-white rounded text-sm font-semibold hover:bg-green-700"
          >
            ↓ Exportar CSV
          </button>
        )}
      </div>

      {cars.length === 0 ? (
        <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg text-center">
          Nenhum CAR com embargo SEMAS ativo no momento
        </div>
      ) : (
        <div className="bg-white rounded-lg border border-red-300 overflow-hidden shadow-lg">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-red-50 border-b border-red-300">
                  <th className="text-left py-3 px-4 font-semibold text-red-800">CAR</th>
                  <th className="text-left py-3 px-4 font-semibold text-red-800">Município</th>
                  <th className="text-left py-3 px-4 font-semibold text-red-800">Nº TAD</th>
                  <th className="text-left py-3 px-4 font-semibold text-red-800">Processo</th>
                  <th className="text-center py-3 px-4 font-semibold text-red-800">Data Embargo</th>
                  <th className="text-left py-3 px-4 font-semibold text-red-800">Situação</th>
                  <th className="text-right py-3 px-4 font-semibold text-red-800">Área (ha)</th>
                  <th className="text-left py-3 px-4 font-semibold text-red-800">Cliente</th>
                  <th className="text-left py-3 px-4 font-semibold text-red-800">Data Pesquisa</th>
                </tr>
              </thead>
              <tbody>
                {cars.map((car, idx) => (
                  <tr key={idx} className="border-b border-red-100 bg-red-50 hover:bg-red-100">
                    <td className="py-3 px-4 font-mono text-xs text-red-900 font-semibold">{car.numero_car}</td>
                    <td className="py-3 px-4 text-red-900">{car.municipio || '-'}</td>
                    <td className="py-3 px-4 font-semibold text-red-800">{car.numero_tad || '-'}</td>
                    <td className="py-3 px-4 text-red-700">{car.processo || '-'}</td>
                    <td className="py-3 px-4 text-center text-red-800">
                      {car.data_embargo ? new Date(car.data_embargo).toLocaleDateString('pt-BR') : '-'}
                    </td>
                    <td className="py-3 px-4 text-red-700 font-semibold">{car.situacao || '-'}</td>
                    <td className="py-3 px-4 text-right font-bold text-red-800">
                      {car.area_embargada_ha ? car.area_embargada_ha.toFixed(2) : '-'}
                    </td>
                    <td className="py-3 px-4 text-red-700 text-xs">{car.usuario_email || '-'}</td>
                    <td className="py-3 px-4 text-red-700 text-xs">
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
