'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import Sidebar from '@/components/Sidebar';
import {
  BarChart3, Users, Award, ShieldCheck, CheckCircle2,
  TrendingUp, Star, Database, ArrowRight
} from 'lucide-react';
import { api } from '@/lib/api';
import { PlatformOverviewStats } from '@/types';

export default function AdminDashboardPage() {
  const [stats, setStats] = useState<PlatformOverviewStats | null>(null);
  const [demandSupply, setDemandSupply] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [overview, ds] = await Promise.all([
          api.getPlatformOverview(),
          api.getDemandSupply()
        ]);
        setStats(overview);
        setDemandSupply(ds);
      } catch (err) {
        console.error("Admin dashboard error", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  return (
    <div className="flex-1 flex">
      <Sidebar role="ADMINISTRATOR" />

      <main className="flex-1 p-8 overflow-y-auto max-w-7xl">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between pb-6 border-b border-slate-200 gap-4">
          <div>
            <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight flex items-center space-x-2">
              <BarChart3 className="w-6 h-6 text-purple-600" />
              <span>Platform Administration & Analytics</span>
            </h1>
            <p className="text-sm text-slate-500 mt-1">
              Authoritative SQL query catalogue telemetry (Q01–Q32) and system health overview.
            </p>
          </div>

          <div className="flex items-center space-x-3">
            <Link href="/admin/funnel" className="btn-primary text-xs py-2 px-3 flex items-center space-x-1">
              <Award className="w-3.5 h-3.5" />
              <span>View Conversion Funnel (Q29)</span>
            </Link>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 my-8">
          <div className="card">
            <div className="flex items-center justify-between">
              <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">Total Users</p>
              <Users className="w-4 h-4 text-blue-500" />
            </div>
            <h3 className="text-3xl font-extrabold text-slate-900 mt-2">{stats?.total_users || 0}</h3>
            <p className="text-xs text-slate-500 mt-1">
              {stats?.active_students || 0} Students • {stats?.active_mentors || 0} Mentors
            </p>
          </div>

          <div className="card">
            <div className="flex items-center justify-between">
              <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">Active Allocations</p>
              <ShieldCheck className="w-4 h-4 text-emerald-500" />
            </div>
            <h3 className="text-3xl font-extrabold text-slate-900 mt-2">{stats?.active_allocations || 0}</h3>
            <p className="text-xs text-slate-500 mt-1">Ongoing 1-on-1 mentorship pairings</p>
          </div>

          <div className="card">
            <div className="flex items-center justify-between">
              <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">Completed Sessions</p>
              <CheckCircle2 className="w-4 h-4 text-purple-500" />
            </div>
            <h3 className="text-3xl font-extrabold text-slate-900 mt-2">{stats?.completed_sessions || 0}</h3>
            <p className="text-xs text-slate-500 mt-1">Recorded via SP04 stored procedure</p>
          </div>

          <div className="card">
            <div className="flex items-center justify-between">
              <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">Platform Rating</p>
              <Star className="w-4 h-4 text-amber-500 fill-current" />
            </div>
            <h3 className="text-3xl font-extrabold text-slate-900 mt-2">
              {stats?.average_mentor_rating ? stats.average_mentor_rating.toFixed(2) : '5.00'}
            </h3>
            <p className="text-xs text-slate-500 mt-1">{stats?.total_reviews || 0} Total Reviews (Q22)</p>
          </div>
        </div>

        {/* Skill Demand vs Supply Table (Q28) */}
        <div className="card my-8">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-lg font-bold text-slate-900 flex items-center space-x-2">
                <TrendingUp className="w-5 h-5 text-emerald-600" />
                <span>Skill Demand vs. Mentor Supply (Q28)</span>
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Calculated demand ratio identifying curriculum growth opportunities and mentor recruitment targets.
              </p>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-500 uppercase tracking-wider border-b border-slate-200">
                <tr>
                  <th className="py-3 px-4 font-bold">Skill / Specialization</th>
                  <th className="py-3 px-4 font-bold text-center">Student Demand</th>
                  <th className="py-3 px-4 font-bold text-center">Mentor Supply</th>
                  <th className="py-3 px-4 font-bold text-center">Demand Ratio</th>
                  <th className="py-3 px-4 font-bold text-right">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {demandSupply.map(item => (
                  <tr key={item.domain_id} className="hover:bg-slate-50">
                    <td className="py-3 px-4 font-bold text-slate-800">{item.domain_name}</td>
                    <td className="py-3 px-4 text-center font-semibold text-blue-600">{item.student_interest_count}</td>
                    <td className="py-3 px-4 text-center font-semibold text-emerald-600">{item.mentor_supply_count}</td>
                    <td className="py-3 px-4 text-center font-bold text-slate-800">{item.ratio}x</td>
                    <td className="py-3 px-4 text-right">
                      <span className={`badge ${
                        item.ratio > 1.5 ? 'bg-rose-100 text-rose-800' :
                        item.ratio < 0.8 ? 'bg-blue-100 text-blue-800' : 'badge-active'
                      }`}>
                        {item.ratio > 1.5 ? 'High Demand' : item.ratio < 0.8 ? 'Surplus' : 'Balanced'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </div>
  );
}

