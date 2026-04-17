'use client';

export const dynamic = 'force-dynamic';

import { useState } from 'react';

interface AuditLog {
  id: string;
  admin_id: string;
  action_type: string;
  target_type: string;
  target_id?: string;
  details: any;
  created_at: string;
}

export default function AuditoriaPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterAction, setFilterAction] = useState('todos');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');

  const getActionIcon = (action: string) => {
    const icons: { [key: string]: string } = {
      approve_client: '✅',
      disapprove_client: '🚫',
      suspend_client: '⏸️',
      edit_limit: '📝',
      reset_quota: '🔄',
      login: '🔐',
      logout: '🚪',
      export_report: '📊',
    };
    return icons[action] || '📋';
  };

  const getActionLabel = (action: string) => {
    const labels: { [key: string]: string } = {
      approve_client: 'Aprovou Cliente',
      disapprove_client: 'Bloqueou Cliente',
      suspend_client: 'Suspendeu Cliente',
      edit_limit: 'Editou Limite',
      reset_quota: 'Resetou Quota',
      login: 'Fez Login',
      logout: 'Fez Logout',
      export_report: 'Exportou Relatório',
    };
    return labels[action] || action;
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-800">Auditoria</h1>
        <p className="text-gray-600 mt-2">Log imutável de todas as ações do administrador</p>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Ação</label>
            <select
              value={filterAction}
              onChange={(e) => setFilterAction(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-green-500 outline-none"
            >
              <option value="todos">Todas as ações</option>
              <option value="approve_client">Aprovar Cliente</option>
              <option value="disapprove_client">Bloquear Cliente</option>
              <option value="suspend_client">Suspender Cliente</option>
              <option value="edit_limit">Editar Limite</option>
              <option value="login">Login</option>
              <option value="logout">Logout</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">De</label>
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-green-500 outline-none"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Até</label>
            <input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-green-500 outline-none"
            />
          </div>
          <div className="flex items-end">
            <button className="w-full px-4 py-2 bg-green-600 text-white font-semibold rounded-lg hover:bg-green-700 text-sm">
              Buscar
            </button>
          </div>
        </div>
      </div>

      {/* Empty State */}
      <div className="bg-white rounded-lg shadow-sm p-12 border border-gray-200 text-center">
        <p className="text-gray-500 text-lg">📋 Nenhum registro de auditoria</p>
        <p className="text-gray-400 text-sm mt-2">As ações do administrador aparecerão aqui</p>
      </div>

      {/* Mock Log (quando implementado) */}
      <div className="space-y-3 hidden">
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="bg-white rounded-lg shadow-sm p-4 border border-gray-200 flex justify-between items-start">
            <div className="flex gap-4 flex-1">
              <span className="text-2xl">{getActionIcon('approve_client')}</span>
              <div className="flex-1">
                <p className="font-semibold text-gray-800">{getActionLabel('approve_client')}</p>
                <p className="text-sm text-gray-600 mt-1">Cliente: João Silva (ID: 123abc...)</p>
                <p className="text-xs text-gray-500 mt-2">2026-04-14 14:30:22</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
