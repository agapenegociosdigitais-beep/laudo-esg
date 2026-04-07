'use client'

import { useState } from 'react'
import type { UsuarioAdmin } from '@/types'

interface Props {
  usuario: UsuarioAdmin
  onSalvar: (limite: number | null) => Promise<void>
  onFechar: () => void
  salvando?: boolean
}

export default function LimiteModal({ usuario, onSalvar, onFechar, salvando = false }: Props) {
  const [limite, setLimite] = useState<string>(
    usuario.limite_consultas === null ? '' : String(usuario.limite_consultas)
  )
  const [semLimite, setSemLimite] = useState(usuario.limite_consultas === null)

  const handleSalvar = async () => {
    const novoLimite = semLimite ? null : (limite ? parseInt(limite, 10) : null)
    await onSalvar(novoLimite)
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-lg max-w-sm w-full p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Editar Limite de Consultas</h3>
        <p className="text-sm text-gray-600 mb-4">Usuário: <strong>{usuario.nome}</strong></p>

        <div className="space-y-4 mb-6">
          <div>
            <label className="flex items-center gap-3">
              <input
                type="checkbox"
                checked={semLimite}
                onChange={(e) => setSemLimite(e.target.checked)}
                disabled={salvando}
                className="w-4 h-4"
              />
              <span className="text-sm font-medium text-gray-700">Sem limite</span>
            </label>
          </div>

          {!semLimite && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Limite mensal (análises)
              </label>
              <input
                type="number"
                value={limite}
                onChange={(e) => setLimite(e.target.value)}
                disabled={salvando || semLimite}
                min="1"
                placeholder="Ex: 10"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-60"
              />
            </div>
          )}
        </div>

        <div className="flex gap-3">
          <button
            onClick={onFechar}
            disabled={salvando}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 font-medium hover:bg-gray-50 transition-colors disabled:opacity-60"
          >
            Cancelar
          </button>
          <button
            onClick={handleSalvar}
            disabled={salvando || (!semLimite && !limite)}
            className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors disabled:opacity-60"
          >
            {salvando ? '⏳ Salvando...' : 'Salvar'}
          </button>
        </div>
      </div>
    </div>
  )
}
