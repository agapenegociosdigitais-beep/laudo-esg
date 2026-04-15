/**
 * Cliente HTTP centralizado para comunicação com a API Eureka Terra.
 * Injeta o token JWT automaticamente em todas as requisições autenticadas.
 */
import axios, { AxiosError, AxiosInstance } from 'axios'
import Cookies from 'js-cookie'

import type { Analise, AnaliseAdmin, CARResultado, EstatisticasAdmin, Propriedade, Relatorio, StatusAPIsExternas, TokenResposta, Usuario, UsuarioAdmin } from '@/types'

const BASE_URL =
  typeof window === 'undefined'
    ? (process.env.INTERNAL_API_URL || 'http://backend:8000')
    : (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000')

// Instância base do axios
const api: AxiosInstance = axios.create({
  baseURL: `${BASE_URL}/api/v1`,
  headers: { 'Content-Type': 'application/json' },
  timeout: 30_000,
})

// Interceptor: injeta o token Bearer em cada requisição
api.interceptors.request.use((config) => {
  const token = Cookies.get('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Interceptor: traduz erros da API para mensagens legíveis
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ detail: unknown }>) => {
    const detail = error.response?.data?.detail
    let mensagem = 'Erro desconhecido. Tente novamente.'

    if (typeof detail === 'string') {
      mensagem = detail
    } else if (Array.isArray(detail) && detail.length > 0) {
      // Erros de validação do Pydantic
      mensagem = (detail as { msg: string }[]).map((e) => e.msg).join('; ')
    } else if (error.request) {
      mensagem = 'Não foi possível conectar ao servidor. Verifique sua conexão.'
    }

    return Promise.reject(new Error(mensagem))
  }
)

// ─── Auth ────────────────────────────────────────────────────────────────────

export const authService = {
  async login(email: string, senha: string): Promise<TokenResposta> {
    const { data } = await api.post<TokenResposta>('/auth/login', { email, senha })
    return data
  },

  async registrar(payload: {
    email: string
    senha: string
    nome: string
    empresa?: string
    perfil: string
  }): Promise<{ usuario: Usuario; mensagem: string; requer_aprovacao: boolean }> {
    const { data } = await api.post<{ usuario: Usuario; mensagem: string; requer_aprovacao: boolean }>('/auth/registrar', payload)
    return data
  },

  async obterPerfil() {
    const { data } = await api.get('/auth/me')
    return data
  },
}

// ─── Propriedades ────────────────────────────────────────────────────────────

export const propriedadeService = {
  async buscarPorCAR(numero_car: string): Promise<CARResultado> {
    const { data } = await api.post<CARResultado>('/propriedades/buscar-car', { numero_car })
    return data
  },

  async obterPorId(id: string): Promise<Propriedade> {
    const { data } = await api.get<Propriedade>(`/propriedades/${id}`)
    return data
  },

  async listar(pagina = 1, por_pagina = 20) {
    const { data } = await api.get('/propriedades/', { params: { pagina, por_pagina } })
    return data
  },
}

// ─── Análises ────────────────────────────────────────────────────────────────

export const analiseService = {
  async iniciar(payload: {
    propriedade_id: string
    data_inicio: string
    data_fim: string
  }): Promise<Analise> {
    const { data } = await api.post<Analise>('/analises/', payload)
    return data
  },

  async obterPorId(id: string): Promise<Analise> {
    const { data } = await api.get<Analise>(`/analises/${id}`)
    return data
  },

  async listarPorPropriedade(propriedade_id: string): Promise<Analise[]> {
    const { data } = await api.get<Analise[]>(`/analises/propriedade/${propriedade_id}`)
    return data
  },

  // Polling: verifica a cada `intervalMs` ms até status ser 'concluido' ou 'erro'
  async aguardarConclusao(
    analiseId: string,
    onAtualizar: (analise: Analise) => void,
    intervalMs = 3000,
    maxTentativas = 40
  ): Promise<Analise> {
    return new Promise((resolve, reject) => {
      let tentativas = 0
      const intervalo = setInterval(async () => {
        tentativas++
        try {
          const analise = await analiseService.obterPorId(analiseId)
          onAtualizar(analise)
          if (analise.status === 'concluido' || analise.status === 'erro') {
            clearInterval(intervalo)
            resolve(analise)
          } else if (tentativas >= maxTentativas) {
            clearInterval(intervalo)
            reject(new Error('Tempo limite de processamento excedido.'))
          }
        } catch (err) {
          clearInterval(intervalo)
          reject(err)
        }
      }, intervalMs)
    })
  },
}

// ─── Relatórios ──────────────────────────────────────────────────────────────

export const relatorioService = {
  async gerar(analise_id: string): Promise<Relatorio> {
    const { data } = await api.post<Relatorio>('/relatorios/gerar', { analise_id })
    return data
  },

  urlDownload(relatorio_id: string): string {
    const token = Cookies.get('token')
    return `${BASE_URL}/api/v1/relatorios/${relatorio_id}/download?token=${token}`
  },
}

// ─── Administração ───────────────────────────────────────────────────────────

export const adminService = {
  async listarUsuarios(pagina = 1, por_pagina = 20): Promise<UsuarioAdmin[]> {
    const { data } = await api.get<UsuarioAdmin[]>('/admin/usuarios', {
      params: { pagina, por_pagina },
    })
    return data
  },

  async ativarUsuario(usuario_id: string): Promise<void> {
    await api.patch(`/admin/usuarios/${usuario_id}/ativar`)
  },

  async desativarUsuario(usuario_id: string): Promise<void> {
    await api.patch(`/admin/usuarios/${usuario_id}/desativar`)
  },

  async atualizarLimite(usuario_id: string, limite_consultas: number | null): Promise<void> {
    await api.patch(`/admin/usuarios/${usuario_id}/limite`, { limite_consultas })
  },

  async obterEstatisticas(): Promise<EstatisticasAdmin> {
    const { data } = await api.get<EstatisticasAdmin>('/admin/estatisticas')
    return data
  },

  async listarAnalises(status?: string, pagina = 1, por_pagina = 20): Promise<AnaliseAdmin[]> {
    const { data } = await api.get<AnaliseAdmin[]>('/admin/analises', {
      params: { status, pagina, por_pagina },
    })
    return data
  },

  async verificarStatusAPIs(): Promise<StatusAPIsExternas> {
    const { data } = await api.get<StatusAPIsExternas>('/admin/apis/status')
    return data
  },
}

export default api



