'use client';

export const dynamic = 'force-dynamic';

import { useState, useEffect } from 'react';
import { adminService } from '@/services/adminService';

interface Notification {
  id: string;
  type: string;
  title: string;
  message: string;
  is_read: boolean;
  created_at: string;
  related_car?: string;
}

export default function NotificacoesPage() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);

  const getTypeIcon = (type: string) => {
    const icons: { [key: string]: string } = {
      new_client: '👤',
      prodes_alert: '🟢',
      embargo_alert: '🟠',
      deforest_alert: '🔴',
      limit_warning: '⚠️',
      limit_reached: '❌',
    };
    return icons[type] || '📬';
  };

  const getTypeBadge = (type: string) => {
    const config: { [key: string]: { bg: string; text: string; label: string } } = {
      new_client: { bg: 'bg-blue-100', text: 'text-blue-800', label: 'Cliente Novo' },
      prodes_alert: { bg: 'bg-green-100', text: 'text-green-800', label: 'Alerta PRODES' },
      embargo_alert: { bg: 'bg-orange-100', text: 'text-orange-800', label: 'Alerta Embargo' },
      deforest_alert: { bg: 'bg-red-100', text: 'text-red-800', label: 'Alerta Desmatamento' },
      limit_warning: { bg: 'bg-yellow-100', text: 'text-yellow-800', label: 'Aviso Limite' },
      limit_reached: { bg: 'bg-red-100', text: 'text-red-800', label: 'Limite Atingido' },
    };
    const cfg = config[type] || config['new_client'];
    return <span className={`px-2 py-1 rounded text-xs font-semibold ${cfg.bg} ${cfg.text}`}>{cfg.label}</span>;
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-800">Notificações</h1>
        <p className="text-gray-600 mt-2">Histórico de alertas e eventos do sistema</p>
      </div>

      {/* Empty State */}
      <div className="bg-white rounded-lg shadow-sm p-12 border border-gray-200 text-center">
        <p className="text-gray-500 text-lg">📬 Nenhuma notificação ainda</p>
        <p className="text-gray-400 text-sm mt-2">As notificações aparecerão aqui quando eventos forem disparados</p>
      </div>

      {/* Mock List (quando implementado) */}
      <div className="space-y-4 hidden">
        {[1, 2, 3].map((i) => (
          <div key={i} className="bg-white rounded-lg shadow-sm p-4 border border-gray-200 hover:shadow-md transition-shadow flex justify-between items-start">
            <div className="flex gap-4 flex-1">
              <span className="text-2xl">{getTypeIcon('prodes_alert')}</span>
              <div className="flex-1">
                <h3 className="font-semibold text-gray-800">PRODES Detectado em PA-150...</h3>
                <p className="text-sm text-gray-600 mt-1">Desmatamento detectado em propriedade rural</p>
                <p className="text-xs text-gray-500 mt-2">Há 2 horas</p>
              </div>
            </div>
            <span className="text-right">{getTypeBadge('prodes_alert')}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
