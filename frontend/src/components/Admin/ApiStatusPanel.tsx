'use client'

import { useEffect, useState } from 'react'
import { adminService } from '@/services/api'
import type { StatusAPIsExternas } from '@/types'

const APIs = [
  { key: 'ibama', nome: 'IBAMA PAMGIA', cor: 'blue' },
  { key: 'semas', nome: 'SEMAS-PA LDI', cor: 'green' },
  { key: 'prodes', nome: 'PRODES/INPE', cor: 'purple' },
] as const

const corMap = {
  blue: { bg: 'bg-blue-50', border: 'border-blue-200', text: 'text-blue-700' },
  green: { bg: 'bg-green-50', border: 'border-green-200', text: 'text-green-700' },
  purple: { bg: 'bg-purple-50', border: 'border-purple-200', text: 'text-purple-700' },
}

export default function ApiStatusPanel() {
  const [status, setStatus] = useState<StatusAPIsExternas | null>(null)
  const [carregando, setCarregando] = useState(false)
  const [erro, setErro] = useState<string | null>(null)

  const carregarStatus = async () => {
    try {
      setCarregando(true)
      setErro(null)
      const dados = await adminService.verificarStatusAPIs()
      setStatus(dados)
    } catch (err) {
      setErro(err instanceof Error ? err.message : 'Erro ao verificar status')
    } finally {
      setCarregando(false)
    }
  }

  useEffect(() => {
    carregarStatus()
    const intervalo = setInterval(carregarStatus, 60000) // 60s
    return () => clearInterval(intervalo)
  }, [])

  if (!status) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-gray-500">Carregando status das APIs...</div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {erro && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
          {erro}
        </div>
      )}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {APIs.map(({ key, nome, cor }) => {
          const api = status[key as keyof StatusAPIsExternas]
          const cores = corMap[cor]
          const statusBadge = api.online ? '🟢 Online' : '🔴 Offline'

          return (
            <div key={key} className={`rounded-lg border p-6 ${cores.bg} ${cores.border}`}>
              <div className="flex items-center justify-between mb-3">
                <p className={`text-sm font-semibold ${cores.text}`}>{nome}</p>
              </div>

              <div className="mb-3">
                <p className={`text-lg font-bold ${cores.text}`}>{statusBadge}</p>
              </div>

              {api.online && api.latencia_ms ? (
                <p className={`text-xs ${cores.text} opacity-75`}>
                  Latência: {api.latencia_ms}ms
                </p>
              ) : (
                <p className={`text-xs ${cores.text} opacity-75`}>
                  Sem resposta
                </p>
              )}

              <p className={`text-xs ${cores.text} opacity-50 mt-2`}>
                {new Date(api.ultima_verificacao).toLocaleTimeString('pt-BR')}
              </p>
            </div>
          )
        })}
      </div>

      <button
        onClick={carregarStatus}
        disabled={carregando}
        className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition-colors disabled:opacity-60 text-sm"
      >
        {carregando ? 'Verificando...' : 'Verificar Agora'}
      </button>
    </div>
  )
}
