'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import Sidebar from '@/components/Sidebar';
import { Send, Clock, CheckCircle2, XCircle, Calendar, ArrowRight } from 'lucide-react';
import { api } from '@/lib/api';
import { MentorshipRequest } from '@/types';

export default function StudentRequestsPage() {
  const [requests, setRequests] = useState<MentorshipRequest[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getStudentRequests()
      .then(setRequests)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="flex-1 flex">
      <Sidebar role="STUDENT" />

      <main className="flex-1 p-8 overflow-y-auto max-w-7xl">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between pb-6 border-b border-slate-200 gap-4">
          <div>
            <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight flex items-center space-x-2">
              <Send className="w-6 h-6 text-blue-600" />
              <span>Mentorship Requests</span>
            </h1>
            <p className="text-sm text-slate-500 mt-1">
              Track the status of your requests and connect with accepted mentors.
            </p>
          </div>
          <Link href="/student/mentors" className="btn-primary text-xs py-2 px-3">
            + New Request
          </Link>
        </div>

        {loading ? (
          <div className="py-20 text-center text-slate-400 text-sm">Loading your request history...</div>
        ) : requests.length === 0 ? (
          <div className="card text-center py-16 my-8">
            <Send className="w-10 h-10 mx-auto text-slate-300 mb-3" />
            <h3 className="text-base font-bold text-slate-800">No requests submitted yet</h3>
            <p className="text-xs text-slate-500 mt-1">Explore top recommended alumni mentors and send your first request.</p>
            <Link href="/student/mentors" className="btn-primary text-xs py-2 px-4 mt-4 inline-block">
              Browse Mentors
            </Link>
          </div>
        ) : (
          <div className="space-y-4 my-8">
            {requests.map(req => (
              <div key={req.request_id} className="card hover:border-slate-300 transition">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
                  <div className="flex items-center space-x-3">
                    <h3 className="text-base font-bold text-slate-900">
                      {req.mentor_name || `Mentor #${req.mentor_user_id}`}
                    </h3>
                    <span className={`badge ${
                      req.request_status === 'ACCEPTED' ? 'badge-active' :
                      req.request_status === 'REJECTED' ? 'badge-rejected' : 'badge-pending'
                    }`}>
                      {req.request_status === 'ACCEPTED' && <CheckCircle2 className="w-3 h-3 mr-1" />}
                      {req.request_status === 'REJECTED' && <XCircle className="w-3 h-3 mr-1" />}
                      {req.request_status === 'PENDING' && <Clock className="w-3 h-3 mr-1" />}
                      {req.request_status}
                    </span>
                  </div>

                  <span className="text-xs text-slate-400">
                    Submitted: {new Date(req.submitted_at).toLocaleDateString()}
                  </span>
                </div>

                <div className="py-3 text-xs text-slate-600">
                  <p className="font-semibold text-slate-700 mb-1">Domain: {req.domain_name || 'General Guidance'}</p>
                  <p className="bg-slate-50 p-3 rounded-lg border border-slate-100 italic">
                    "{req.request_message}"
                  </p>
                </div>

                {req.decision_at && (
                  <div className="mt-2 p-3 bg-slate-50 rounded-lg border border-slate-100 text-xs">
                    <p className="font-semibold text-slate-700">
                      Mentor Response ({new Date(req.decision_at).toLocaleDateString()}):
                    </p>
                    <p className="text-slate-600 mt-1">{req.decision_reason || 'No additional note provided.'}</p>
                  </div>
                )}

                {req.request_status === 'ACCEPTED' && (
                  <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between">
                    <span className="text-xs font-semibold text-emerald-700">
                      Active Allocation Created! You are eligible to book a 1-on-1 session.
                    </span>
                    <Link
                      href="/student/sessions"
                      className="btn-primary text-xs py-1.5 px-3 flex items-center space-x-1"
                    >
                      <Calendar className="w-3.5 h-3.5" />
                      <span>Book Session</span>
                    </Link>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}

