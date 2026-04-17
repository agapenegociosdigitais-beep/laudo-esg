# 🚀 Setup Frontend Painel Admin — Quick Start

## Fase 1: Autenticação Admin (1h)

### 1.1 Criar Contexto de Autenticação

```bash
# Arquivo: frontend/src/contexts/AdminAuthContext.tsx

'use client';

import { createContext, useContext, useState, useCallback, useEffect, ReactNode } from 'react';
import { adminService } from '@/services/adminService';
import { AdminUser, AdminTokenResponse } from '@/types/admin';

interface AdminAuthContextType {
  admin: AdminUser | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<void>;
}

const AdminAuthContext = createContext<AdminAuthContextType | null>(null);

export function AdminAuthProvider({ children }: { children: ReactNode }) {
  const [admin, setAdmin] = useState<AdminUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Verificar se há token salvo ao iniciar
  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('admin_token');
      if (token) {
        try {
          const me = await adminService.getMe();
          setAdmin(me);
        } catch (error) {
          localStorage.removeItem('admin_token');
          localStorage.removeItem('admin_user');
        }
      }
      setIsLoading(false);
    };

    checkAuth();
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    setIsLoading(true);
    try {
      const response = await adminService.login(email, password);
      setAdmin(response.admin);
      localStorage.setItem('admin_token', response.access_token);
      localStorage.setItem('admin_user', JSON.stringify(response.admin));
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    localStorage.removeItem('admin_token');
    localStorage.removeItem('admin_user');
    setAdmin(null);
  }, []);

  const refreshToken = useCallback(async () => {
    try {
      const response = await adminService.getMe();
      setAdmin(response);
    } catch (error) {
      logout();
    }
  }, [logout]);

  return (
    <AdminAuthContext.Provider value={{
      admin,
      isLoading,
      isAuthenticated: !!admin,
      login,
      logout,
      refreshToken,
    }}>
      {children}
    </AdminAuthContext.Provider>
  );
}

export function useAdminAuth() {
  const context = useContext(AdminAuthContext);
  if (!context) {
    throw new Error('useAdminAuth deve ser usado dentro de AdminAuthProvider');
  }
  return context;
}
```

### 1.2 Criar Admin Service

```bash
# Arquivo: frontend/src/services/adminService.ts

import axios, { AxiosInstance } from 'axios';
import { AdminTokenResponse, ClienteListaItem, ClientePerfil, OverviewMetricas } from '@/types/admin';

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const apiClient: AxiosInstance = axios.create({
  baseURL: `${BASE_URL}/api/v1`,
  timeout: 30000,
});

// Interceptador de requisição: adicionar token
apiClient.interceptors.request.use((config) => {
  const token = typeof window !== 'undefined' ? localStorage.getItem('admin_token') : null;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Interceptador de resposta: tratar erros
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('admin_token');
      window.location.href = '/admin/login';
    }
    throw error;
  }
);

export const adminService = {
  // AUTENTICAÇÃO
  login: async (email: string, password: string): Promise<AdminTokenResponse> => {
    const res = await apiClient.post('/admin/login', { email, password });
    return res.data;
  },

  logout: async (): Promise<void> => {
    await apiClient.post('/admin/logout');
  },

  getMe: async () => {
    const res = await apiClient.get('/admin/me');
    return res.data;
  },

  // DASHBOARD
  getMetricasOverview: async (): Promise<OverviewMetricas> => {
    const res = await apiClient.get('/admin/metrics/overview');
    return res.data;
  },

  getGraficos: async () => {
    const res = await apiClient.get('/admin/metrics/graficos');
    return res.data;
  },

  // CLIENTES
  listarClientes: async (page = 1, pageSize = 20, status?: string, search?: string) => {
    const res = await apiClient.get('/admin/clientes', {
      params: { page, page_size: pageSize, status, search },
    });
    return res.data;
  },

  getClientePerfil: async (clienteId: string): Promise<ClientePerfil> => {
    const res = await apiClient.get(`/admin/clientes/${clienteId}`);
    return res.data;
  },

  aprovarCliente: async (clienteId: string) => {
    const res = await apiClient.patch(`/admin/clientes/${clienteId}/aprovar`);
    return res.data;
  },

  desaprovarCliente: async (clienteId: string) => {
    const res = await apiClient.patch(`/admin/clientes/${clienteId}/desaprovar`);
    return res.data;
  },

  suspenderCliente: async (clienteId: string) => {
    const res = await apiClient.patch(`/admin/clientes/${clienteId}/suspender`);
    return res.data;
  },

  editarLimite: async (clienteId: string, novoLimite: number | null) => {
    const res = await apiClient.patch(`/admin/clientes/${clienteId}/limite`, {
      novo_limite: novoLimite,
    });
    return res.data;
  },

  // NOTIFICAÇÕES
  listarNotificacoes: async (page = 1, pageSize = 20) => {
    const res = await apiClient.get('/admin/notificacoes', {
      params: { page, page_size: pageSize },
    });
    return res.data;
  },

  conharNotificacoesNaoLidas: async (): Promise<number> => {
    const res = await apiClient.get('/admin/notificacoes/unread-count');
    return res.data.unread_count;
  },

  marcarNotificacaoLida: async (notifId: string) => {
    const res = await apiClient.patch(`/admin/notificacoes/${notifId}/ler`);
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
};
```

### 1.3 Criar Tipos TypeScript

