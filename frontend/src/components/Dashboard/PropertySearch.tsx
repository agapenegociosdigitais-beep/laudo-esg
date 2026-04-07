'use client'

/**
 * Componente de busca de propriedade pelo número do CAR.
 */
import { useState } from 'react'
import type { CARResultado } from '@/types'
import { propriedadeService } from '@/services/api'

interface Props {
  onEncontrada: (resultado: CARResultado) => void
}

// Exemplos de CARs para facilitar testes em desenvolvimento
const EXEMPLOS_CAR = [
  'MT-5107248-4F7A21B3C8E14D9A9F2B3C4D5E6F7A8B',
  'PA-1500602-2A3B4C5D6E7F8A9B0C1D2E3F4A5B6C7D',
  'GO-5208004-1B2C3D4E5F6A7B8C9D0E1F2A3B4C5D6E',
]

export default function PropertySearch({ onEncontrada }: Props) {
  const [numeroCar, setNumeroCar] = useState('')
  const [carregando, setCarregando] = useState(false)
  const [erro, setErro] = useState('')

  async function handleBuscar(car?: string) {
    const valor = (car || numeroCar).trim().toUpperCase()
    if (!valor) {
      setErro('Informe o número do CAR.')
      return
    }

    setErro('')
    setCarregando(true)
    try {
      const resultado = await propriedadeService.buscarPorCAR(valor)
      onEncontrada(resultado)
      setNumeroCar(valor)
    } catch (err: unknown) {
      setErro(err instanceof Error ? err.message : 'Erro ao buscar propriedade.')
    } finally {
      setCarregando(false)
    }
  }

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
      <h2 className="text-lg font-semibold text-gray-800 mb-1">Buscar Propriedade</h2>
      <p className="text-sm text-gray-500 mb-4">
        Informe o número do CAR no formato: <code className="bg-gray-100 px-1 rounded text-xs">UF-IBGE-IDENTIFICADOR</code>
      </p>

      <div className="flex gap-2">
        <input
          type="text"
          value={numeroCar}
          onChange={(e) => setNumeroCar(e.target.value.toUpperCase())}
          onKeyDown={(e) => e.key === 'Enter' && handleBuscar()}
          placeholder="MT-5107248-XXXXXXXXXXXX"
          className="flex-1 px-4 py-2.5 border border-gray-300 rounded-lg text-sm font-mono focus:outline-none focus:ring-2 focus:ring-verde-500 focus:border-transparent"
        />
        <button
          onClick={() => handleBuscar()}
          disabled={carregando}
          className="px-6 py-2.5 bg-verde-700 hover:bg-verde-800 text-white text-sm font-semibold rounded-lg transition-colors disabled:opacity-60 disabled:cursor-not-allowed whitespace-nowrap"
        >
          {carregando ? '⏳ Buscando...' : '🔍 Buscar'}
        </button>
      </div>

      {erro && (
        <p className="mt-2 text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2">{erro}</p>
      )}

      {/* Exemplos de CARs para desenvolvimento */}
      <div className="mt-4">
        <p className="text-xs text-gray-400 mb-2">Exemplos para teste:</p>
        <div className="flex flex-wrap gap-2">
          {EXEMPLOS_CAR.map((car) => (
            <button
              key={car}
              onClick={() => {
                setNumeroCar(car)
                handleBuscar(car)
              }}
              className="text-xs text-verde-700 bg-verde-50 hover:bg-verde-100 border border-verde-200 rounded-md px-2 py-1 font-mono transition-colors"
            >
              {car.substring(0, 20)}…
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
