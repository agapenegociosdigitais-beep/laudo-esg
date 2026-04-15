'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { adminService } from '@/services/api'
import { authStorage } from '@/services/auth'
import type { EstatisticasAdmin, UsuarioAdmin } from '@/types'
import AdminStats from '@/components/Admin/AdminStats'
import UsuariosTable from '@/components/Admin/UsuariosTable'
import ApiStatusPanel from '@/components/Admin/ApiStatusPanel'
import AnalisesTable from '@/components/Admin/AnalisesTable'

export default function AdminPage() {
  const router = useRouter()
  const [stats, setStats] = useState<EstatisticasAdmin | null>(null)
  const [usuarios, setUsuarios] = useState<UsuarioAdmin[]>([])
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState<string | null>(null)

  useEffect(() => {
    // Verificação de autenticação + perfil admin
    const usuario = authStorage.obterUsuario()
    if (!usuario) {
      router.push('/login')
      return
    }
    if (usuario.perfil !== 'admin') {
      router.push('/dashboard')
      return
    }

    // Carrega dados
    carregarDados()
  }, [router])

  const carregarDados = async () => {
    try {
      setCarregando(true)
      setErro(null)
      const [statsData, usuariosData] = await Promise.all([
        adminService.obterEstatisticas(),
        adminService.listarUsuarios(1, 50),
      ])
      setStats(statsData)
      setUsuarios(usuariosData)
    } catch (err) {
      setErro(err instanceof Error ? err.message : 'Erro ao carregar dados.')
    } finally {
      setCarregando(false)
    }
  }

  const handleToggleAtivo = async (id: string, ativo: boolean) => {
    try {
      if (ativo) {
        await adminService.ativarUsuario(id)
      } else {
        await adminService.desativarUsuario(id)
      }
      // Atualiza lista local
      setUsuarios((prev) =>
        prev.map((u) => (u.id === id ? { ...u, ativo } : u))
      )
      // Recarrega estatísticas
      const novasStats = await adminService.obterEstatisticas()
      setStats(novasStats)
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Erro ao atualizar usuário.')
    }
  }

  const handleEditarLimite = async (id: string, limite: number | null) => {
    try {
      await adminService.atualizarLimite(id, limite)
      // Atualiza lista local
      setUsuarios((prev) =>
        prev.map((u) => (u.id === id ? { ...u, limite_consultas: limite } : u))
      )
      // Recarrega estatísticas
      const novasStats = await adminService.obterEstatisticas()
      setStats(novasStats)
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Erro ao atualizar limite.')
    }
  }

  if (carregando) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-100">
        <div className="text-gray-600">⏳ Carregando...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-100 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Painel Administrativo</h1>
          <p className="text-gray-600 mt-1">Controle de usuários, quotas e estatísticas</p>
        </div>

        {erro && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
            {erro}
          </div>
        )}

        {/* Estatísticas */}
        {stats && <AdminStats stats={stats} />}

        {/* Tabela de usuários */}
        <div className="mt-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Usuários Cadastrados</h2>
          <UsuariosTable
            usuarios={usuarios}
            onToggleAtivo={handleToggleAtivo}
            onEditarLimite={handleEditarLimite}
            carregando={carregando}
          />
        </div>

        {/* Status das APIs */}
        <div className="mt-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Status das APIs Externas</h2>
          <ApiStatusPanel />
        </div>

        {/* Análises Recentes */}
        <div className="mt-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Análises Recentes</h2>
          <AnalisesTable />
        </div>
      </div>
    </div>
  )
}