```bash
# Arquivo: frontend/src/types/admin.ts

export interface AdminUser {
  id: string;
  email: string;
  role: string;
  last_login?: string;
  created_at: string;
}

export interface AdminTokenResponse {
  access_token: string;
  token_type: string;
  admin: AdminUser;
}

export interface ClienteListaItem {
  id: string;
  nome: string;
  email: string;
  ativo: boolean;
  criado_em: string;
  consultas_mes_atual: number;
  limite_consultas?: number;
}

export interface ClientePerfil {
  id: string;
  email: string;
  nome: string;
  empresa?: string;
  perfil: string;
  ativo: boolean;
  limite_consultas?: number;
  consultas_mes_atual: number;
  criado_em: string;
}

export interface OverviewMetricas {
  total_clientes: number;
  clientes_ativos: number;
  clientes_inativos: number;
  clientes_pendentes: number;
  total_pesquisas_hoje: number;
  total_pesquisas_semana: number;
  total_pesquisas_mes: number;
  total_pesquisas_geral: number;
  total_cars_unicos: number;
  total_cars_com_problemas: number;
  cars_com_prodes: number;
  cars_com_embargo: number;
  cars_com_desmatamento: number;
}

export interface PesquisasPorDia {
  data: string;
  quantidade: number;
}

export interface CARsPorStatus {
  categoria: string;
  quantidade: number;
  percentual: number;
}

export interface TopCliente {
  nome: string;
  email: string;
  quantidade_pesquisas: number;
  limite_mensal?: number;
}

export interface DashboardGraficos {
  pesquisas_por_dia: PesquisasPorDia[];
  cars_por_status: CARsPorStatus[];
  top_clientes: TopCliente[];
}

export interface Notificacao {
  id: string;
  type: string;
  title: string;
  message?: string;
  related_car?: string;
  is_read: boolean;
  created_at: string;
}
```

### 1.4 Criar Página de Login

```bash
# Arquivo: frontend/src/app/admin/login/page.tsx

'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAdminAuth } from '@/contexts/AdminAuthContext';

export default function AdminLoginPage() {
  const router = useRouter();
  const { login, isLoading } = useAdminAuth();
  const [email, setEmail] = useState('admin@georural.com');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    try {
      await login(email, password);
      router.push('/admin/dashboard');
    } catch (err) {
      setError('Email ou senha incorretos');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-900 to-green-700 flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-2xl p-8">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="text-4xl font-bold text-green-700 mb-2">🌱</div>
          <h1 className="text-2xl font-bold text-gray-800">GeoRural</h1>
          <p className="text-sm text-gray-500 mt-1">Painel Administrativo</p>
        </div>

        {/* Formulário */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 outline-none"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Senha
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 outline-none"
              required
              autoComplete="current-password"
            />
          </div>

          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-2 bg-green-600 text-white font-semibold rounded-lg hover:bg-green-700 disabled:opacity-50"
          >
            {isLoading ? 'Entrando...' : 'Entrar'}
          </button>
        </form>

        {/* Rodapé */}
        <p className="text-center text-xs text-gray-500 mt-6">
          Painel exclusivo para administradores
        </p>
      </div>
    </div>
  );
}
```

### 1.5 Criar Middleware de Proteção

```bash
# Arquivo: frontend/src/middleware.ts

import { NextRequest, NextResponse } from 'next/server';

export function middleware(request: NextRequest) {
  const pathname = request.nextUrl.pathname;

  // Se é rota admin
  if (pathname.startsWith('/admin')) {
    const token = request.cookies.get('admin_token');

    // Se não tem token e não é login, redireciona para login
    if (!token && pathname !== '/admin/login') {
      return NextResponse.redirect(new URL('/admin/login', request.url));
    }

    // Se tem token e é login, redireciona para dashboard
    if (token && pathname === '/admin/login') {
      return NextResponse.redirect(new URL('/admin/dashboard', request.url));
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/admin/:path*'],
};
```

---

## Fase 2: Layout Admin (1-2h)

### 2.1 Criar RootLayout Protegido

```bash
# Arquivo: frontend/src/app/admin/layout.tsx

'use client';

import { AdminAuthProvider, useAdminAuth } from '@/contexts/AdminAuthContext';
import AdminSidebar from './components/AdminSidebar';
import AdminHeader from './components/AdminHeader';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

function AdminLayoutContent({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAdminAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/admin/login');
    }
  }, [isAuthenticated, isLoading, router]);

  if (isLoading) {
    return <div className="flex items-center justify-center min-h-screen">Carregando...</div>;
  }

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="flex h-screen bg-gray-50">
      <AdminSidebar />
      <div className="flex-1 overflow-auto">
        <AdminHeader />
        <main className="p-8">{children}</main>
      </div>
    </div>
  );
}

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AdminAuthProvider>
      <AdminLayoutContent>{children}</AdminLayoutContent>
    </AdminAuthProvider>
  );
}
```

---

## 🎯 Próximas Etapas

1. **Criar componentes base**: AdminSidebar, AdminHeader, MetricCard
2. **Implementar dashboard**: Com Recharts
3. **Adicionar páginas de clientes e pesquisas**
4. **Integrar exportação PDF/Excel**
5. **Testes E2E**

---

## 📦 Dependências Necessárias

```bash
npm install recharts jspdf autoTable xlsx axios swr sonner
```

Adione ao `package.json`:
```json
{
  "dependencies": {
    "recharts": "^2.10.0",
    "jspdf": "^2.5.0",
    "autoTable": "^3.6.0",
    "xlsx": "^0.18.5",
    "axios": "^1.6.0",
    "swr": "^2.2.0",
    "sonner": "^1.2.0"
  }
}
```

---

**Status**: Backend 100% ✅ | Frontend 0% ⏳
