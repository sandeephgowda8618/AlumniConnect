'use client';

import React, { useEffect, useState } from 'react';
import Sidebar from '@/components/Sidebar';
import { CheckSquare, Clock, CheckCircle2, AlertCircle, X, Award, FileText } from 'lucide-react';
import { api } from '@/lib/api';
import { MentorshipSession, Skill } from '@/types';

export default function MentorSessionsPage() {
  const [sessions, setSessions] = useState<MentorshipSession[]>([]);
  const [skills, setSkills] = useState<Skill[]>([]);
  const [loading, setLoading] = useState(true);

  // Outcome recording modal
  const [targetSession, setTargetSession] = useState<MentorshipSession | null>(null);
  const [newStatus, setNewStatus] = useState<'COMPLETED' | 'NO_SHOW' | 'CANCELLED'>('COMPLETED');
  const [discussion, setDiscussion] = useState('');
  const [observations, setObservations] = useState('');
  const [improvement, setImprovement] = useState('');
  const [nextSteps, setNextSteps] = useState('');
  const [selectedSkillId, setSelectedSkillId] = useState<number>(1);
  const [skillResult, setSkillResult] = useState<string>('PROFICIENT');
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadSessions = async () => {
    setLoading(true);
    try {
      const [sess, sk] = await Promise.all([
        api.getMentorSessions(),
        api.getSkills()
      ]);
      setSessions(sess);
      setSkills(sk);
      if (sk.length > 0) setSelectedSkillId(sk[0].skill_id);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSessions();
  }, []);

  const handleOpenOutcomeModal = (session: MentorshipSession) => {
    setTargetSession(session);
    setNewStatus('COMPLETED');
    setDiscussion(session.discussion_summary || 'Discussed system architecture, distributed database trade-offs, and career roadmap.');
    setObservations(session.performance_observations || 'Student demonstrated strong fundamentals and analytical mindset.');
    setImprovement(session.improvement_areas || 'Recommended hands-on implementation of Redis caching strategies.');
    setNextSteps(session.next_steps || '1. Review ACID isolation levels. 2. Build mock API.');
    setError(null);
  };

  const handleRecordOutcome = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!targetSession) return;

    setSubmitting(true);
    setError(null);
    try {
      await api.recordSessionOutcome(targetSession.session_id, {
        new_status: newStatus,
        discussion_summary: discussion,
        performance_observations: observations,
        improvement_areas: improvement,
        next_steps: nextSteps,
        skill_assessments: [
          { skill_id: selectedSkillId, assessment_result: skillResult, assessment_notes: "Evaluated during offline technical mentorship." }
        ]
      });
      setMessage(`Outcome recorded for Session #${targetSession.session_id}! SP04 transaction completed.`);
      setTargetSession(null);
      loadSessions();
    } catch (err: any) {
      setError(err.message || 'Failed to record session outcome');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="flex-1 flex">
      <Sidebar role="MENTOR" />

      <main className="flex-1 p-8 overflow-y-auto max-w-7xl">
        <div className="pb-6 border-b border-slate-200">
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight flex items-center space-x-2">
            <CheckSquare className="w-6 h-6 text-emerald-600" />
            <span>Session Outcomes & Skill Evaluations</span>
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Conduct offline mentorship or mock interviews and record student evaluations (SP04).
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
          <div className="py-20 text-center text-slate-400 text-sm">Loading sessions...</div>
        ) : sessions.length === 0 ? (
          <div className="card text-center py-16 my-8">
            <Clock className="w-10 h-10 text-slate-300 mx-auto mb-3" />
            <h3 className="text-base font-bold text-slate-800">No Sessions Scheduled</h3>
            <p className="text-xs text-slate-500 mt-1">Once mentees reserve your published availability slots, they will appear here.</p>
          </div>
        ) : (
          <div className="space-y-4 my-8">
            {sessions.map(sess => (
              <div key={sess.session_id} className="card">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
                  <div>
                    <h3 className="text-base font-bold text-slate-900">
                      Mentee: {sess.student_name || 'Student Mentee'}
                    </h3>
                    {sess.slot_starts_at && (
                      <p className="text-xs text-slate-500 mt-0.5">
                        Scheduled: {new Date(sess.slot_starts_at).toLocaleString()}
                      </p>
                    )}
                  </div>

                  <div className="flex items-center space-x-3">
                    <span className={`badge ${
                      sess.session_status === 'COMPLETED' ? 'badge-completed' :
                      sess.session_status === 'SCHEDULED' ? 'badge-pending' : 'badge-rejected'
                    }`}>
                      {sess.session_status}
                    </span>

                    <button
                      onClick={() => handleOpenOutcomeModal(sess)}
                      className="btn-primary text-xs py-1.5 px-3 flex items-center space-x-1"
                    >
                      <FileText className="w-3.5 h-3.5" />
                      <span>{sess.session_status === 'COMPLETED' ? 'Update Evaluation' : 'Record Outcome'}</span>
                    </button>
                  </div>
                </div>

                {sess.discussion_summary && (
                  <div className="mt-3 bg-slate-50 p-3 rounded-lg border border-slate-100 text-xs space-y-1">
                    <p><span className="font-semibold text-slate-700">Summary:</span> {sess.discussion_summary}</p>
                    {sess.performance_observations && (
                      <p><span className="font-semibold text-slate-700">Observations:</span> {sess.performance_observations}</p>
                    )}
                    {sess.next_steps && (
                      <p><span className="font-semibold text-slate-700">Next Steps:</span> {sess.next_steps}</p>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Record Outcome Modal */}
        {targetSession && (
          <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 max-w-xl w-full p-6 max-h-[90vh] overflow-y-auto">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                <h3 className="text-base font-bold text-slate-900">
                  Record Mentorship Outcome (SP04)
                </h3>
                <button onClick={() => setTargetSession(null)} className="text-slate-400 hover:text-slate-600">
                  <X className="w-5 h-5" />
                </button>
              </div>

              <form className="mt-4 space-y-4" onSubmit={handleRecordOutcome}>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Session Outcome Status</label>
                  <select
                    value={newStatus}
                    onChange={e => setNewStatus(e.target.value as any)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs outline-none"
                  >
                    <option value="COMPLETED">COMPLETED (Session successfully held)</option>
                    <option value="NO_SHOW">NO_SHOW (Mentee did not attend)</option>
                    <option value="CANCELLED">CANCELLED (Session called off)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Discussion Summary</label>
                  <textarea
                    rows={3}
                    required
                    value={discussion}
                    onChange={e => setDiscussion(e.target.value)}
                    className="w-full p-2.5 border border-slate-300 rounded-lg text-xs outline-none focus:ring-2 focus:ring-emerald-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Performance Observations</label>
                  <textarea
                    rows={2}
                    value={observations}
                    onChange={e => setObservations(e.target.value)}
                    className="w-full p-2.5 border border-slate-300 rounded-lg text-xs outline-none focus:ring-2 focus:ring-emerald-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Areas for Improvement & Action Items</label>
                  <textarea
                    rows={2}
                    value={improvement}
                    onChange={e => setImprovement(e.target.value)}
                    className="w-full p-2.5 border border-slate-300 rounded-lg text-xs outline-none focus:ring-2 focus:ring-emerald-500"
                  />
                </div>

                <div className="pt-2 border-t border-slate-100">
                  <label className="block text-xs font-bold text-slate-800 uppercase tracking-wider mb-2">
                    Skill Rubric Assessment
                  </label>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-[11px] text-slate-500 mb-1">Assessed Skill</label>
                      <select
                        value={selectedSkillId}
                        onChange={e => setSelectedSkillId(Number(e.target.value))}
                        className="w-full px-3 py-1.5 border border-slate-300 rounded-lg text-xs"
                      >
                        {skills.map(s => (
                          <option key={s.skill_id} value={s.skill_id}>{s.skill_name}</option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label className="block text-[11px] text-slate-500 mb-1">Evaluation Result</label>
                      <select
                        value={skillResult}
                        onChange={e => setSkillResult(e.target.value)}
                        className="w-full px-3 py-1.5 border border-slate-300 rounded-lg text-xs"
                      >
                        <option value="PROFICIENT">PROFICIENT</option>
                        <option value="DEVELOPING">DEVELOPING</option>
                        <option value="NEEDS_IMPROVEMENT">NEEDS_IMPROVEMENT</option>
                        <option value="NOT_EVALUATED">NOT_EVALUATED</option>
                      </select>
                    </div>
                  </div>
                </div>

                <div className="flex justify-end space-x-3 pt-4 border-t border-slate-100">
                  <button
                    type="button"
                    onClick={() => setTargetSession(null)}
                    className="btn-secondary text-xs py-2 px-4"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submitting}
                    className="btn-primary text-xs py-2 px-4"
                  >
                    {submitting ? 'Recording SP04...' : 'Save Evaluation'}
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

