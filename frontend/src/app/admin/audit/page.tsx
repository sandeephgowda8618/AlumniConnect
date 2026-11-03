'use client';

import React, { useEffect, useState } from 'react';
import Sidebar from '@/components/Sidebar';
import { ShieldAlert, ShieldCheck, Clock, FileText, User } from 'lucide-react';
import { api } from '@/lib/api';

export default function AdminAuditPage() {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getAuditLogs()
      .then(setLogs)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="flex-1 flex">
      <Sidebar role="ADMINISTRATOR" />

      <main className="flex-1 p-8 overflow-y-auto max-w-7xl">
        <div className="pb-6 border-b border-slate-200">
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight flex items-center space-x-2">
            <ShieldAlert className="w-6 h-6 text-purple-600" />
            <span>Security & System Audit Log (Query Q30)</span>
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Authoritative immutable audit log of critical business events, state transitions, and security operations.
          </p>
        </div>

        {loading ? (
          <div className="py-20 text-center text-slate-400 text-sm">Querying audit_log relations...</div>
        ) : logs.length === 0 ? (
          <div className="card text-center py-16 my-8">
            <ShieldCheck className="w-12 h-12 text-emerald-500 mx-auto mb-3" />
            <p className="text-sm text-slate-500">Audit repository is currently initializing.</p>
          </div>
        ) : (
          <div className="card my-8">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 text-slate-500 uppercase tracking-wider border-b border-slate-200">
                  <tr>
                    <th className="py-3 px-4 font-bold">Timestamp</th>
                    <th className="py-3 px-4 font-bold">Action</th>
                    <th className="py-3 px-4 font-bold">Entity</th>
                    <th className="py-3 px-4 font-bold">Actor User</th>
                    <th className="py-3 px-4 font-bold">IP / Client</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {logs.map((log, idx) => (
                    <tr key={log.audit_id || log.log_id || idx} className="hover:bg-slate-50">
                      <td className="py-3 px-4 text-slate-400 font-mono text-[11px]">
                        {new Date(log.occurred_at).toLocaleString()}
                      </td>
                      <td className="py-3 px-4 font-bold text-slate-800">
                        <span className="badge bg-slate-100 text-slate-800 border border-slate-200">
                          {log.action}
                        </span>
                      </td>
                      <td className="py-3 px-4 font-semibold text-slate-600">
                        {log.entity_type} #{log.entity_id}
                      </td>
                      <td className="py-3 px-4 text-slate-700">
                        {log.actor_name ? `${log.actor_name} (#${log.actor_user_id})` : log.actor_user_id ? `User #${log.actor_user_id}` : 'System / Anonymous'}
                      </td>
                      <td className="py-3 px-4 font-mono text-slate-400 text-[11px]">
                        {log.ip_address || '127.0.0.1'}
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

