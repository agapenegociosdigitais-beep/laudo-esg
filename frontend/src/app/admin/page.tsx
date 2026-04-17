'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { adminService } from '@/services/api'
import { authStorage } from '@/services/auth'
import type { EstatisticasAdmin, UsuarioAdmin } from '@/types'
import AdminStats from '@/components/Admin/AdminStats'
import UsuariosTable from '@/components/Admin/UsuariosTable'
import ApiStatusPanel from '@/components/Admin/ApiStatusPanel'
import AlertasPanel from '@/components/Admin/AlertasPanel'
import AnalisesTable from '@/components/Admin/AnalisesTable'
import CARsProblematicosPanel from '@/components/Admin/CARsProblematicosPanel'

type Secao = 'overview' | 'usuarios' | 'alertas' | 'cars' | 'apis'

export default function AdminPage() {
  const router = useRouter()
  const [stats, setStats] = useState<EstatisticasAdmin | null>(null)
  const [usuarios, setUsuarios] = useState<UsuarioAdmin[]>([])
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState<string | null>(null)
  const [secaoAtiva, setSecaoAtiva] = useState<Secao>('overview')

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
      setUsuarios((prev) =>
        prev.map((u) => (u.id === id ? { ...u, ativo } : u))
      )
      const novasStats = await adminService.obterEstatisticas()
      setStats(novasStats)
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Erro ao atualizar usuário.')
    }
  }

  const handleEditarLimite = async (id: string, limite: number | null) => {
    try {
      await adminService.atualizarLimite(id, limite)
      setUsuarios((prev) =>
        prev.map((u) => (u.id === id ? { ...u, limite_consultas: limite } : u))
      )
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
    <div className="flex min-h-screen bg-gray-100">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-gray-200 shadow-sm">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-lg font-bold text-gray-900">Administração</h2>
          <p className="text-xs text-gray-500 mt-1">Eureka Terra</p>
        </div>

        <nav className="p-4 space-y-2">
          <button
            onClick={() => setSecaoAtiva('overview')}
            className={`w-full text-left px-4 py-3 rounded-lg font-semibold text-sm transition-colors ${
              secaoAtiva === 'overview'
                ? 'bg-blue-100 text-blue-800 border-l-4 border-blue-600'
                : 'text-gray-700 hover:bg-gray-100'
            }`}
          >
            📊 Visão Geral
          </button>

          <button
            onClick={() => setSecaoAtiva('usuarios')}
            className={`w-full text-left px-4 py-3 rounded-lg font-semibold text-sm transition-colors ${
              secaoAtiva === 'usuarios'
                ? 'bg-blue-100 text-blue-800 border-l-4 border-blue-600'
                : 'text-gray-700 hover:bg-gray-100'
            }`}
          >
            👥 Usuários
          </button>

          <button
            onClick={() => setSecaoAtiva('alertas')}
            className={`w-full text-left px-4 py-3 rounded-lg font-semibold text-sm transition-colors ${
              secaoAtiva === 'alertas'
                ? 'bg-blue-100 text-blue-800 border-l-4 border-blue-600'
                : 'text-gray-700 hover:bg-gray-100'
            }`}
          >
            ⚠️ Alertas
          </button>

          <button
            onClick={() => setSecaoAtiva('cars')}
            className={`w-full text-left px-4 py-3 rounded-lg font-semibold text-sm transition-colors ${
              secaoAtiva === 'cars'
                ? 'bg-blue-100 text-blue-800 border-l-4 border-blue-600'
                : 'text-gray-700 hover:bg-gray-100'
            }`}
          >
            🚨 CARs Problemáticos
          </button>

          <button
            onClick={() => setSecaoAtiva('apis')}
            className={`w-full text-left px-4 py-3 rounded-lg font-semibold text-sm transition-colors ${
              secaoAtiva === 'apis'
                ? 'bg-blue-100 text-blue-800 border-l-4 border-blue-600'
                : 'text-gray-700 hover:bg-gray-100'
            }`}
          >
            🌐 APIs Externas
          </button>
        </nav>
      </aside>

      {/* Main Content */}
      <main className="flex-1 p-6">
        <div className="max-w-6xl">
          {/* Header */}
          <div className="mb-6">
            <h1 className="text-3xl font-bold text-gray-900">Painel Administrativo</h1>
            <p className="text-gray-600 mt-1">
              {secaoAtiva === 'overview' && 'Visão geral da plataforma'}
              {secaoAtiva === 'usuarios' && 'Gerenciamento de usuários'}
              {secaoAtiva === 'alertas' && 'Propriedades críticas com embargo e desmatamento'}
              {secaoAtiva === 'cars' && 'CARs problemáticos: PRODES, Embargo, Desmatamento e Resumo'}
              {secaoAtiva === 'apis' && 'Status das APIs externas'}
            </p>
          </div>

          {erro && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
              {erro}
            </div>
          )}

          {/* Seção: Overview */}
          {secaoAtiva === 'overview' && (
            <div className="space-y-8">
              {stats && <AdminStats stats={stats} />}

              {/* Alertas */}
              <div>
                <h2 className="text-2xl font-bold text-red-700 mb-4">⚠️ Alertas — Propriedades Críticas</h2>
                <AlertasPanel />
              </div>
            </div>
          )}

          {/* Seção: Usuários */}
          {secaoAtiva === 'usuarios' && (
            <div>
              <UsuariosTable
                usuarios={usuarios}
                onToggleAtivo={handleToggleAtivo}
                onEditarLimite={handleEditarLimite}
                carregando={carregando}
              />
            </div>
          )}

          {/* Seção: Alertas */}
          {secaoAtiva === 'alertas' && (
            <div>
              <AlertasPanel />
            </div>
          )}

          {/* Seção: CARs Problemáticos */}
          {secaoAtiva === 'cars' && (
            <div>
              <CARsProblematicosPanel />
            </div>
          )}

          {/* Seção: APIs */}
          {secaoAtiva === 'apis' && (
            <div className="space-y-8">
              <ApiStatusPanel />
              <div>
                <h2 className="text-2xl font-bold text-gray-900 mb-4">Análises Recentes</h2>
                <AnalisesTable />
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
