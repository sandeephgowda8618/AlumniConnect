'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { UserPlus, AlertCircle, GraduationCap, Briefcase } from 'lucide-react';
import { api } from '@/lib/api';
import { MentorshipDomain } from '@/types';

export default function RegisterPage() {
  const router = useRouter();
  const [role, setRole] = useState<'STUDENT' | 'MENTOR'>('STUDENT');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [domains, setDomains] = useState<MentorshipDomain[]>([]);

  // Student specific
  const [studentNumber, setStudentNumber] = useState('2024CS099');
  const [programme, setProgramme] = useState('B.Tech Computer Science');
  const [graduationYear, setGraduationYear] = useState('2026');
  const [careerGoal, setCareerGoal] = useState('Machine Learning & AI');

  // Mentor specific
  const [jobTitle, setJobTitle] = useState('Principal Software Engineer');
  const [yearsExp, setYearsExp] = useState('8.5');
  const [maxMentees, setMaxMentees] = useState('3');

  useEffect(() => {
    api.getDomains()
      .then(doms => {
        if (doms && doms.length > 0) {
          setDomains(doms);
          setCareerGoal(doms[0].domain_name);
        }
      })
      .catch(err => {
        console.error("Failed to fetch domain catalogue:", err);
      });
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (role === 'STUDENT') {
        const user = await api.registerStudent({
          email,
          password,
          display_name: displayName,
          student_number: studentNumber,
          department_id: 1,
          programme,
          batch_year: 2022,
          expected_graduation_year: parseInt(graduationYear),
          career_goal: careerGoal
        });
        router.push('/student/dashboard');
      } else {
        const user = await api.registerMentor({
          email,
          password,
          display_name: displayName,
          job_title: jobTitle,
          years_experience: parseFloat(yearsExp),
          max_active_mentees: parseInt(maxMentees),
          department_id: 1,
          company_id: 1
        });
        router.push('/mentor/dashboard');
      }
    } catch (err: any) {
      setError(err.message || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex-1 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-lg w-full space-y-6 bg-white p-8 rounded-2xl shadow-xl border border-slate-200">
        <div className="text-center">
          <h2 className="text-2xl font-extrabold text-slate-900">Create your Account</h2>
          <p className="mt-1 text-sm text-slate-500">
            Join the AlumniConnect campus mentorship network
          </p>
        </div>

        {/* Role Toggle */}
        <div className="grid grid-cols-2 gap-3 p-1 bg-slate-100 rounded-xl">
          <button
            type="button"
            onClick={() => setRole('STUDENT')}
            className={`py-2 text-sm font-semibold rounded-lg flex items-center justify-center space-x-2 transition ${
              role === 'STUDENT' ? 'bg-white text-emerald-700 shadow-sm' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <GraduationCap className="w-4 h-4" />
            <span>Student Mentee</span>
          </button>

          <button
            type="button"
            onClick={() => setRole('MENTOR')}
            className={`py-2 text-sm font-semibold rounded-lg flex items-center justify-center space-x-2 transition ${
              role === 'MENTOR' ? 'bg-white text-emerald-700 shadow-sm' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Briefcase className="w-4 h-4" />
            <span>Alumni Mentor</span>
          </button>
        </div>

        {error && (
          <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl flex items-center space-x-2 text-rose-700 text-sm">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form className="space-y-4" onSubmit={handleSubmit}>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Full Name</label>
              <input
                type="text"
                required
                value={displayName}
                onChange={e => setDisplayName(e.target.value)}
                placeholder="John Doe"
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-emerald-500 outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Email</label>
              <input
                type="email"
                required
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="john@alumniconnect.edu"
                className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-emerald-500 outline-none"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Password</label>
            <input
              type="password"
              required
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-emerald-500 outline-none"
            />
          </div>

          {role === 'STUDENT' ? (
            <div className="space-y-3 pt-2 border-t border-slate-100">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Student Roll No</label>
                  <input
                    type="text"
                    required
                    value={studentNumber}
                    onChange={e => setStudentNumber(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Expected Graduation</label>
                  <input
                    type="number"
                    required
                    value={graduationYear}
                    onChange={e => setGraduationYear(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm outline-none"
                  />
                </div>
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Target Career Goal</label>
                <select
                  required
                  value={careerGoal}
                  onChange={e => setCareerGoal(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 bg-white rounded-lg text-sm focus:ring-2 focus:ring-emerald-500 outline-none"
                >
                  {domains.length > 0 ? (
                    domains.map(d => (
                      <option key={d.domain_id} value={d.domain_name}>
                        {d.domain_name}
                      </option>
                    ))
                  ) : (
                    <>
                      <option value="Machine Learning & AI">Machine Learning & AI</option>
                      <option value="Cloud Computing & DevOps">Cloud Computing & DevOps</option>
                      <option value="Full-Stack Web Engineering">Full-Stack Web Engineering</option>
                      <option value="Distributed Systems & Microservices">Distributed Systems & Microservices</option>
                      <option value="Data Engineering & Analytics">Data Engineering & Analytics</option>
                    </>
                  )}
                </select>
                <p className="text-[11px] text-slate-400 mt-1">
                  Select your primary career aspiration from available mentorship tracks.
                </p>
              </div>
            </div>
          ) : (
            <div className="space-y-3 pt-2 border-t border-slate-100">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Current Job Title</label>
                  <input
                    type="text"
                    required
                    value={jobTitle}
                    onChange={e => setJobTitle(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Years Experience</label>
                  <input
                    type="number"
                    step="0.5"
                    required
                    value={yearsExp}
                    onChange={e => setYearsExp(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm outline-none"
                  />
                </div>
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Max Active Mentees</label>
                <input
                  type="number"
                  min="1"
                  max="10"
                  required
                  value={maxMentees}
                  onChange={e => setMaxMentees(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm outline-none"
                />
              </div>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full btn-primary py-2.5 flex items-center justify-center space-x-2 mt-4"
          >
            <UserPlus className="w-4 h-4" />
            <span>{loading ? 'Creating Account...' : 'Complete Registration'}</span>
          </button>
        </form>

        <p className="text-center text-xs text-slate-500">
          Already registered?{' '}
          <Link href="/login" className="text-emerald-600 font-semibold hover:underline">
            Sign in here
          </Link>
        </p>
      </div>
    </div>
  );
}

