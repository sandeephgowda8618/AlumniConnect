'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard, Compass, Send, Calendar, CheckSquare,
  User, BarChart3, Users, ShieldAlert, Award, FileText
} from 'lucide-react';
import { RoleCode } from '@/types';

interface SidebarProps {
  role: RoleCode;
}

export default function Sidebar({ role }: SidebarProps) {
  const pathname = usePathname();

  const studentLinks = [
    { label: 'Dashboard', href: '/student/dashboard', icon: LayoutDashboard },
    { label: 'Find Mentors', href: '/student/mentors', icon: Compass },
    { label: 'My Requests', href: '/student/requests', icon: Send },
    { label: 'My Sessions & Bookings', href: '/student/sessions', icon: Calendar },
    { label: 'Profile & Skills', href: '/student/profile', icon: User },
  ];

  const mentorLinks = [
    { label: 'Dashboard', href: '/mentor/dashboard', icon: LayoutDashboard },
    { label: 'Request Inbox', href: '/mentor/requests', icon: Send },
    { label: 'Availability Calendar', href: '/mentor/availability', icon: Calendar },
    { label: 'Session Evaluations', href: '/mentor/sessions', icon: CheckSquare },
    { label: 'Mentor Profile', href: '/mentor/profile', icon: User },
  ];

  const adminLinks = [
    { label: 'Platform Analytics', href: '/admin/dashboard', icon: BarChart3 },
    { label: 'Conversion Funnel', href: '/admin/funnel', icon: Award },
    { label: 'Capacity & Saturation', href: '/admin/capacity', icon: Users },
    { label: 'Audit Trail', href: '/admin/audit', icon: ShieldAlert },
  ];

  const links = role === 'ADMINISTRATOR' ? adminLinks : role === 'MENTOR' ? mentorLinks : studentLinks;

  return (
    <aside className="w-64 bg-slate-900 min-h-[calc(100vh-57px)] flex flex-col justify-between py-6 px-4">
      <div className="space-y-6">
        <div>
          <p className="px-3 text-[11px] font-bold text-slate-400 uppercase tracking-wider">
            {role} PORTAL
          </p>
          <nav className="mt-3 space-y-1">
            {links.map(link => {
              const Icon = link.icon;
              const isActive = pathname === link.href;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-emerald-600 text-white shadow-sm'
                      : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{link.label}</span>
                </Link>
              );
            })}
          </nav>
        </div>
      </div>

      <div className="px-3 py-2 bg-slate-800/60 rounded-xl border border-slate-700/60 text-xs text-slate-400">
        <div className="flex items-center space-x-2 text-slate-300 font-semibold mb-1">
          <FileText className="w-3.5 h-3.5 text-emerald-400" />
          <span>DBMS Mini-Project</span>
        </div>
        <p className="text-[11px] leading-relaxed">
          Polyglot persistence powered by MySQL 8.x, Redis & Neo4j.
        </p>
      </div>
    </aside>
  );
}

