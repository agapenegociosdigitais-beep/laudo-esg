'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAdminAuth } from '@/contexts/AdminAuthContext';

export function AdminHeader() {
  const router = useRouter();
  const { logout } = useAdminAuth();
  const [open, setOpen] = useState(false);

  const handleLogout = () => {
    logout();
    router.push('/admin/login');
  };

  return (
    <header className="fixed top-0 right-0 left-64 h-16 bg-white border-b border-gray-200 flex items-center justify-between px-8 z-40">
      <div>
        <h2 className="text-sm text-gray-600">Painel Administrativo</h2>
      </div>

      <div className="flex items-center gap-6">
        {/* Notificações */}
        <button className="relative p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition">
          🔔
          <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
        </button>

        {/* User Dropdown */}
        <div className="relative">
          <button
            onClick={() => setOpen(!open)}
            className="flex items-center gap-2 px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition"
          >
            <span>👤</span>
            <span className="text-sm">Admin</span>
            <span className="text-xs">▼</span>
          </button>

          {open && (
            <div className="absolute right-0 mt-2 w-48 bg-white border border-gray-200 rounded-lg shadow-lg">
              <button
                onClick={handleLogout}
                className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50"
              >
                Fazer logout
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
