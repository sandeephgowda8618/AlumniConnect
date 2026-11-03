'use client';

import React, { useEffect, useState } from 'react';
import Sidebar from '@/components/Sidebar';
import { Award, ArrowDown, CheckCircle2, TrendingUp, Filter } from 'lucide-react';
import { api } from '@/lib/api';
import { FunnelReport } from '@/types';

export default function AdminFunnelPage() {
  const [funnel, setFunnel] = useState<FunnelReport | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getFunnelReport()
      .then(setFunnel)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="flex-1 flex">
      <Sidebar role="ADMINISTRATOR" />

      <main className="flex-1 p-8 overflow-y-auto max-w-7xl">
        <div className="pb-6 border-b border-slate-200">
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight flex items-center space-x-2">
            <Award className="w-6 h-6 text-purple-600" />
            <span>Platform Conversion Funnel (Query Q29)</span>
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            End-to-end lifecycle conversion tracked via SQL Common Table Expressions (CTEs):
            Request → Allocation → Booking → Session → Review.
          </p>
        </div>

        {loading ? (
          <div className="py-20 text-center text-slate-400 text-sm">Executing SQL CTE Funnel Aggregations...</div>
        ) : funnel && (
          <div className="my-8 space-y-8">
            {/* Visual Funnel Cards */}
            <div className="card space-y-6">
              <h2 className="text-base font-bold text-slate-900">Conversion Pipeline Analysis</h2>

              <div className="space-y-4">
                {funnel.steps.map((step, idx) => {
                  const widthPercent = Math.max(15, Math.min(100, step.conversion_rate_percent));
                  return (
                    <div key={step.step_name} className="space-y-1">
                      <div className="flex items-center justify-between text-xs font-semibold">
                        <span className="text-slate-800 flex items-center space-x-2">
                          <span className="w-5 h-5 rounded-full bg-slate-900 text-white flex items-center justify-center text-[10px]">
                            {idx + 1}
                          </span>
                          <span>{step.step_name}</span>
                        </span>
                        <div className="space-x-3">
                          <span className="text-slate-900 font-bold">{step.count} occurrences</span>
                          <span className="text-emerald-600 font-bold">({step.conversion_rate_percent.toFixed(1)}%)</span>
                        </div>
                      </div>

                      {/* Visual Progress Bar */}
                      <div className="w-full h-8 bg-slate-100 rounded-lg overflow-hidden flex items-center px-3">
                        <div
                          className="h-full bg-gradient-to-r from-emerald-500 to-teal-600 rounded-lg transition-all duration-500 flex items-center px-3 text-white font-bold text-xs shadow-sm"
                          style={{ width: `${widthPercent}%` }}
                        >
                          {step.count}
                        </div>
                      </div>

                      {idx < funnel.steps.length - 1 && (
                        <div className="flex justify-center py-1 text-slate-300">
                          <ArrowDown className="w-4 h-4" />
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Funnel Metrics Summary Table */}
            <div className="card">
              <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider mb-4">
                Funnel Telemetry Data (Q29)
              </h3>
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-4 text-center">
                <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
                  <p className="text-[11px] font-semibold text-slate-400 uppercase">Requests</p>
                  <p className="text-2xl font-bold text-slate-900 mt-1">{funnel.total_requests}</p>
                </div>
                <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
                  <p className="text-[11px] font-semibold text-slate-400 uppercase">Allocations</p>
                  <p className="text-2xl font-bold text-slate-900 mt-1">{funnel.accepted_requests}</p>
                </div>
                <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
                  <p className="text-[11px] font-semibold text-slate-400 uppercase">Bookings</p>
                  <p className="text-2xl font-bold text-slate-900 mt-1">{funnel.confirmed_bookings}</p>
                </div>
                <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
                  <p className="text-[11px] font-semibold text-slate-400 uppercase">Sessions</p>
                  <p className="text-2xl font-bold text-slate-900 mt-1">{funnel.completed_sessions}</p>
                </div>
                <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
                  <p className="text-[11px] font-semibold text-slate-400 uppercase">Reviews</p>
                  <p className="text-2xl font-bold text-slate-900 mt-1">{funnel.reviewed_sessions}</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

