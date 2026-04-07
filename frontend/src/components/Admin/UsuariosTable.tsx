'use client'

import { useState } from 'react'
import type { UsuarioAdmin } from '@/types'
import LimiteModal from './LimiteModal'

interface Props {
  usuarios: UsuarioAdmin[]
  onToggleAtivo: (id: string, ativo: boolean) => Promise<void>
  onEditarLimite: (id: string, limite: number | null) => Promise<void>
  carregando?: boolean
}

const perfilCores: Record<string, string> = {
  admin: 'bg-red-100 text-red-800',
  produtor: 'bg-green-100 text-green-800',
  trader: 'bg-blue-100 text-blue-800',
  consultor: 'bg-purple-100 text-purple-800',
}

export default function UsuariosTable({
  usuarios,
  onToggleAtivo,
  onEditarLimite,
  carregando = false,
}: Props) {
  const [usuarioSelecionado, setUsuarioSelecionado] = useState<UsuarioAdmin | null>(null)
  const [salvando, setSalvando] = useState<string | null>(null)

  const handleSalvarLimite = async (limite: number | null) => {
    if (usuarioSelecionado) {
      setSalvando(usuarioSelecionado.id)
      try {
        await onEditarLimite(usuarioSelecionado.id, limite)
      } finally {
        setSalvando(null)
        setUsuarioSelecionado(null)
      }
    }
  }

  const handleToggle = async (usuario: UsuarioAdmin) => {
    setSalvando(usuario.id)
    try {
      await onToggleAtivo(usuario.id, !usuario.ativo)
    } finally {
      setSalvando(null)
    }
  }

  return (
    <>
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                <th className="text-left py-3 px-4 font-semibold text-gray-700">Nome</th>
                <th className="text-left py-3 px-4 font-semibold text-gray-700">E-mail</th>
                <th className="text-left py-3 px-4 font-semibold text-gray-700">Perfil</th>
                <th className="text-center py-3 px-4 font-semibold text-gray-700">Status</th>
                <th className="text-center py-3 px-4 font-semibold text-gray-700">Consultas/Mês</th>
                <th className="text-center py-3 px-4 font-semibold text-gray-700">Limite</th>
                <th className="text-left py-3 px-4 font-semibold text-gray-700">Criado em</th>
                <th className="text-center py-3 px-4 font-semibold text-gray-700">Ações</th>
              </tr>
            </thead>
            <tbody>
              {usuarios.map((usuario) => (
                <tr key={usuario.id} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="py-3 px-4 font-medium text-gray-800">{usuario.nome}</td>
                  <td className="py-3 px-4 text-gray-600 text-xs">{usuario.email}</td>
                  <td className="py-3 px-4">
                    <span
                      className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                        perfilCores[usuario.perfil] || 'bg-gray-100 text-gray-800'
                      }`}
                    >
                      {usuario.perfil}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-center">
                    <span
                      className={`px-2 py-1 rounded text-xs font-semibold ${
                        usuario.ativo
                          ? 'bg-green-100 text-green-800'
                          : 'bg-red-100 text-red-800'
                      }`}
                    >
                      {usuario.ativo ? 'Ativo' : 'Inativo'}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-center text-gray-800 font-semibold">
                    {usuario.consultas_mes_atual}
                  </td>
                  <td className="py-3 px-4 text-center text-gray-600">
                    {usuario.limite_consultas === null ? '∞' : usuario.limite_consultas}
                  </td>
                  <td className="py-3 px-4 text-gray-600 text-xs">
                    {new Date(usuario.criado_em).toLocaleDateString('pt-BR')}
                  </td>
                  <td className="py-3 px-4 text-center">
                    <div className="flex gap-2 justify-center">
                      <button
                        onClick={() => handleToggle(usuario)}
                        disabled={carregando || salvando === usuario.id}
                        className="text-xs px-2 py-1 rounded border transition-colors disabled:opacity-60"
                        title={usuario.ativo ? 'Desativar' : 'Ativar'}
                      >
                        {usuario.ativo ? '🔓' : '🔒'}
                      </button>
                      <button
                        onClick={() => setUsuarioSelecionado(usuario)}
                        disabled={carregando || salvando === usuario.id}
                        className="text-xs px-2 py-1 rounded border border-blue-300 text-blue-700 hover:bg-blue-50 transition-colors disabled:opacity-60"
                      >
                        ⚙️
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal de limite */}
      {usuarioSelecionado && (
        <LimiteModal
          usuario={usuarioSelecionado}
          onSalvar={handleSalvarLimite}
          onFechar={() => setUsuarioSelecionado(null)}
          salvando={salvando === usuarioSelecionado.id}
        />
      )}
    </>
  )
}
