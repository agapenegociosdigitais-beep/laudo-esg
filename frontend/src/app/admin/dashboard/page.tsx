'use client';

export const dynamic = 'force-dynamic';

import { useEffect, useState } from 'react';
import { adminService } from '@/services/adminService';

export default function DashboardPage() {
  const [metrics, setMetrics] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadMetrics = async () => {
      try {
        const data = await adminService.getMetricasOverview();
        setMetrics(data);
      } catch (error) {
        console.error('Erro ao carregar métricas:', error);
      } finally {
        setLoading(false);
      }
    };

    loadMetrics();
  }, []);

  if (loading) return <div className="text-center py-10">Carregando...</div>;
  if (!metrics) return <div className="text-center py-10 text-red-600">Erro ao carregar métricas</div>;

  return (
    <div className="space-y-8">
      <h1 className="text-3xl font-bold text-gray-800">Dashboard</h1>

      {/* Cards de Métricas */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow-sm p-6 border-l-4 border-green-500">
          <p className="text-gray-600 text-sm font-medium">Total de Clientes</p>
          <p className="text-3xl font-bold text-gray-800 mt-2">{metrics.total_clientes}</p>
          <p className="text-gray-500 text-xs mt-1">{metrics.clientes_ativos} ativos</p>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6 border-l-4 border-blue-500">
          <p className="text-gray-600 text-sm font-medium">Pesquisas (Mês)</p>
          <p className="text-3xl font-bold text-gray-800 mt-2">{metrics.total_pesquisas_mes}</p>
          <p className="text-gray-500 text-xs mt-1">{metrics.total_pesquisas_hoje} hoje</p>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6 border-l-4 border-purple-500">
          <p className="text-gray-600 text-sm font-medium">CARs Únicos</p>
          <p className="text-3xl font-bold text-gray-800 mt-2">{metrics.total_cars_unicos}</p>
          <p className="text-gray-500 text-xs mt-1">consultados</p>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6 border-l-4 border-red-500">
          <p className="text-gray-600 text-sm font-medium">com Problemas</p>
          <p className="text-3xl font-bold text-gray-800 mt-2">{metrics.total_cars_com_problemas}</p>
          <p className="text-gray-500 text-xs mt-1">detectados</p>
        </div>
      </div>

      {/* Seção de Info */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-xl font-bold text-gray-800 mb-4">Resumo das Análises</h2>
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center">
            <p className="text-2xl font-bold text-green-600">{metrics.cars_com_prodes}</p>
            <p className="text-sm text-gray-600">CARs com PRODES</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-orange-600">{metrics.cars_com_embargo}</p>
            <p className="text-sm text-gray-600">CARs com Embargo</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-yellow-600">{metrics.cars_com_desmatamento}</p>
            <p className="text-sm text-gray-600">CARs com Desmatamento</p>
          </div>
        </div>
      </div>
    </div>
  );
}
