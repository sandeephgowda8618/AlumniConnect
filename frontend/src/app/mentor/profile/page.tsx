'use client';

import React, { useEffect, useState } from 'react';
import Sidebar from '@/components/Sidebar';
import { User, Save, CheckCircle2, Briefcase, Award, Star } from 'lucide-react';
import { api } from '@/lib/api';
import { MentorProfile } from '@/types';

export default function MentorProfilePage() {
  const [profile, setProfile] = useState<MentorProfile | null>(null);
  const [jobTitle, setJobTitle] = useState('');
  const [yearsExp, setYearsExp] = useState('');
  const [maxMentees, setMaxMentees] = useState(3);
  const [accepting, setAccepting] = useState(true);
  const [summary, setSummary] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    api.getMentorProfile()
      .then(p => {
        setProfile(p);
        setJobTitle(p.job_title);
        setYearsExp(String(p.years_experience));
        setMaxMentees(p.max_active_mentees);
        setAccepting(p.accepting_requests);
        setSummary(p.professional_summary || '');
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setMessage(null);
    try {
      const updated = await api.updateMentorProfile({
        job_title: jobTitle,
        years_experience: parseFloat(yearsExp),
        max_active_mentees: maxMentees,
        accepting_requests: accepting,
        professional_summary: summary
      });
      setProfile(updated);
      setMessage("Mentor profile & capacity settings updated successfully!");
    } catch (err: any) {
      setMessage(`Error: ${err.message}`);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="flex-1 flex">
      <Sidebar role="MENTOR" />

      <main className="flex-1 p-8 overflow-y-auto max-w-4xl">
        <div className="pb-6 border-b border-slate-200">
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight flex items-center space-x-2">
            <User className="w-6 h-6 text-emerald-600" />
            <span>Mentor Profile & Settings</span>
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Manage your professional credentials, mentee capacity limits, and availability.
          </p>
        </div>

        {message && (
          <div className="my-6 p-4 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center space-x-2 text-emerald-800 text-sm">
            <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
            <span>{message}</span>
          </div>
        )}

        {loading ? (
          <div className="py-20 text-center text-slate-400">Loading mentor profile...</div>
        ) : profile && (
          <form className="space-y-6 my-8" onSubmit={handleSave}>
            <div className="card space-y-4">
              <h2 className="text-base font-bold text-slate-900 flex items-center space-x-2">
                <Briefcase className="w-4 h-4 text-emerald-600" />
                <span>Professional Details</span>
              </h2>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-500 mb-1">Full Name</label>
                  <input
                    type="text"
                    disabled
                    value={profile.display_name}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-600"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Current Job Title</label>
                  <input
                    type="text"
                    value={jobTitle}
                    onChange={e => setJobTitle(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-emerald-500 outline-none"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-500 mb-1">Affiliated Company</label>
                  <input
                    type="text"
                    disabled
                    value={profile.company_name || 'Technology Enterprise'}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-600"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Years Experience</label>
                  <input
                    type="number"
                    step="0.5"
                    value={yearsExp}
                    onChange={e => setYearsExp(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-emerald-500 outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Professional Summary</label>
                <textarea
                  rows={3}
                  value={summary}
                  onChange={e => setSummary(e.target.value)}
                  placeholder="Outline your background, domain specializations, and mentorship focus..."
                  className="w-full p-3 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-emerald-500 outline-none"
                />
              </div>
            </div>

            {/* Capacity & Request Controls */}
            <div className="card space-y-4">
              <h2 className="text-base font-bold text-slate-900 flex items-center space-x-2">
                <Award className="w-4 h-4 text-purple-600" />
                <span>Mentee Capacity & Intake Settings</span>
              </h2>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Maximum Active Mentees (Quota)
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="10"
                    value={maxMentees}
                    onChange={e => setMaxMentees(parseInt(e.target.value))}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-emerald-500 outline-none"
                  />
                  <p className="text-[11px] text-slate-400 mt-1">
                    Currently mentoring {profile.active_mentees_count || 0} active students.
                  </p>
                </div>

                <div className="flex flex-col justify-center">
                  <label className="flex items-center space-x-3 cursor-pointer mt-4">
                    <input
                      type="checkbox"
                      checked={accepting}
                      onChange={e => setAccepting(e.target.checked)}
                      className="w-4 h-4 text-emerald-600 rounded border-slate-300 focus:ring-emerald-500"
                    />
                    <span className="text-xs font-semibold text-slate-700">
                      Currently Accepting New Mentorship Requests
                    </span>
                  </label>
                </div>
              </div>
            </div>

            <div className="flex justify-end">
              <button
                type="submit"
                disabled={saving}
                className="btn-primary flex items-center space-x-2 text-sm px-6"
              >
                <Save className="w-4 h-4" />
                <span>{saving ? 'Saving...' : 'Save Profile Changes'}</span>
              </button>
            </div>
          </form>
        )}
      </main>
    </div>
  );
}

