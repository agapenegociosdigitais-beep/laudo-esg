'use client';

import { useState, useEffect } from 'react';
import { adminService } from '@/services/adminService';

interface Cliente {
  id: string;
  nome: string;
  email: string;
  telefone: string;
  status: string;
  created_at: string;
  limite_consultas: number | null;
  consultas_mes_atual: number;
}

export function ClientesTable() {
  const [clientes, setClientes] = useState<Cliente[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);

  useEffect(() => {
    loadClientes();
  }, [page]);

  const loadClientes = async () => {
    try {
      setLoading(true);
      const data = await adminService.listarClientes(page);
      setClientes(data.items || []);
    } catch (error) {
      console.error('Erro ao carregar clientes:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAction = async (cliente_id: string, action: 'aprovar' | 'bloquear' | 'suspender') => {
    try {
      const key = (action + 'Cliente') as keyof typeof adminService;
      await adminService[key](cliente_id);
      loadClientes();
    } catch (error) {
      console.error(`Erro ao ${action} cliente:`, error);
    }
  };

  if (loading) return <div className="text-center py-10">Carregando...</div>;

  return (
    <div className="bg-white rounded-lg shadow-sm overflow-hidden">
      <table className="w-full">
        <thead className="bg-gray-50 border-b">
          <tr>
            <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">Nome</th>
            <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">Email</th>
            <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">Telefone</th>
            <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">Status</th>
            <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">Pesquisas</th>
            <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">Ações</th>
          </tr>
        </thead>
        <tbody>
          {clientes.map((cliente) => (
            <tr key={cliente.id} className="border-b hover:bg-gray-50">
              <td className="px-6 py-4 text-sm text-gray-900 font-medium">{cliente.nome}</td>
              <td className="px-6 py-4 text-sm text-gray-600">{cliente.email}</td>
              <td className="px-6 py-4 text-sm text-gray-600">{cliente.telefone}</td>
              <td className="px-6 py-4 text-sm">
                <span
                  className={`px-3 py-1 rounded-full text-xs font-semibold ${
                    cliente.status === 'ativo'
                      ? 'bg-green-100 text-green-800'
                      : cliente.status === 'pendente'
                      ? 'bg-yellow-100 text-yellow-800'
                      : 'bg-red-100 text-red-800'
                  }`}
                >
                  {cliente.status.charAt(0).toUpperCase() + cliente.status.slice(1)}
                </span>
              </td>
              <td className="px-6 py-4 text-sm text-gray-600">
                {cliente.consultas_mes_atual}/{cliente.limite_consultas || '∞'}
              </td>
              <td className="px-6 py-4 text-sm flex gap-2">
                {cliente.status === 'pendente' && (
                  <button
                    onClick={() => handleAction(cliente.id, 'aprovar')}
                    className="px-3 py-1 bg-green-600 text-white text-xs rounded hover:bg-green-700"
                  >
                    Aprovar
                  </button>
                )}
                {cliente.status === 'ativo' && (
                  <>
                    <button
                      onClick={() => handleAction(cliente.id, 'suspender')}
                      className="px-3 py-1 bg-yellow-600 text-white text-xs rounded hover:bg-yellow-700"
                    >
                      Suspender
                    </button>
                    <button
                      onClick={() => handleAction(cliente.id, 'bloquear')}
                      className="px-3 py-1 bg-red-600 text-white text-xs rounded hover:bg-red-700"
                    >
                      Bloquear
                    </button>
                  </>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
