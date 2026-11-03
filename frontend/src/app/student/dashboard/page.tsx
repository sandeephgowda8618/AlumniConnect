'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import Sidebar from '@/components/Sidebar';
import {
  Compass, Send, Calendar, Star, ArrowRight,
  Sparkles, CheckCircle, Clock
} from 'lucide-react';
import { api } from '@/lib/api';
import {
  StudentProfile, RecommendedMentor, MentorshipRequest,
  MentorAllocation, Booking, MentorshipSession
} from '@/types';

export default function StudentDashboard() {
  const router = useRouter();
  const [profile, setProfile] = useState<StudentProfile | null>(null);
  const [recommendations, setRecommendations] = useState<RecommendedMentor[]>([]);
  const [requests, setRequests] = useState<MentorshipRequest[]>([]);
  const [sessions, setSessions] = useState<MentorshipSession[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [prof, recs, reqs, sess] = await Promise.all([
          api.getStudentProfile(),
          api.discoverRecommendations(),
          api.getStudentRequests(),
          api.getStudentSessions()
        ]);
        setProfile(prof);
        setRecommendations(recs.results.slice(0, 3));
        setRequests(reqs.slice(0, 5));
        setSessions(sess.slice(0, 5));
      } catch (err: any) {
        console.error("Dashboard load failed", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  return (
    <div className="flex-1 flex">
      <Sidebar role="STUDENT" />

      <main className="flex-1 p-8 overflow-y-auto max-w-7xl">
        {/* Welcome Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between pb-6 border-b border-slate-200 gap-4">
          <div>
            <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
              Welcome back, {profile?.display_name || 'Student'}! 👋
            </h1>
            <p className="text-sm text-slate-500 mt-1">
              Targeting career goal: <span className="font-semibold text-slate-700">{profile?.career_goal || 'Software Engineering'}</span>
            </p>
          </div>
          <Link href="/student/mentors" className="btn-primary flex items-center space-x-2 text-sm">
            <Compass className="w-4 h-4" />
            <span>Discover Top Mentors</span>
          </Link>
        </div>

        {/* Quick Stats Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 my-8">
          <div className="card flex items-center space-x-4">
            <div className="w-12 h-12 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
              <Send className="w-6 h-6" />
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase">Requests Sent</p>
              <h3 className="text-2xl font-bold text-slate-900">{requests.length}</h3>
            </div>
          </div>

          <div className="card flex items-center space-x-4">
            <div className="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
              <Calendar className="w-6 h-6" />
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase">Sessions Conducted</p>
              <h3 className="text-2xl font-bold text-slate-900">
                {sessions.filter(s => s.session_status === 'COMPLETED').length}
              </h3>
            </div>
          </div>

          <div className="card flex items-center space-x-4">
            <div className="w-12 h-12 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center">
              <Sparkles className="w-6 h-6" />
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500 uppercase">Top Match Score</p>
              <h3 className="text-2xl font-bold text-purple-700">
                {recommendations[0]?.overall_score ? `${recommendations[0].overall_score}%` : 'N/A'}
              </h3>
            </div>
          </div>
        </div>

        {/* Two-Column Section: Top Matches & Recent Requests */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Recommended Mentors Preview */}
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-slate-900 flex items-center space-x-2">
                <Sparkles className="w-5 h-5 text-amber-500" />
                <span>Recommended For You</span>
              </h2>
              <Link href="/student/mentors" className="text-xs font-semibold text-emerald-600 hover:underline flex items-center space-x-1">
                <span>View all</span>
                <ArrowRight className="w-3 h-3" />
              </Link>
            </div>

            {loading ? (
              <p className="text-sm text-slate-400 py-4">Evaluating graph recommendation algorithm...</p>
            ) : recommendations.length === 0 ? (
              <p className="text-sm text-slate-500 py-4">No recommendations found yet. Update your skills profile.</p>
            ) : (
              <div className="space-y-4">
                {recommendations.map(mentor => (
                  <div key={mentor.mentor_user_id} className="p-4 rounded-xl border border-slate-100 bg-slate-50/50 hover:bg-slate-50 transition flex items-start justify-between">
                    <div>
                      <div className="flex items-center space-x-2">
                        <h4 className="font-bold text-slate-900 text-sm">{mentor.full_name}</h4>
                        <span className="badge bg-emerald-100 text-emerald-800 text-[10px]">
                          {mentor.overall_score}% Match
                        </span>
                      </div>
                      <p className="text-xs text-slate-600 mt-0.5">
                        {mentor.job_title} {mentor.company_name ? `at ${mentor.company_name}` : ''}
                      </p>
                      <p className="text-[11px] text-slate-500 mt-2 line-clamp-1 italic">
                        "{mentor.explanation_text}"
                      </p>
                    </div>

                    <Link
                      href={`/student/mentors?target=${mentor.mentor_user_id}`}
                      className="btn-secondary text-xs py-1.5 px-3 shrink-0 ml-4"
                    >
                      Request
                    </Link>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Active Mentorship Requests */}
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-slate-900 flex items-center space-x-2">
                <Send className="w-5 h-5 text-blue-500" />
                <span>My Mentorship Requests</span>
              </h2>
              <Link href="/student/requests" className="text-xs font-semibold text-emerald-600 hover:underline flex items-center space-x-1">
                <span>View all</span>
                <ArrowRight className="w-3 h-3" />
              </Link>
            </div>

            {loading ? (
              <p className="text-sm text-slate-400 py-4">Loading requests...</p>
            ) : requests.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-sm text-slate-500">You haven't submitted any mentorship requests yet.</p>
                <Link href="/student/mentors" className="mt-3 inline-block text-xs font-semibold text-emerald-600 hover:underline">
                  Browse mentor directory
                </Link>
              </div>
            ) : (
              <div className="divide-y divide-slate-100">
                {requests.map(req => (
                  <div key={req.request_id} className="py-3 flex items-center justify-between">
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="text-sm font-semibold text-slate-800">
                          {req.mentor_name || `Mentor #${req.mentor_user_id}`}
                        </span>
                        <span className={`badge ${
                          req.request_status === 'ACCEPTED' ? 'badge-active' :
                          req.request_status === 'REJECTED' ? 'badge-rejected' : 'badge-pending'
                        }`}>
                          {req.request_status}
                        </span>
                      </div>
                      <p className="text-xs text-slate-500 mt-0.5 line-clamp-1">
                        Domain: {req.domain_name || 'General Guidance'}
                      </p>
                    </div>

                    <span className="text-[11px] text-slate-400">
                      {new Date(req.submitted_at).toLocaleDateString()}
                    </span>
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

