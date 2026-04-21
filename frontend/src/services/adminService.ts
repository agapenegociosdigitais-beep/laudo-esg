import axios from 'axios';

const _RAW_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const BASE_URL = _RAW_BASE.replace(/\/+$/g, '').replace(/\/api\/v1$/i, '')

const apiClient = axios.create({
  baseURL: `${BASE_URL}/api/v1`,
  timeout: 30000,
});

apiClient.interceptors.request.use((config) => {
  const token = typeof window !== 'undefined' ? localStorage.getItem('admin_token') : null;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('admin_token');
      if (typeof window !== 'undefined') {
        window.location.href = '/admin/login';
      }
    }
    throw error;
  }
);

export const adminService = {
  // AUTENTICAÇÃO
  login: async (email: string, password: string) => {
    const res = await apiClient.post('/admin/login', { email, password });
    if (res.data.access_token) {
      if (typeof window !== 'undefined') {
        localStorage.setItem('admin_token', res.data.access_token);
      }
    }
    return res.data;
  },

  // CLIENTES
  listarClientes: async (page = 1, pageSize = 20, status?: string, search?: string) => {
    const res = await apiClient.get('/admin/clientes', {
      params: { page, page_size: pageSize, status, search },
    });
    return res.data;
  },

  aprovarCliente: async (id: string) => {
    const res = await apiClient.patch(`/admin/clientes/${id}/aprovar`);
    return res.data;
  },

  bloquearCliente: async (id: string) => {
    const res = await apiClient.patch(`/admin/clientes/${id}/bloquear`);
    return res.data;
  },

  suspenderCliente: async (id: string) => {
    const res = await apiClient.patch(`/admin/clientes/${id}/suspender`);
    return res.data;
  },

  editarLimite: async (id: string, novoLimite: number | null) => {
    const res = await apiClient.patch(`/admin/clientes/${id}/limite`, { novo_limite: novoLimite });
    return res.data;
  },

  getMe: async () => {
    const res = await apiClient.get('/admin/me');
    return res.data;
  },

  logout: async () => {
    await apiClient.post('/admin/logout');
  },

  // DASHBOARD
  getMetricasOverview: async () => {
    const res = await apiClient.get('/admin/metrics/overview');
    return res.data;
  },

  getGraficos: async () => {
    const res = await apiClient.get('/admin/metrics/graficos');
    return res.data;
  },

  getClientePerfil: async (id: string) => {
    const res = await apiClient.get(`/admin/clientes/${id}`);
    return res.data;
  },

  desaprovarCliente: async (id: string) => {
    const res = await apiClient.patch(`/admin/clientes/${id}/desaprovar`);
    return res.data;
  },

  // NOTIFICAÇÕES
  listarNotificacoes: async (page = 1) => {
    const res = await apiClient.get('/admin/notificacoes', {
      params: { page, page_size: 20 },
    });
    return res.data;
  },

  contarNotificacoesNaoLidas: async () => {
    const res = await apiClient.get('/admin/notificacoes/unread-count');
    return res.data.unread_count;
  },

  marcarNotificacaoLida: async (id: string) => {
    const res = await apiClient.patch(`/admin/notificacoes/${id}/ler`);
    return res.data;
  },

  // CONFIGURAÇÕES
  alterarSenha: async (senhaAtual: string, senhaNova: string) => {
    const res = await apiClient.patch('/admin/config/password', {
      senha_atual: senhaAtual,
      senha_nova: senhaNova,
    });
    return res.data;
  },

  getInfoSistema: async () => {
    const res = await apiClient.get('/admin/config/info');
    return res.data;
  },

  // UTILITÁRIOS
  getToken: () => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('admin_token');
    }
    return null;
  },

  clearToken: () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('admin_token');
    }
  },
};
