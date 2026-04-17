'use client';

export const dynamic = 'force-dynamic';

import { useState } from 'react';

type TabType = 'prodes' | 'embargo' | 'desmatamento' | 'consolidado';

interface FlaggedCar {
  id: string;
  car_code: string;
  flag_type: string;
  severity: string;
  cliente_nome: string;
  details_json: any;
}

export default function CARsProblematicosPage() {
  const [activeTab, setActiveTab] = useState<TabType>('consolidado');

  const renderTabContent = () => {
    switch (activeTab) {
      case 'consolidado':
        return <ConsolidadoTab />;
      case 'prodes':
        return <ProdesTab />;
      case 'embargo':
        return <EmbargoTab />;
      case 'desmatamento':
        return <DesmatamentoTab />;
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-800">CARs Problemáticos</h1>
        <p className="text-gray-600 mt-2">Monitore áreas com PRODES, embargo ou desmatamento detectado</p>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <div className="flex gap-6">
          <button
            onClick={() => setActiveTab('consolidado')}
            className={`px-4 py-3 font-semibold border-b-2 transition-colors ${
              activeTab === 'consolidado'
                ? 'border-green-600 text-green-600'
                : 'border-transparent text-gray-600 hover:text-gray-900'
            }`}
          >
            📊 Consolidado
          </button>
          <button
            onClick={() => setActiveTab('prodes')}
            className={`px-4 py-3 font-semibold border-b-2 transition-colors ${
              activeTab === 'prodes'
                ? 'border-green-600 text-green-600'
                : 'border-transparent text-gray-600 hover:text-gray-900'
            }`}
          >
            🟢 PRODES
          </button>
          <button
            onClick={() => setActiveTab('embargo')}
            className={`px-4 py-3 font-semibold border-b-2 transition-colors ${
              activeTab === 'embargo'
                ? 'border-green-600 text-green-600'
                : 'border-transparent text-gray-600 hover:text-gray-900'
            }`}
          >
            🟠 Embargo
          </button>
          <button
            onClick={() => setActiveTab('desmatamento')}
            className={`px-4 py-3 font-semibold border-b-2 transition-colors ${
              activeTab === 'desmatamento'
                ? 'border-green-600 text-green-600'
                : 'border-transparent text-gray-600 hover:text-gray-900'
            }`}
          >
            🔴 Desmatamento
          </button>
        </div>
      </div>

      {/* Content */}
      <div>{renderTabContent()}</div>
    </div>
  );
}

function ConsolidadoTab() {
  return (
    <div className="space-y-6">
      {/* Alert Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-red-50 rounded-lg p-4 border border-red-200">
          <p className="text-red-600 text-sm font-semibold">Total CARs com Problemas</p>
          <p className="text-3xl font-bold text-red-700 mt-2">1,847</p>
          <p className="text-xs text-red-600 mt-1">📈 +15 esta semana</p>
        </div>
        <div className="bg-green-50 rounded-lg p-4 border border-green-200">
          <p className="text-green-600 text-sm font-semibold">Com PRODES</p>
          <p className="text-3xl font-bold text-green-700 mt-2">1,204</p>
          <p className="text-xs text-green-600 mt-1">65% do total</p>
        </div>
        <div className="bg-orange-50 rounded-lg p-4 border border-orange-200">
          <p className="text-orange-600 text-sm font-semibold">Com Embargo</p>
          <p className="text-3xl font-bold text-orange-700 mt-2">387</p>
          <p className="text-xs text-orange-600 mt-1">21% do total</p>
        </div>
        <div className="bg-yellow-50 rounded-lg p-4 border border-yellow-200">
          <p className="text-yellow-600 text-sm font-semibold">Com Desmatamento</p>
          <p className="text-3xl font-bold text-yellow-700 mt-2">256</p>
          <p className="text-xs text-yellow-600 mt-1">14% do total</p>
        </div>
      </div>

      {/* Critical Alerts */}
      <div className="bg-white rounded-lg shadow-sm p-6 border border-red-200 bg-red-50">
        <h3 className="text-lg font-bold text-red-700 mb-4">⚠️ Alertas Críticos (Últimos 7 dias)</h3>
        <div className="space-y-3">
          <div className="flex justify-between items-center p-3 bg-white rounded border-l-4 border-l-red-600">
            <div>
              <p className="font-semibold text-gray-800">PA-1501451-110F7A95</p>
              <p className="text-sm text-gray-600">PRODES + Desmatamento | São Félix do Xingu</p>
            </div>
            <span className="px-3 py-1 bg-red-100 text-red-700 rounded text-xs font-semibold">CRÍTICO</span>
          </div>
          <div className="flex justify-between items-center p-3 bg-white rounded border-l-4 border-l-orange-600">
            <div>
              <p className="font-semibold text-gray-800">PA-1604800-12AB34CD</p>
              <p className="text-sm text-gray-600">Embargo SEMAS-PA | Altamira</p>
            </div>
            <span className="px-3 py-1 bg-orange-100 text-orange-700 rounded text-xs font-semibold">ALTO</span>
          </div>
          <div className="flex justify-between items-center p-3 bg-white rounded border-l-4 border-l-green-600">
            <div>
              <p className="font-semibold text-gray-800">PA-2123456-45EF67GH</p>
              <p className="text-sm text-gray-600">PRODES detectado hoje</p>
            </div>
            <span className="px-3 py-1 bg-green-100 text-green-700 rounded text-xs font-semibold">NOVO</span>
          </div>
        </div>
      </div>

      {/* Summary Table */}
      <div className="bg-white rounded-lg shadow-sm overflow-hidden border border-gray-200">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-6 py-3 text-left font-semibold text-gray-700">CAR</th>
              <th className="px-6 py-3 text-left font-semibold text-gray-700">Tipo</th>
              <th className="px-6 py-3 text-left font-semibold text-gray-700">Severidade</th>
              <th className="px-6 py-3 text-left font-semibold text-gray-700">Detectado em</th>
              <th className="px-6 py-3 text-left font-semibold text-gray-700">Ação</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            <tr className="hover:bg-gray-50">
              <td colSpan={5} className="px-6 py-8 text-center text-gray-500">
                Carregando dados...
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}

function ProdesTab() {
  return (
    <div className="space-y-4">
      <div className="bg-green-50 rounded-lg p-4 border border-green-200">
        <p className="text-green-700 font-semibold">Total com PRODES: <span className="text-2xl">1,204 CARs</span></p>
      </div>
      <div className="bg-white rounded-lg shadow-sm overflow-hidden border border-gray-200">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-6 py-3 text-left font-semibold text-gray-700">CAR</th>
              <th className="px-6 py-3 text-left font-semibold text-gray-700">Cliente</th>
              <th className="px-6 py-3 text-left font-semibold text-gray-700">Área PRODES (ha)</th>
              <th className="px-6 py-3 text-left font-semibold text-gray-700">% CAR</th>
              <th className="px-6 py-3 text-left font-semibold text-gray-700">Ano</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            <tr className="hover:bg-gray-50">
              <td colSpan={5} className="px-6 py-8 text-center text-gray-500">
                Nenhum dado disponível
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}

function EmbargoTab() {
  return (
    <div className="space-y-4">
      <div className="bg-orange-50 rounded-lg p-4 border border-orange-200">
        <p className="text-orange-700 font-semibold">Total com Embargo: <span className="text-2xl">387 CARs</span></p>
      </div>
      <div className="bg-white rounded-lg shadow-sm overflow-hidden border border-gray-200">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-6 py-3 text-left font-semibold text-gray-700">CAR</th>
              <th className="px-6 py-3 text-left font-semibold text-gray-700">Cliente</th>
              <th className="px-6 py-3 text-left font-semibold text-gray-700">Órgão</th>
              <th className="px-6 py-3 text-left font-semibold text-gray-700">Tipo</th>
              <th className="px-6 py-3 text-left font-semibold text-gray-700">Data</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            <tr className="hover:bg-gray-50">
              <td colSpan={5} className="px-6 py-8 text-center text-gray-500">
                Nenhum dado disponível
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}

function DesmatamentoTab() {
  return (
    <div className="space-y-4">
      <div className="bg-red-50 rounded-lg p-4 border border-red-200">
        <p className="text-red-700 font-semibold">Total com Desmatamento: <span className="text-2xl">256 CARs</span></p>
      </div>
      <div className="bg-white rounded-lg shadow-sm overflow-hidden border border-gray-200">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-6 py-3 text-left font-semibold text-gray-700">CAR</th>
              <th className="px-6 py-3 text-left font-semibold text-gray-700">Cliente</th>
              <th className="px-6 py-3 text-left font-semibold text-gray-700">Bioma</th>
              <th className="px-6 py-3 text-left font-semibold text-gray-700">Período</th>
              <th className="px-6 py-3 text-left font-semibold text-gray-700">Área (ha)</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            <tr className="hover:bg-gray-50">
              <td colSpan={5} className="px-6 py-8 text-center text-gray-500">
                Nenhum dado disponível
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
