'use client';

export const dynamic = 'force-dynamic';

import { useState, useEffect } from 'react';
import { adminService } from '@/services/adminService';

interface SearchLog {
  id: string;
  car_code: string;
  municipio: string;
  area_hectares: number;
  searched_at: string;
  has_prodes: boolean;
  has_embargo_sema: boolean;
  has_deforestation: boolean;
  cliente_nome: string;
}

interface PaginatedResponse {
  items: SearchLog[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export default function PesquisasPage() {
  const [searches, setSearches] = useState<SearchLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [filterResult, setFilterResult] = useState('todos');
  const [search, setSearch] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');

  const getResultBadge = (hasProdes: boolean, hasEmbargo: boolean, hasDeforestation: boolean) => {
    if (hasProdes) return <span className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs font-semibold">✅ PRODES</span>;
    if (hasEmbargo) return <span className="px-2 py-1 bg-orange-100 text-orange-800 rounded text-xs font-semibold">⚠️ Embargo</span>;
    if (hasDeforestation) return <span className="px-2 py-1 bg-red-100 text-red-800 rounded text-xs font-semibold">🔴 Desmatamento</span>;
    return <span className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs font-semibold">✅ Limpo</span>;
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-800">Log de Pesquisas</h1>
        <p className="text-gray-600 mt-2">Histórico completo de todas as análises realizadas no sistema</p>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
        <div className="grid grid-cols-1 md:grid-cols-4 lg:grid-cols-5 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Buscar CAR/Cliente</label>
            <input
              type="text"
              placeholder="CAR ou cliente..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-green-500 outline-none"
            />
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
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Resultado</label>
            <select
              value={filterResult}
              onChange={(e) => setFilterResult(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-green-500 outline-none"
            >
              <option value="todos">Todos</option>
              <option value="limpo">Limpo</option>
              <option value="prodes">PRODES</option>
              <option value="embargo">Embargo</option>
              <option value="desmatamento">Desmatamento</option>
            </select>
          </div>
          <div className="flex items-end">
            <button className="w-full px-4 py-2 bg-green-600 text-white font-semibold rounded-lg hover:bg-green-700 text-sm">
              Buscar
            </button>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg shadow-sm overflow-hidden border border-gray-200">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-6 py-3 text-left font-semibold text-gray-700">CAR</th>
              <th className="px-6 py-3 text-left font-semibold text-gray-700">Cliente</th>
              <th className="px-6 py-3 text-left font-semibold text-gray-700">Município</th>
              <th className="px-6 py-3 text-left font-semibold text-gray-700">Área (ha)</th>
              <th className="px-6 py-3 text-left font-semibold text-gray-700">Data/Hora</th>
              <th className="px-6 py-3 text-left font-semibold text-gray-700">Resultado</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            <tr className="hover:bg-gray-50">
              <td colSpan={6} className="px-6 py-8 text-center text-gray-500">
                Nenhuma pesquisa encontrada ou endpoint não implementado
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex justify-center items-center gap-2">
        <button className="px-3 py-2 border border-gray-300 rounded-lg text-sm font-medium hover:bg-gray-50 disabled:opacity-50">
          ← Anterior
        </button>
        <button className="px-3 py-2 bg-green-600 text-white rounded-lg text-sm font-medium">
          1
        </button>
        <button className="px-3 py-2 border border-gray-300 rounded-lg text-sm font-medium hover:bg-gray-50 disabled:opacity-50">
          Próximo →
        </button>
      </div>
    </div>
  );
}
