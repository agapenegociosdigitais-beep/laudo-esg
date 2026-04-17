'use client';

import { useState, useEffect } from 'react';
import { adminService } from '@/services/adminService';

interface Client {
  id: string;
  nome: string;
  email: string;
  telefone: string;
  created_at: string;
  status: string;
  limite_consultas: number;
  consultas_mes_atual: number;
}

interface PaginatedResponse {
  items: Client[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

interface ClientTableProps {
  onSelectClient?: (clientId: string) => void;
  onClientUpdated?: () => void;
}

export function ClientTable({ onSelectClient, onClientUpdated }: ClientTableProps) {
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [search, setSearch] = useState('');
  const [filterStatus, setFilterStatus] = useState('todos');
  const [actionLoading, setActionLoading] = useState<{ [key: string]: string }>({});
  const [actionError, setActionError] = useState<{ [key: string]: string }>({});

  const loadClients = async (pageNum: number, searchTerm: string, status: string) => {
    setLoading(true);
    setError('');
    try {
      const statusParam = status === 'todos' ? undefined : status;
      const response = await adminService.listarClientes(pageNum, 20, statusParam, searchTerm);
      setClients(response.items || []);
      setTotalPages(response.total_pages || 1);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erro ao carregar clientes');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadClients(page, search, filterStatus);
  }, [page, filterStatus]);

  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearch(e.target.value);
    setPage(1);
  };

  const handleSearchSubmit = () => {
    setPage(1);
    loadClients(1, search, filterStatus);
  };

  const handleApprove = async (clientId: string) => {
    setActionLoading((prev) => ({ ...prev, [clientId]: 'approving' }));
    setActionError((prev) => ({ ...prev, [clientId]: '' }));
    try {
      await adminService.aprovarCliente(clientId);
      onClientUpdated?.();
      loadClients(page, search, filterStatus);
    } catch (err: any) {
      setActionError((prev) => ({
        ...prev,
        [clientId]: err.response?.data?.detail || 'Erro ao aprovar',
      }));
    } finally {
      setActionLoading((prev) => ({ ...prev, [clientId]: '' }));
    }
  };

  const handleDisapprove = async (clientId: string) => {
    setActionLoading((prev) => ({ ...prev, [clientId]: 'disapproving' }));
    setActionError((prev) => ({ ...prev, [clientId]: '' }));
    try {
      await adminService.desaprovarCliente(clientId);
      onClientUpdated?.();
      loadClients(page, search, filterStatus);
    } catch (err: any) {
      setActionError((prev) => ({
        ...prev,
        [clientId]: err.response?.data?.detail || 'Erro ao desaprovar',
      }));
    } finally {
      setActionLoading((prev) => ({ ...prev, [clientId]: '' }));
    }
  };

  const handleSuspend = async (clientId: string) => {
    if (!confirm('Tem certeza que deseja suspender este cliente?')) return;
    setActionLoading((prev) => ({ ...prev, [clientId]: 'suspending' }));
    setActionError((prev) => ({ ...prev, [clientId]: '' }));
    try {
      await adminService.suspenderCliente(clientId);
      onClientUpdated?.();
      loadClients(page, search, filterStatus);
    } catch (err: any) {
      setActionError((prev) => ({
        ...prev,
        [clientId]: err.response?.data?.detail || 'Erro ao suspender',
      }));
    } finally {
      setActionLoading((prev) => ({ ...prev, [clientId]: '' }));
    }
  };

  const getStatusBadge = (status: string) => {
    const statusMap: { [key: string]: { bg: string; text: string; label: string } } = {
      ativo: { bg: 'bg-green-100', text: 'text-green-800', label: '✅ Ativo' },
      pendente: { bg: 'bg-yellow-100', text: 'text-yellow-800', label: '⏳ Pendente' },
      suspenso: { bg: 'bg-orange-100', text: 'text-orange-800', label: '⚠️ Suspenso' },
      inativo: { bg: 'bg-red-100', text: 'text-red-800', label: '🚫 Inativo' },
    };
    const config = statusMap[status?.toLowerCase()] || statusMap['pendente'];
    return (
      <span className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${config.bg} ${config.text}`}>
        {config.label}
      </span>
    );
  };

  const getUsagePercent = (current: number, limit: number) => {
    if (limit === 0) return 0;
    return Math.round((current / limit) * 100);
  };

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
        {error}
        <button
          onClick={() => loadClients(page, search, filterStatus)}
          className="ml-4 underline font-semibold"
        >
          Tentar Novamente
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex gap-4 items-end">
        <div className="flex-1">
          <label className="block text-sm font-medium text-gray-700 mb-1">Buscar</label>
          <input
            type="text"
            placeholder="Nome ou email..."
            value={search}
            onChange={handleSearch}
            onKeyDown={(e) => e.key === 'Enter' && handleSearchSubmit()}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 outline-none"
          />
        </div>
        <div className="w-48">
          <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
          <select
            value={filterStatus}
            onChange={(e) => {
              setFilterStatus(e.target.value);
              setPage(1);
            }}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 outline-none"
          >
            <option value="todos">Todos</option>
            <option value="ativo">Ativo</option>
            <option value="pendente">Pendente</option>
            <option value="suspenso">Suspenso</option>
            <option value="inativo">Inativo</option>
          </select>
        </div>
        <button
          onClick={handleSearchSubmit}
          className="px-4 py-2 bg-green-600 text-white font-semibold rounded-lg hover:bg-green-700"
        >
          Buscar
        </button>
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg shadow-sm overflow-hidden border border-gray-200">
        <table className="w-full">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">Nome</th>
              <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">Email</th>
              <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">Telefone</th>
              <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">Data</th>
              <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">Status</th>
              <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">Uso</th>
              <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">Ações</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {loading ? (
              <tr>
                <td colSpan={7} className="px-6 py-8 text-center text-gray-500">
                  Carregando...
                </td>
              </tr>
            ) : clients.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-6 py-8 text-center text-gray-500">
                  Nenhum cliente encontrado
                </td>
              </tr>
            ) : (
              clients.map((client) => (
                <tr
                  key={client.id}
                  className="hover:bg-gray-50 cursor-pointer"
                  onClick={() => onSelectClient?.(client.id)}
                >
                  <td className="px-6 py-4 text-sm text-gray-800 font-medium">{client.nome}</td>
                  <td className="px-6 py-4 text-sm text-gray-600">{client.email}</td>
                  <td className="px-6 py-4 text-sm text-gray-600">{client.telefone || '-'}</td>
                  <td className="px-6 py-4 text-sm text-gray-600">
                    {new Date(client.created_at).toLocaleDateString('pt-BR')}
                  </td>
                  <td className="px-6 py-4 text-sm">{getStatusBadge(client.status)}</td>
                  <td className="px-6 py-4 text-sm">
                    <div className="w-24">
                      <div className="flex justify-between text-xs text-gray-600 mb-1">
                        <span>
                          {client.consultas_mes_atual}/{client.limite_consultas}
                        </span>
                        <span>{getUsagePercent(client.consultas_mes_atual, client.limite_consultas)}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-green-600 h-2 rounded-full transition-all"
                          style={{ width: `${getUsagePercent(client.consultas_mes_atual, client.limite_consultas)}%` }}
                        ></div>
                      </div>
                    </div>
                  </td>
                  <td
                    className="px-6 py-4 text-sm"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <div className="flex gap-2">
                      {client.status !== 'ativo' && (
                        <button
                          onClick={() => handleApprove(client.id)}
                          disabled={actionLoading[client.id] === 'approving'}
                          className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs font-semibold hover:bg-green-200 disabled:opacity-50"
                        >
                          {actionLoading[client.id] === 'approving' ? '...' : 'Aprovar'}
                        </button>
                      )}
                      {client.status === 'ativo' && (
                        <button
                          onClick={() => handleDisapprove(client.id)}
                          disabled={actionLoading[client.id] === 'disapproving'}
                          className="px-2 py-1 bg-red-100 text-red-700 rounded text-xs font-semibold hover:bg-red-200 disabled:opacity-50"
                        >
                          {actionLoading[client.id] === 'disapproving' ? '...' : 'Bloquear'}
                        </button>
                      )}
                      {client.status !== 'suspenso' && client.status !== 'inativo' && (
                        <button
                          onClick={() => handleSuspend(client.id)}
                          disabled={actionLoading[client.id] === 'suspending'}
                          className="px-2 py-1 bg-orange-100 text-orange-700 rounded text-xs font-semibold hover:bg-orange-200 disabled:opacity-50"
                        >
                          {actionLoading[client.id] === 'suspending' ? '...' : 'Suspender'}
                        </button>
                      )}
                    </div>
                    {actionError[client.id] && (
                      <p className="text-red-600 text-xs mt-1">{actionError[client.id]}</p>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex justify-center items-center gap-2">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm font-medium hover:bg-gray-50 disabled:opacity-50"
          >
            ← Anterior
          </button>
          {Array.from({ length: totalPages }, (_, i) => i + 1).map((p) => (
            <button
              key={p}
              onClick={() => setPage(p)}
              className={`px-3 py-2 rounded-lg text-sm font-medium ${
                page === p
                  ? 'bg-green-600 text-white'
                  : 'border border-gray-300 hover:bg-gray-50'
              }`}
            >
              {p}
            </button>
          ))}
          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm font-medium hover:bg-gray-50 disabled:opacity-50"
          >
            Próximo →
          </button>
          <span className="text-sm text-gray-600 ml-4">
            Página {page} de {totalPages}
          </span>
        </div>
      )}
    </div>
  );
}
