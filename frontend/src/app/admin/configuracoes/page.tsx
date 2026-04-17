'use client';

export const dynamic = 'force-dynamic';

import { useState } from 'react';
import { adminService } from '@/services/adminService';
import { useAdminAuth } from '@/contexts/AdminAuthContext';

export default function ConfiguracoesPage() {
  const { logout } = useAdminAuth();
  const [senhaAtual, setSenhaAtual] = useState('');
  const [senhaNova, setSenhaNova] = useState('');
  const [senhaConfirm, setSenhaConfirm] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [systemInfo, setSystemInfo] = useState<any>(null);

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (senhaNova !== senhaConfirm) {
      setError('As senhas não coincidem');
      return;
    }

    if (senhaNova.length < 8) {
      setError('A nova senha deve ter pelo menos 8 caracteres');
      return;
    }

    setLoading(true);
    try {
      await adminService.alterarSenha(senhaAtual, senhaNova);
      setSuccess('Senha alterada com sucesso! Faça login novamente.');
      setSenhaAtual('');
      setSenhaNova('');
      setSenhaConfirm('');
      setTimeout(() => {
        logout();
      }, 2000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Erro ao alterar senha');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-800">Configurações</h1>
        <p className="text-gray-600 mt-2">Gerencie suas credenciais e preferências do painel</p>
      </div>

      {/* Password Section */}
      <div className="bg-white rounded-lg shadow-sm p-8 border border-gray-200">
        <h2 className="text-xl font-bold text-gray-800 mb-6">Alterar Senha</h2>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
            {error}
          </div>
        )}

        {success && (
          <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm">
            {success}
          </div>
        )}

        <form onSubmit={handleChangePassword} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Senha Atual</label>
            <input
              type="password"
              value={senhaAtual}
              onChange={(e) => setSenhaAtual(e.target.value)}
              required
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 outline-none"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Nova Senha</label>
            <input
              type="password"
              value={senhaNova}
              onChange={(e) => setSenhaNova(e.target.value)}
              required
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 outline-none"
            />
            <p className="text-xs text-gray-500 mt-1">Mínimo 8 caracteres</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Confirmar Nova Senha</label>
            <input
              type="password"
              value={senhaConfirm}
              onChange={(e) => setSenhaConfirm(e.target.value)}
              required
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 outline-none"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="px-6 py-2 bg-green-600 text-white font-semibold rounded-lg hover:bg-green-700 disabled:opacity-50"
          >
            {loading ? 'Alterando...' : 'Alterar Senha'}
          </button>
        </form>
      </div>

      {/* Info Section */}
      <div className="bg-white rounded-lg shadow-sm p-8 border border-gray-200">
        <h2 className="text-xl font-bold text-gray-800 mb-6">Informações do Sistema</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
            <p className="text-sm text-gray-600 font-medium">Versão do Painel</p>
            <p className="text-lg font-bold text-gray-800 mt-1">1.0.0</p>
          </div>
          <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
            <p className="text-sm text-gray-600 font-medium">API Backend</p>
            <p className="text-lg font-bold text-gray-800 mt-1">v1 (FastAPI)</p>
          </div>
          <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
            <p className="text-sm text-gray-600 font-medium">Banco de Dados</p>
            <p className="text-lg font-bold text-gray-800 mt-1">PostgreSQL 15+</p>
          </div>
          <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
            <p className="text-sm text-gray-600 font-medium">Status</p>
            <p className="text-lg font-bold text-green-700 mt-1">✅ Operacional</p>
          </div>
        </div>
      </div>

      {/* Danger Zone */}
      <div className="bg-red-50 rounded-lg shadow-sm p-8 border border-red-200">
        <h2 className="text-xl font-bold text-red-700 mb-6">🔒 Zona de Risco</h2>
        <div className="space-y-4">
          <p className="text-gray-700">
            As ações nesta seção não podem ser desfeitas. Tenha cuidado.
          </p>
          <button
            onClick={() => {
              if (confirm('Tem certeza que deseja fazer logout?')) {
                logout();
              }
            }}
            className="px-6 py-2 bg-red-600 text-white font-semibold rounded-lg hover:bg-red-700"
          >
            Fazer Logout
          </button>
        </div>
      </div>
    </div>
  );
}
