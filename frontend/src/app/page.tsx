'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  GraduationCap, Briefcase, BarChart3, Database,
  ArrowRight, ShieldCheck, Zap, GitFork, CheckCircle2
} from 'lucide-react';
import { api } from '@/lib/api';
import { User } from '@/types';

export default function HomePage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    const stored = api.getStoredUser();
    setUser(stored);
  }, []);

  const handleQuickLogin = async (email: string, role: string) => {
    try {
      const auth = await api.login(email, 'Password123!');
      if (role === 'STUDENT') router.push('/student/dashboard');
      else if (role === 'MENTOR') router.push('/mentor/dashboard');
      else router.push('/admin/dashboard');
    } catch (err: any) {
      alert(`Login failed: ${err.message}`);
    }
  };

  return (
    <div className="flex-1 flex flex-col justify-between">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-b from-white via-slate-50 to-emerald-50/30 pt-16 pb-20 border-b border-slate-200">
        <div className="max-w-6xl mx-auto px-6 text-center">
          <div className="inline-flex items-center space-x-2 px-3 py-1 bg-emerald-100 text-emerald-800 text-xs font-semibold rounded-full mb-6">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span>Production DBMS Mini-Project Architecture</span>
          </div>

          <h1 className="text-4xl md:text-6xl font-extrabold text-slate-900 tracking-tight leading-tight">
            Connecting Students with <br />
            <span className="text-emerald-600">Alumni Mentors</span> at Scale
          </h1>

          <p className="mt-5 text-lg text-slate-600 max-w-2xl mx-auto leading-relaxed">
            A high-performance DBMS platform featuring ACID transactions, graph-based mentor matching,
            Redis sub-millisecond caching, and automated transactional outbox notifications.
          </p>

          {/* Quick Demo Access Bar */}
          <div className="mt-10 p-6 bg-white rounded-2xl shadow-xl border border-slate-200 max-w-3xl mx-auto">
            <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider mb-4">
              Instant Demo Access (Seeded Accounts)
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <button
                onClick={() => handleQuickLogin('aarav.sharma@alumniconnect.edu', 'STUDENT')}
                className="flex items-center justify-center space-x-2 p-3 bg-blue-50 hover:bg-blue-100 text-blue-700 rounded-xl font-medium text-sm transition-all border border-blue-200"
              >
                <GraduationCap className="w-4 h-4" />
                <span>Student: Aarav Sharma</span>
              </button>

              <button
                onClick={() => handleQuickLogin('rohit.verma@alumniconnect.edu', 'MENTOR')}
                className="flex items-center justify-center space-x-2 p-3 bg-emerald-50 hover:bg-emerald-100 text-emerald-700 rounded-xl font-medium text-sm transition-all border border-emerald-200"
              >
                <Briefcase className="w-4 h-4" />
                <span>Mentor: Rohit Verma</span>
              </button>

              <button
                onClick={() => handleQuickLogin('admin@alumniconnect.edu', 'ADMIN')}
                className="flex items-center justify-center space-x-2 p-3 bg-purple-50 hover:bg-purple-100 text-purple-700 rounded-xl font-medium text-sm transition-all border border-purple-200"
              >
                <BarChart3 className="w-4 h-4" />
                <span>Admin Dashboard</span>
              </button>
            </div>
            <p className="text-[11px] text-slate-400 mt-3">
              Click any button above to instantly authenticate with seeded test credentials.
            </p>
          </div>
        </div>
      </section>

      {/* Architecture Highlights */}
      <section className="py-16 max-w-6xl mx-auto px-6">
        <h2 className="text-2xl font-bold text-slate-900 text-center mb-10">
          Polyglot Persistence & Architectural Pillars
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="card">
            <div className="w-10 h-10 rounded-lg bg-blue-100 text-blue-600 flex items-center justify-center mb-4">
              <Database className="w-5 h-5" />
            </div>
            <h3 className="text-lg font-bold text-slate-900 mb-2">MySQL 8.x (Authoritative)</h3>
            <p className="text-sm text-slate-600 leading-relaxed">
              25 normalized tables, InnoDB ACID transactions, stored procedures (SP01–SP05),
              triggers (TR01–TR04), views (V01–V04), and full query catalogue Q01–Q32.
            </p>
          </div>

          <div className="card">
            <div className="w-10 h-10 rounded-lg bg-rose-100 text-rose-600 flex items-center justify-center mb-4">
              <Zap className="w-5 h-5" />
            </div>
            <h3 className="text-lg font-bold text-slate-900 mb-2">Redis Caching & Limits</h3>
            <p className="text-sm text-slate-600 leading-relaxed">
              High-throughput cache-aside pattern (<code className="text-xs bg-slate-100 px-1 py-0.5 rounded">ac:v1:*</code>),
              token bucket rate limiting, booking idempotency guards, and TTL expiry.
            </p>
          </div>

          <div className="card">
            <div className="w-10 h-10 rounded-lg bg-emerald-100 text-emerald-600 flex items-center justify-center mb-4">
              <GitFork className="w-5 h-5" />
            </div>
            <h3 className="text-lg font-bold text-slate-900 mb-2">Neo4j Graph Traversals</h3>
            <p className="text-sm text-slate-600 leading-relaxed">
              Relationship-driven mentor candidate discovery, multi-hop alumni network queries,
              and 5-factor weighted scoring pipeline with Bayesian quality smoothing.
            </p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-slate-900 text-slate-400 py-8 text-center text-xs border-t border-slate-800">
        <p className="font-medium text-slate-300">AlumniConnect — DBMS Mini Project Specification Compliance</p>
        <p className="mt-1 text-slate-500">
          Strictly implemented against all 15 authoritative specification blueprints.
        </p>
      </footer>
    </div>
  );
}

