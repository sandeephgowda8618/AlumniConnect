'use client';

import React, { useEffect, useState } from 'react';
import Sidebar from '@/components/Sidebar';
import { Send, CheckCircle2, XCircle, AlertCircle, Clock, X, Check } from 'lucide-react';
import { api } from '@/lib/api';
import { MentorshipRequest } from '@/types';

export default function MentorRequestsPage() {
  const [requests, setRequests] = useState<MentorshipRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<number | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Reject modal
  const [rejectingReq, setRejectingReq] = useState<MentorshipRequest | null>(null);
  const [rejectReason, setRejectReason] = useState('Mentorship capacity reached for this term.');

  const loadInbox = () => {
    setLoading(true);
    api.getMentorInbox()
      .then(setRequests)
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadInbox();
  }, []);

  const handleAccept = async (requestId: number) => {
    setActionLoading(requestId);
    setMessage(null);
    setError(null);
    try {
      const alloc = await api.acceptRequest(requestId);
      setMessage(`Request accepted! Stored procedure SP01 created Allocation #${alloc.allocation_id}.`);
      loadInbox();
    } catch (err: any) {
      setError(err.message || 'Failed to accept request');
    } finally {
      setActionLoading(null);
    }
  };

  const handleReject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!rejectingReq) return;

    setActionLoading(rejectingReq.request_id);
    setMessage(null);
    setError(null);
    try {
      await api.rejectRequest(rejectingReq.request_id, rejectReason);
      setMessage(`Mentorship request #${rejectingReq.request_id} declined.`);
      setRejectingReq(null);
      loadInbox();
    } catch (err: any) {
      setError(err.message || 'Failed to decline request');
    } finally {
      setActionLoading(null);
    }
  };

  return (
    <div className="flex-1 flex">
      <Sidebar role="MENTOR" />

      <main className="flex-1 p-8 overflow-y-auto max-w-7xl">
        <div className="pb-6 border-b border-slate-200">
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight flex items-center space-x-2">
            <Send className="w-6 h-6 text-amber-500" />
            <span>Mentee Request Inbox</span>
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Review incoming mentorship proposals from students and accept or decline based on availability.
          </p>
        </div>

        {message && (
          <div className="my-6 p-4 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center space-x-2 text-emerald-800 text-sm">
            <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
            <span>{message}</span>
          </div>
        )}

        {error && (
          <div className="my-6 p-4 bg-rose-50 border border-rose-200 rounded-xl flex items-center space-x-2 text-rose-800 text-sm">
            <AlertCircle className="w-5 h-5 text-rose-600 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {loading ? (
          <div className="py-20 text-center text-slate-400 text-sm">Loading mentee inbox...</div>
        ) : requests.length === 0 ? (
          <div className="card text-center py-16 my-8">
            <CheckCircle2 className="w-12 h-12 text-emerald-500 mx-auto mb-3" />
            <h3 className="text-base font-bold text-slate-800">No Pending Requests</h3>
            <p className="text-xs text-slate-500 mt-1">All incoming student requests have been addressed.</p>
          </div>
        ) : (
          <div className="space-y-4 my-8">
            {requests.map(req => (
              <div key={req.request_id} className="card">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
                  <div>
                    <h3 className="text-base font-bold text-slate-900">
                      {req.student_name || `Student Mentee #${req.student_user_id}`}
                    </h3>
                    <p className="text-xs text-slate-500">{req.student_programme || 'Student Mentee'}</p>
                  </div>
                  <span className="badge badge-pending">{req.request_status}</span>
                </div>

                <div className="py-3 text-xs space-y-2">
                  <p><span className="font-semibold text-slate-700">Specialization Domain:</span> {req.domain_name || 'General'}</p>
                  {req.career_goal_snapshot && (
                    <p><span className="font-semibold text-slate-700">Career Goal:</span> {req.career_goal_snapshot}</p>
                  )}
                  <div>
                    <p className="font-semibold text-slate-700 mb-1">Request Message:</p>
                    <p className="bg-slate-50 p-3 rounded-lg border border-slate-100 text-slate-600 italic">
                      "{req.request_message}"
                    </p>
                  </div>
                </div>

                <div className="pt-3 border-t border-slate-100 flex items-center justify-end space-x-3">
                  <button
                    onClick={() => setRejectingReq(req)}
                    disabled={actionLoading === req.request_id}
                    className="btn-secondary text-xs py-1.5 px-3 flex items-center space-x-1 text-rose-600 hover:bg-rose-50"
                  >
                    <XCircle className="w-3.5 h-3.5" />
                    <span>Decline</span>
                  </button>
                  <button
                    onClick={() => handleAccept(req.request_id)}
                    disabled={actionLoading === req.request_id}
                    className="btn-primary text-xs py-1.5 px-3 flex items-center space-x-1"
                  >
                    <Check className="w-3.5 h-3.5" />
                    <span>{actionLoading === req.request_id ? 'Accepting...' : 'Accept Mentee'}</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Reject Modal */}
        {rejectingReq && (
          <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 max-w-md w-full p-6">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                <h3 className="text-base font-bold text-slate-900">Decline Mentorship Request</h3>
                <button onClick={() => setRejectingReq(null)} className="text-slate-400 hover:text-slate-600">
                  <X className="w-5 h-5" />
                </button>
              </div>

              <form className="mt-4 space-y-4" onSubmit={handleReject}>
                <p className="text-xs text-slate-600">
                  Provide a brief reason to notify {rejectingReq.student_name}:
                </p>

                <textarea
                  rows={3}
                  required
                  value={rejectReason}
                  onChange={e => setRejectReason(e.target.value)}
                  className="w-full p-3 border border-slate-300 rounded-lg text-xs outline-none focus:ring-2 focus:ring-emerald-500"
                />

                <div className="flex justify-end space-x-3 pt-3">
                  <button
                    type="button"
                    onClick={() => setRejectingReq(null)}
                    className="btn-secondary text-xs py-2 px-4"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white font-medium rounded-lg text-xs transition"
                  >
                    Confirm Decline
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

