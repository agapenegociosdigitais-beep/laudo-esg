'use client';

export const dynamic = 'force-dynamic';

import { useState } from 'react';

export default function RelatoriosPage() {
  const [section, setSection] = useState<'dashboard' | 'clientes' | 'pesquisas' | 'cars'>('dashboard');
  const [period, setPeriod] = useState<'week' | 'month' | 'quarter' | 'year'>('month');
  const [format, setFormat] = useState<'pdf' | 'xlsx'>('pdf');
  const [loading, setLoading] = useState(false);

  const handleExport = async () => {
    setLoading(true);
    // TODO: Conectar ao endpoint de exportação
    setTimeout(() => setLoading(false), 1500);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-800">Relatórios e Exportações</h1>
        <p className="text-gray-600 mt-2">Gere e exporte dados do painel em PDF ou Excel</p>
      </div>

      {/* Export Options */}
      <div className="bg-white rounded-lg shadow-sm p-8 border border-gray-200">
        <h2 className="text-xl font-bold text-gray-800 mb-6">Gerar Relatório</h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Section Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">Seção</label>
            <div className="space-y-2">
              {[
                { value: 'dashboard' as const, label: '📊 Dashboard (Métricas)' },
                { value: 'clientes' as const, label: '👥 Clientes' },
                { value: 'pesquisas' as const, label: '🔍 Pesquisas' },
                { value: 'cars' as const, label: '⚠️ CARs Problemáticos' },
              ].map((option) => (
                <label key={option.value} className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="radio"
                    name="section"
                    value={option.value}
                    checked={section === option.value}
                    onChange={(e) => setSection(e.target.value as any)}
                    className="w-4 h-4 cursor-pointer"
                  />
                  <span className="text-gray-700">{option.label}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Period Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-3">Período</label>
            <div className="space-y-2">
              {[
                { value: 'week' as const, label: '📅 Última Semana' },
                { value: 'month' as const, label: '📅 Último Mês' },
                { value: 'quarter' as const, label: '📅 Último Trimestre' },
                { value: 'year' as const, label: '📅 Último Ano' },
              ].map((option) => (
                <label key={option.value} className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="radio"
                    name="period"
                    value={option.value}
                    checked={period === option.value}
                    onChange={(e) => setPeriod(e.target.value as any)}
                    className="w-4 h-4 cursor-pointer"
                  />
                  <span className="text-gray-700">{option.label}</span>
                </label>
              ))}
            </div>
          </div>
        </div>

        <div className="mt-6 pt-6 border-t border-gray-200">
          <label className="block text-sm font-medium text-gray-700 mb-3">Formato</label>
          <div className="flex gap-4">
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="radio"
                name="format"
                value="pdf"
                checked={format === 'pdf'}
                onChange={(e) => setFormat(e.target.value as any)}
                className="w-4 h-4 cursor-pointer"
              />
              <span className="text-gray-700">📄 PDF (Imprimível)</span>
            </label>
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="radio"
                name="format"
                value="xlsx"
                checked={format === 'xlsx'}
                onChange={(e) => setFormat(e.target.value as any)}
                className="w-4 h-4 cursor-pointer"
              />
              <span className="text-gray-700">📊 Excel (Editável)</span>
            </label>
          </div>
        </div>

        <button
          onClick={handleExport}
          disabled={loading}
          className="mt-6 px-6 py-3 bg-green-600 text-white font-semibold rounded-lg hover:bg-green-700 disabled:opacity-50"
        >
          {loading ? 'Gerando...' : `Gerar Relatório em ${format.toUpperCase()}`}
        </button>
      </div>

      {/* Recent Exports */}
      <div className="bg-white rounded-lg shadow-sm p-8 border border-gray-200">
        <h2 className="text-xl font-bold text-gray-800 mb-6">Exportações Recentes</h2>
        <div className="text-center py-8 text-gray-500">
          <p>Nenhuma exportação realizada ainda</p>
        </div>
      </div>
    </div>
  );
}
