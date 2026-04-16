'use client'

import { useState } from 'react'
import TabProdes from './TabProdes'
import TabEmbargoSemas from './TabEmbargoSemas'
import TabDesmatamento from './TabDesmatamento'
import TabResumo from './TabResumo'

type AbaType = 'prodes' | 'embargo' | 'desmatamento' | 'resumo'

export default function CARsProblematicosPanel() {
  const [abaAtiva, setAbaAtiva] = useState<AbaType>('resumo')

  const abas: { id: AbaType; label: string; icon: string }[] = [
    { id: 'prodes', label: 'PRODES', icon: '🛰️' },
    { id: 'embargo', label: 'Embargo SEMAS', icon: '🔴' },
    { id: 'desmatamento', label: 'Desmatamento', icon: '📍' },
    { id: 'resumo', label: 'Resumo', icon: '📊' },
  ]

  return (
    <div className="space-y-4">
      {/* Abas */}
      <div className="flex flex-wrap gap-2 border-b border-gray-300 pb-2">
        {abas.map(aba => (
          <button
            key={aba.id}
            onClick={() => setAbaAtiva(aba.id)}
            className={`px-4 py-2 rounded-t-lg font-semibold text-sm transition-all ${
              abaAtiva === aba.id
                ? 'bg-blue-600 text-white border-b-4 border-blue-700'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            {aba.icon} {aba.label}
          </button>
        ))}
      </div>

      {/* Conteúdo da aba */}
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        {abaAtiva === 'prodes' && <TabProdes />}
        {abaAtiva === 'embargo' && <TabEmbargoSemas />}
        {abaAtiva === 'desmatamento' && <TabDesmatamento />}
        {abaAtiva === 'resumo' && <TabResumo />}
      </div>
    </div>
  )
}
