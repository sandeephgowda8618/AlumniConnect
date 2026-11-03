'use client';

import React, { useEffect, useState } from 'react';
import Sidebar from '@/components/Sidebar';
import { Users, AlertTriangle, CheckCircle2, ShieldCheck } from 'lucide-react';
import { api } from '@/lib/api';

export default function AdminCapacityPage() {
  const [capacityData, setCapacityData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getCapacityReport()
      .then(setCapacityData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="flex-1 flex">
      <Sidebar role="ADMINISTRATOR" />

      <main className="flex-1 p-8 overflow-y-auto max-w-7xl">
        <div className="pb-6 border-b border-slate-200">
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight flex items-center space-x-2">
            <Users className="w-6 h-6 text-purple-600" />
            <span>Mentor Capacity & Saturation (Query Q27)</span>
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Real-time monitoring of alumni mentor workload, active allocations, and quota saturation.
          </p>
        </div>

        {loading ? (
          <div className="py-20 text-center text-slate-400 text-sm">Evaluating mentor allocation capacity...</div>
        ) : (
          <div className="card my-8">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-slate-500 uppercase tracking-wider border-b border-slate-200">
                  <tr>
                    <th className="py-3 px-4 font-bold">Mentor Name</th>
                    <th className="py-3 px-4 font-bold text-center">Active Mentees</th>
                    <th className="py-3 px-4 font-bold text-center">Max Quota</th>
                    <th className="py-3 px-4 font-bold text-center">Utilization</th>
                    <th className="py-3 px-4 font-bold text-right">Capacity State</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {capacityData.map(m => (
                    <tr key={m.mentor_user_id} className="hover:bg-slate-50">
                      <td className="py-3 px-4 font-bold text-slate-900">{m.full_name}</td>
                      <td className="py-3 px-4 text-center font-bold text-blue-600">{m.current_active_mentees}</td>
                      <td className="py-3 px-4 text-center font-semibold text-slate-600">{m.max_active_mentees}</td>
                      <td className="py-3 px-4 text-center">
                        <div className="flex items-center justify-center space-x-2">
                          <div className="w-24 bg-slate-100 rounded-full h-2 overflow-hidden">
                            <div
                              className={`h-full ${m.utilization_percent >= 100 ? 'bg-rose-500' : 'bg-emerald-500'}`}
                              style={{ width: `${Math.min(100, m.utilization_percent)}%` }}
                            />
                          </div>
                          <span className="font-semibold text-slate-700">{m.utilization_percent}%</span>
                        </div>
                      </td>
                      <td className="py-3 px-4 text-right">
                        <span className={`badge ${
                          m.is_at_capacity ? 'bg-rose-100 text-rose-800 border-rose-200' : 'badge-active'
                        }`}>
                          {m.is_at_capacity ? 'Saturated' : 'Available'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

