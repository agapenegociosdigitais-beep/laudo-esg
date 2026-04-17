'use client';

export const dynamic = 'force-dynamic';

import { ClientesTable } from '../components/ClientesTable';

export default function ClientesPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-800">Clientes</h1>
        <p className="text-gray-600 mt-2">Gerencie aprovação, suspensão e limites de consultas dos clientes</p>
      </div>

      <ClientesTable />
    </div>
  );
}
