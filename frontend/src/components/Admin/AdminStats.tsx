'use client'

import type { EstatisticasAdmin } from '@/types'

interface Props {
  stats: EstatisticasAdmin
}

export default function AdminStats({ stats }: Props) {
  const cards = [
    {
      titulo: 'Usuários Cadastrados',
      valor: stats.total_usuarios,
      subtitulo: `${stats.usuarios_ativos} ativos`,
      cor: 'bg-blue-50 border-blue-200',
      textoCor: 'text-blue-700',
    },
    {
      titulo: 'Análises Este Mês',
      valor: stats.analises_mes_atual,
      subtitulo: `${stats.total_analises} total`,
      cor: 'bg-green-50 border-green-200',
      textoCor: 'text-green-700',
    },
    {
      titulo: 'CARs Consultados',
      valor: stats.cars_consultados,
      subtitulo: 'únicos',
      cor: 'bg-purple-50 border-purple-200',
      textoCor: 'text-purple-700',
    },
    {
      titulo: 'Usuários Ativos',
      valor: stats.usuarios_ativos,
      subtitulo: `de ${stats.total_usuarios}`,
      cor: 'bg-yellow-50 border-yellow-200',
      textoCor: 'text-yellow-700',
    },
  ]

  return (
    <div className="space-y-6">
      {/* Cards de métricas */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {cards.map((card) => (
          <div key={card.titulo} className={`rounded-lg border p-4 ${card.cor}`}>
            <p className={`text-sm font-semibold ${card.textoCor}`}>{card.titulo}</p>
            <p className={`text-3xl font-bold ${card.textoCor} mt-2`}>{card.valor}</p>
            <p className={`text-xs ${card.textoCor} opacity-75 mt-1`}>{card.subtitulo}</p>
          </div>
        ))}
      </div>

      {/* Top 5 usuários */}
      {stats.top_usuarios.length > 0 && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Top 5 Usuários (Este Mês)</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-gray-600 border-b border-gray-200">
                  <th className="text-left py-2 px-3">Nome</th>
                  <th className="text-left py-2 px-3">E-mail</th>
                  <th className="text-right py-2 px-3">Consultas</th>
                </tr>
              </thead>
              <tbody>
                {stats.top_usuarios.map((user, i) => (
                  <tr key={i} className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="py-3 px-3 font-medium text-gray-800">{user.nome}</td>
                    <td className="py-3 px-3 text-gray-600">{user.email}</td>
                    <td className="py-3 px-3 text-right">
                      <span className="bg-blue-100 text-blue-800 px-2.5 py-0.5 rounded-full text-xs font-semibold">
                        {user.consultas_mes}
                      </span>
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
