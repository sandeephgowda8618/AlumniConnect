'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Bell, User as UserIcon, LogOut, CheckCircle, Clock } from 'lucide-react';
import { api } from '@/lib/api';
import { User, NotificationItem } from '@/types';

export default function Navbar() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [showNotifications, setShowNotifications] = useState(false);

  useEffect(() => {
    const storedUser = api.getStoredUser();
    setUser(storedUser);

    if (storedUser) {
      api.getNotifications()
        .then(setNotifications)
        .catch(err => console.error("Notification load error", err));
    }
  }, []);

  const handleLogout = () => {
    api.clearAuth();
    router.push('/login');
  };

  const markAsRead = async (id: number) => {
    try {
      await api.markNotificationRead(id);
      setNotifications(prev => prev.map(n => n.notification_id === id ? { ...n, is_read: true } : n));
    } catch (e) {
      console.error(e);
    }
  };

  const unreadCount = notifications.filter(n => !n.is_read).length;

  return (
    <header className="sticky top-0 z-40 bg-white border-b border-slate-200">
      <div className="flex items-center justify-between px-6 py-3">
        {/* Brand */}
        <div className="flex items-center space-x-3">
          <Link href="/" className="flex items-center space-x-2">
            <div className="w-9 h-9 rounded-lg bg-emerald-600 flex items-center justify-center text-white font-bold text-lg shadow-sm">
              AC
            </div>
            <div>
              <span className="text-lg font-bold text-slate-900 tracking-tight">AlumniConnect</span>
              <span className="hidden sm:inline-block ml-2 text-xs font-semibold px-2 py-0.5 bg-emerald-50 text-emerald-700 rounded-full border border-emerald-200">
                Official DBMS Platform
              </span>
            </div>
          </Link>
        </div>

        {/* User Navigation / Notifications */}
        {user ? (
          <div className="flex items-center space-x-4">
            {/* Notification Bell */}
            <div className="relative">
              <button
                onClick={() => setShowNotifications(!showNotifications)}
                className="relative p-2 text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded-full transition-colors"
                title="Notifications"
              >
                <Bell className="w-5 h-5" />
                {unreadCount > 0 && (
                  <span className="absolute top-1 right-1 w-4 h-4 bg-rose-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center">
                    {unreadCount}
                  </span>
                )}
              </button>

              {/* Notification Dropdown */}
              {showNotifications && (
                <div className="absolute right-0 mt-2 w-80 bg-white rounded-xl shadow-xl border border-slate-200 py-2 z-50">
                  <div className="px-4 py-2 border-b border-slate-100 flex items-center justify-between">
                    <span className="text-sm font-bold text-slate-800">Notifications</span>
                    <span className="text-xs text-slate-500">{unreadCount} unread</span>
                  </div>
                  <div className="max-h-72 overflow-y-auto divide-y divide-slate-100">
                    {notifications.length === 0 ? (
                      <p className="p-4 text-xs text-slate-500 text-center">No notifications yet.</p>
                    ) : (
                      notifications.map(n => (
                        <div
                          key={n.notification_id}
                          className={`p-3 text-xs cursor-pointer hover:bg-slate-50 transition-colors ${
                            !n.is_read ? 'bg-emerald-50/40 font-medium' : ''
                          }`}
                          onClick={() => markAsRead(n.notification_id)}
                        >
                          <div className="flex items-start justify-between">
                            <h4 className="text-slate-900">{n.title}</h4>
                            {!n.is_read && <span className="w-2 h-2 rounded-full bg-emerald-500 ml-2 mt-1"></span>}
                          </div>
                          <p className="text-slate-600 mt-1 line-clamp-2">{n.body_text}</p>
                          <span className="text-[10px] text-slate-400 mt-1 block">
                            {new Date(n.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </span>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* User Pill */}
            <div className="flex items-center space-x-3 pl-2 border-l border-slate-200">
              <div className="flex flex-col text-right">
                <span className="text-sm font-semibold text-slate-800">{user.display_name}</span>
                <span className="text-xs font-medium text-emerald-700 capitalize">{user.role.toLowerCase()}</span>
              </div>
              <button
                onClick={handleLogout}
                className="p-2 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
                title="Log out"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          </div>
        ) : (
          <div className="flex items-center space-x-3">
            <Link href="/login" className="text-sm font-medium text-slate-600 hover:text-slate-900">
              Sign In
            </Link>
            <Link href="/register" className="btn-primary text-sm py-1.5 px-3">
              Get Started
            </Link>
          </div>
        )}
      </div>
    </header>
  );
}

