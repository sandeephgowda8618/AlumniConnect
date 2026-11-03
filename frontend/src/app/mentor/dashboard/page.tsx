'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import Sidebar from '@/components/Sidebar';
import {
  Send, Calendar, Star, Users, CheckCircle2,
  Clock, ArrowRight, ShieldCheck, Award
} from 'lucide-react';
import { api } from '@/lib/api';
import { MentorProfile, MentorshipRequest, MentorshipSession } from '@/types';

export default function MentorDashboard() {
  const [profile, setProfile] = useState<MentorProfile | null>(null);
  const [inbox, setInbox] = useState<MentorshipRequest[]>([]);
  const [sessions, setSessions] = useState<MentorshipSession[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [prof, reqs, sess] = await Promise.all([
          api.getMentorProfile(),
          api.getMentorInbox(),
          api.getMentorSessions()
        ]);
        setProfile(prof);
        setInbox(reqs);
        setSessions(sess);
      } catch (err) {
        console.error("Mentor dashboard load error", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  return (
    <div className="flex-1 flex">
      <Sidebar role="MENTOR" />

      <main className="flex-1 p-8 overflow-y-auto max-w-7xl">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between pb-6 border-b border-slate-200 gap-4">
          <div>
            <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
              Mentor Portal — {profile?.display_name || 'Alumni Mentor'}
            </h1>
            <p className="text-sm text-slate-500 mt-1">
              {profile?.job_title} {profile?.company_name ? `@ ${profile.company_name}` : ''} • {profile?.years_experience} Years Experience
            </p>
          </div>

          <div className="flex items-center space-x-3">
            <Link href="/mentor/availability" className="btn-primary text-xs py-2 px-3 flex items-center space-x-1">
              <Calendar className="w-3.5 h-3.5" />
              <span>Publish Availability</span>
            </Link>
          </div>
        </div>

        {/* Quick Stats Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-6 my-8">
          <div className="card flex items-center space-x-4">
            <div className="w-12 h-12 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center">
              <Send className="w-6 h-6" />
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase">Pending Requests</p>
              <h3 className="text-2xl font-bold text-slate-900">{inbox.length}</h3>
            </div>
          </div>

          <div className="card flex items-center space-x-4">
            <div className="w-12 h-12 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
              <Users className="w-6 h-6" />
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase">Active Mentees</p>
              <h3 className="text-2xl font-bold text-slate-900">
                {profile?.active_mentees_count || 0} / {profile?.max_active_mentees || 3}
              </h3>
            </div>
          </div>

          <div className="card flex items-center space-x-4">
            <div className="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase">Sessions Done</p>
              <h3 className="text-2xl font-bold text-slate-900">
                {sessions.filter(s => s.session_status === 'COMPLETED').length}
              </h3>
            </div>
          </div>

          <div className="card flex items-center space-x-4">
            <div className="w-12 h-12 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center">
              <Star className="w-6 h-6 fill-current" />
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase">Average Rating</p>
              <h3 className="text-2xl font-bold text-slate-900">
                {profile?.average_rating ? profile.average_rating.toFixed(1) : '5.0'}
              </h3>
            </div>
          </div>
        </div>

        {/* Pending Requests & Upcoming Sessions */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Inbox Preview */}
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-slate-900 flex items-center space-x-2">
                <Send className="w-5 h-5 text-amber-500" />
                <span>Pending Mentee Requests</span>
              </h2>
              <Link href="/mentor/requests" className="text-xs font-semibold text-emerald-600 hover:underline flex items-center space-x-1">
                <span>Go to Inbox</span>
                <ArrowRight className="w-3 h-3" />
              </Link>
            </div>

            {loading ? (
              <p className="text-xs text-slate-400 py-4">Checking incoming student requests...</p>
            ) : inbox.length === 0 ? (
              <div className="text-center py-8">
                <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
                <p className="text-xs text-slate-500 font-medium">Your request inbox is all caught up!</p>
              </div>
            ) : (
              <div className="divide-y divide-slate-100">
                {inbox.map(req => (
                  <div key={req.request_id} className="py-3 flex items-start justify-between">
                    <div>
                      <p className="text-sm font-bold text-slate-800">{req.student_name || 'Student Mentee'}</p>
                      <p className="text-xs text-slate-500 mt-0.5">Specialization: {req.domain_name || 'General'}</p>
                      <p className="text-xs text-slate-600 mt-1 italic line-clamp-1">"{req.request_message}"</p>
                    </div>

                    <Link
                      href="/mentor/requests"
                      className="btn-primary text-xs py-1 px-3 shrink-0 ml-4"
                    >
                      Review
                    </Link>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Conducted Sessions */}
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-slate-900 flex items-center space-x-2">
                <Calendar className="w-5 h-5 text-blue-500" />
                <span>Recent Mentorship Sessions</span>
              </h2>
              <Link href="/mentor/sessions" className="text-xs font-semibold text-emerald-600 hover:underline flex items-center space-x-1">
                <span>View all</span>
                <ArrowRight className="w-3 h-3" />
              </Link>
            </div>

            {loading ? (
              <p className="text-xs text-slate-400 py-4">Loading sessions...</p>
            ) : sessions.length === 0 ? (
              <div className="text-center py-8 text-xs text-slate-500">
                No sessions booked yet. Publish availability slots to start meeting mentees.
              </div>
            ) : (
              <div className="divide-y divide-slate-100">
                {sessions.slice(0, 5).map(sess => (
                  <div key={sess.session_id} className="py-3 flex items-center justify-between">
                    <div>
                      <p className="text-sm font-bold text-slate-800">{sess.student_name || 'Mentee'}</p>
                      <p className="text-xs text-slate-500">
                        Status: <span className="font-semibold text-slate-700">{sess.session_status}</span>
                      </p>
                    </div>

                    <Link
                      href="/mentor/sessions"
                      className="btn-secondary text-xs py-1 px-3"
                    >
                      Outcome
                    </Link>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

