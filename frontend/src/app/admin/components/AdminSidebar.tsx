'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState } from 'react';

const MENU_ITEMS = [
  { label: 'Dashboard', icon: '📊', href: '/admin/dashboard' },
  { label: 'Clientes', icon: '👥', href: '/admin/clientes' },
  { label: 'Pesquisas', icon: '🔍', href: '/admin/pesquisas' },
  { label: 'CARs Problemáticos', icon: '⚠️', href: '/admin/cars-problematicos' },
  { label: 'Notificações', icon: '🔔', href: '/admin/notificacoes' },
  { label: 'Auditoria', icon: '📋', href: '/admin/auditoria' },
  { label: 'Relatórios', icon: '📄', href: '/admin/relatorios' },
  { label: 'Configurações', icon: '⚙️', href: '/admin/configuracoes' },
];

export function AdminSidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside className={`fixed left-0 top-0 h-screen bg-gray-900 text-white transition-all duration-300 ${collapsed ? 'w-20' : 'w-64'} border-r border-gray-800`}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-800">
        {!collapsed && <h1 className="text-xl font-bold">🌱 Eureka</h1>}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="p-2 hover:bg-gray-800 rounded-lg transition"
        >
          {collapsed ? '→' : '←'}
        </button>
      </div>

      {/* Menu */}
      <nav className="p-4 space-y-2">
        {MENU_ITEMS.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-4 py-2.5 rounded-lg transition ${
                isActive
                  ? 'bg-green-600 text-white font-semibold'
                  : 'text-gray-400 hover:bg-gray-800'
              }`}
              title={collapsed ? item.label : ''}
            >
              <span className="text-lg">{item.icon}</span>
              {!collapsed && <span>{item.label}</span>}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="absolute bottom-4 left-4 right-4">
        <div className={`px-4 py-2 bg-gray-800 rounded-lg text-sm ${collapsed ? 'text-center' : ''}`}>
          {!collapsed && <p className="text-gray-400 font-medium">Agape</p>}
          <p className="text-xs text-gray-500 truncate">super_admin</p>
        </div>
      </div>
    </aside>
  );
}
