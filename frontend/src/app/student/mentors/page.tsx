'use client';

import React, { useEffect, useState, useRef } from 'react';
import Link from 'next/link';
import Sidebar from '@/components/Sidebar';
import {
  Compass, Star, Briefcase, Award, CheckCircle,
  Filter, Sparkles, Send, X, AlertCircle, LogIn
} from 'lucide-react';
import { api } from '@/lib/api';
import { RecommendedMentor, MentorshipDomain, StudentProfile } from '@/types';

export default function StudentMentorsPage() {
  const [mentors, setMentors] = useState<RecommendedMentor[]>([]);
  const [domains, setDomains] = useState<MentorshipDomain[]>([]);
  const [studentProfile, setStudentProfile] = useState<StudentProfile | null>(null);
  const [selectedDomain, setSelectedDomain] = useState<number | ''>('');
  const [loading, setLoading] = useState(true);
  const [authError, setAuthError] = useState(false);
  const isInitialMount = useRef(true);

  // Request Modal State
  const [targetMentor, setTargetMentor] = useState<RecommendedMentor | null>(null);
  const [requestMessage, setRequestMessage] = useState('');
  const [requestDomainId, setRequestDomainId] = useState<number>(1);
  const [submitting, setSubmitting] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const fetchMentors = async (domainId?: number | '') => {
    setLoading(true);
    setAuthError(false);
    try {
      const activeDomain = domainId !== undefined ? domainId : selectedDomain;
      const filters = activeDomain ? { domain_ids: [Number(activeDomain)] } : {};
      const res = await api.discoverRecommendations(filters);
      setMentors(res.results || []);
    } catch (err: any) {
      console.error("Discovery error:", err);
      if (err.message?.includes('401') || err.message?.includes('authenticated') || !api.getStoredUser()) {
        setAuthError(true);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Load domains, student profile and initial mentors on mount
    Promise.all([
      api.getDomains().catch(() => []),
      api.getStudentProfile().catch(() => null),
      fetchMentors('')
    ]).then(([doms, prof]) => {
      setDomains(doms);
      if (prof) setStudentProfile(prof);
      if (doms.length > 0) setRequestDomainId(doms[0].domain_id);
    });
  }, []);

  const handleDomainFilterChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value === '' ? '' : Number(e.target.value);
    setSelectedDomain(val);
  };

  useEffect(() => {
    if (isInitialMount.current) {
      isInitialMount.current = false;
      return;
    }
    fetchMentors(selectedDomain);
  }, [selectedDomain]);

  const handleDemoStudentLogin = async () => {
    try {
      setLoading(true);
      await api.login('aarav.sharma@alumniconnect.edu', 'Password123!');
      const prof = await api.getStudentProfile().catch(() => null);
      if (prof) setStudentProfile(prof);
      setAuthError(false);
      await fetchMentors(selectedDomain);
    } catch (e: any) {
      console.error("Demo login error:", e);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenRequestModal = (mentor: RecommendedMentor) => {
    setTargetMentor(mentor);
    setRequestMessage(`Hi ${mentor.full_name}, I would love your mentorship guidance on career progression and technical architectural practices.`);
    setErrorMsg(null);
    setSuccessMsg(null);
  };

  const handleSendRequest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!targetMentor) return;

    setSubmitting(true);
    setErrorMsg(null);
    try {
      await api.submitMentorshipRequest({
        mentor_user_id: targetMentor.mentor_user_id,
        domain_id: requestDomainId,
        request_message: requestMessage,
        career_goal_snapshot: 'Full Stack & Database Engineer'
      });
      setSuccessMsg(`Mentorship request successfully sent to ${targetMentor.full_name}!`);
      setTimeout(() => {
        setTargetMentor(null);
        setSuccessMsg(null);
      }, 2000);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to submit mentorship request');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="flex-1 flex">
      <Sidebar role="STUDENT" />

      <main className="flex-1 p-8 overflow-y-auto max-w-7xl">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between pb-6 border-b border-slate-200 gap-4">
          <div>
            <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight flex items-center space-x-2">
              <Compass className="w-6 h-6 text-emerald-600" />
              <span>Mentor Discovery</span>
            </h1>
            <p className="text-sm text-slate-500 mt-1">
              Traversing graph relationships and 5-factor scoring model to match with top alumni.
            </p>
          </div>

          {/* Filter dropdown */}
          <div className="flex items-center space-x-3">
            <Filter className="w-4 h-4 text-slate-400" />
            <select
              value={selectedDomain}
              onChange={handleDomainFilterChange}
              className="px-3 py-2 bg-white border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-emerald-500 outline-none"
            >
              <option value="">All Domains & Specializations</option>
              {domains.map(d => (
                <option key={d.domain_id} value={d.domain_id}>{d.domain_name}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Onboarding Callout Banner ONLY if student has ZERO skills configured */}
        {studentProfile && (!studentProfile.skills || studentProfile.skills.length === 0) && (
          <div className="my-6 p-5 bg-gradient-to-r from-emerald-500/10 via-teal-500/10 to-blue-500/10 border-2 border-emerald-500/30 rounded-2xl flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div className="flex items-start space-x-3">
              <div className="w-10 h-10 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center shrink-0">
                <Sparkles className="w-5 h-5 text-emerald-600" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-slate-900">Complete Profile & Skill Setup</h3>
                <p className="text-xs text-slate-600 mt-0.5">
                  You haven't configured your skills yet. Complete your setup so our Neo4j graph engine can calculate 5-factor affinity matches with alumni mentors.
                </p>
              </div>
            </div>
            <Link
              href="/student/profile"
              className="btn-primary text-xs px-4 py-2.5 whitespace-nowrap flex items-center space-x-1.5 shrink-0"
            >
              <span>Complete Profile & Skills</span>
              <span>&rarr;</span>
            </Link>
          </div>
        )}

        {/* Mentors Grid */}
        {loading ? (
          <div className="py-20 text-center text-slate-400 text-sm">
            <Sparkles className="w-8 h-8 mx-auto mb-2 text-emerald-500 animate-spin" />
            Calculating multi-factor affinity scores...
          </div>
        ) : authError ? (
          <div className="my-12 p-8 max-w-xl mx-auto bg-amber-50 border border-amber-200 rounded-2xl text-center space-y-4">
            <div className="w-12 h-12 bg-amber-100 text-amber-600 rounded-full flex items-center justify-center mx-auto">
              <LogIn className="w-6 h-6" />
            </div>
            <h2 className="text-lg font-bold text-slate-800">Student Sign-In Required</h2>
            <p className="text-sm text-slate-600">
              The multi-factor recommendation engine utilizes your student skill graph, domain interests, and department to calculate personalized mentor affinity scores.
            </p>
            <div className="flex flex-col sm:flex-row gap-3 justify-center pt-2">
              <button
                onClick={handleDemoStudentLogin}
                className="btn-primary text-sm px-4 py-2"
              >
                Sign In as Aarav Sharma (Demo Student)
              </button>
              <Link
                href="/login"
                className="px-4 py-2 border border-slate-300 rounded-xl text-sm font-semibold text-slate-700 bg-white hover:bg-slate-50 transition"
              >
                Go to Login Page
              </Link>
            </div>
          </div>
        ) : mentors.length === 0 ? (
          studentProfile && (!studentProfile.skills || studentProfile.skills.length === 0) ? (
            <div className="my-12 p-8 max-w-lg mx-auto bg-white border border-slate-200 rounded-2xl text-center space-y-4 shadow-sm">
              <div className="w-14 h-14 bg-emerald-50 text-emerald-600 rounded-2xl flex items-center justify-center mx-auto">
                <Compass className="w-7 h-7" />
              </div>
              <h2 className="text-lg font-bold text-slate-800">Activate AI Graph Discovery</h2>
              <p className="text-sm text-slate-600 leading-relaxed">
                Our recommendation engine matches mentors based on shared technical skills, domain alignment, and career goals. Configure your profile skills to view personalized alumni recommendations.
              </p>
              <div className="pt-2">
                <Link href="/student/profile" className="btn-primary text-sm px-6 py-2.5 inline-flex items-center space-x-2">
                  <span>Configure Skills</span>
                  <span>&rarr;</span>
                </Link>
              </div>
            </div>
          ) : (
            <div className="py-20 text-center">
              <p className="text-slate-500 font-medium">No mentors match the selected domain filters.</p>
            </div>
          )
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 my-8">
            {mentors.map(mentor => (
              <div key={mentor.mentor_user_id} className="card flex flex-col justify-between hover:shadow-md transition">
                <div>
                  {/* Top card header */}
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="text-base font-bold text-slate-900">{mentor.full_name}</h3>
                      <p className="text-xs text-slate-600 font-medium">
                        {mentor.job_title}
                      </p>
                      <p className="text-[11px] text-slate-400">
                        {mentor.company_name ? `@ ${mentor.company_name} • ` : ''}{mentor.years_experience} yrs exp
                      </p>
                    </div>

                    <div className="flex flex-col items-end">
                      <span className="badge bg-emerald-100 text-emerald-800 font-bold text-xs">
                        {mentor.overall_score}% Match
                      </span>
                      <span className="text-[10px] text-slate-400 mt-1">Rank #{mentor.rank_position}</span>
                    </div>
                  </div>

                  {/* Bayesian Rating */}
                  <div className="flex items-center space-x-1 mt-3 text-xs text-amber-500">
                    <Star className="w-3.5 h-3.5 fill-current" />
                    <span className="font-bold text-slate-800">
                      {mentor.average_rating ? mentor.average_rating.toFixed(1) : '5.0'}
                    </span>
                    <span className="text-slate-400 text-[11px]">
                      ({mentor.review_count} {mentor.review_count === 1 ? 'review' : 'reviews'})
                    </span>
                  </div>

                  {/* Explanation rationale */}
                  <p className="mt-3 text-xs text-slate-600 bg-slate-50 p-2.5 rounded-lg border border-slate-100 leading-relaxed italic">
                    "{mentor.explanation_text}"
                  </p>

                  {/* Skills tags */}
                  <div className="mt-4">
                    <p className="text-[10px] uppercase font-bold text-slate-400 tracking-wider mb-1.5">
                      Matched Skills & Domains
                    </p>
                    <div className="flex flex-wrap gap-1.5">
                      {mentor.matched_skills.map(skill => (
                        <span key={skill} className="px-2 py-0.5 bg-blue-50 text-blue-700 text-[11px] font-medium rounded-md border border-blue-200">
                          {skill}
                        </span>
                      ))}
                      {mentor.matched_domains.map(dom => (
                        <span key={dom} className="px-2 py-0.5 bg-purple-50 text-purple-700 text-[11px] font-medium rounded-md border border-purple-200">
                          {dom}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Request Action Button */}
                <div className="mt-6 pt-4 border-t border-slate-100">
                  <button
                    onClick={() => handleOpenRequestModal(mentor)}
                    disabled={!mentor.accepting_requests}
                    className="w-full btn-primary text-xs py-2 flex items-center justify-center space-x-2"
                  >
                    <Send className="w-3.5 h-3.5" />
                    <span>{mentor.accepting_requests ? 'Request Mentorship' : 'Capacity Full'}</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Request Modal */}
        {targetMentor && (
          <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 max-w-lg w-full p-6">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                <h3 className="text-base font-bold text-slate-900 flex items-center space-x-2">
                  <Send className="w-4 h-4 text-emerald-600" />
                  <span>Request Mentorship with {targetMentor.full_name}</span>
                </h3>
                <button onClick={() => setTargetMentor(null)} className="text-slate-400 hover:text-slate-600">
                  <X className="w-5 h-5" />
                </button>
              </div>

              {errorMsg && (
                <div className="mt-4 p-3 bg-rose-50 border border-rose-200 rounded-xl flex items-center space-x-2 text-rose-700 text-xs">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{errorMsg}</span>
                </div>
              )}

              {successMsg && (
                <div className="mt-4 p-3 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center space-x-2 text-emerald-700 text-xs font-semibold">
                  <CheckCircle className="w-4 h-4 shrink-0" />
                  <span>{successMsg}</span>
                </div>
              )}

              <form className="mt-4 space-y-4" onSubmit={handleSendRequest}>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Select Specialization Domain</label>
                  <select
                    value={requestDomainId}
                    onChange={e => setRequestDomainId(Number(e.target.value))}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs outline-none focus:ring-2 focus:ring-emerald-500"
                  >
                    {domains.map(d => (
                      <option key={d.domain_id} value={d.domain_id}>{d.domain_name}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Your Request Message & Learning Goals</label>
                  <textarea
                    rows={4}
                    required
                    value={requestMessage}
                    onChange={e => setRequestMessage(e.target.value)}
                    className="w-full p-3 border border-slate-300 rounded-lg text-xs outline-none focus:ring-2 focus:ring-emerald-500"
                    placeholder="Describe what areas you are looking for advice on..."
                  />
                </div>

                <div className="flex justify-end space-x-3 pt-3">
                  <button
                    type="button"
                    onClick={() => setTargetMentor(null)}
                    className="btn-secondary text-xs py-2 px-4"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submitting}
                    className="btn-primary text-xs py-2 px-4 flex items-center space-x-2"
                  >
                    <Send className="w-3.5 h-3.5" />
                    <span>{submitting ? 'Sending...' : 'Submit Request'}</span>
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

