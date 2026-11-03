'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import Sidebar from '@/components/Sidebar';
import {
  User, Save, CheckCircle2, AlertCircle, BookOpen, GraduationCap,
  Plus, X, Sparkles, ArrowRight
} from 'lucide-react';
import { api } from '@/lib/api';
import { StudentProfile, MentorshipDomain, Skill } from '@/types';

const PROFICIENCY_OPTIONS = [
  { value: 'BEGINNER', label: 'Beginner (Foundational)' },
  { value: 'INTERMEDIATE', label: 'Intermediate (Working knowledge)' },
  { value: 'ADVANCED', label: 'Advanced (Proficient)' },
  { value: 'EXPERT', label: 'Expert (Mastery)' },
];

export default function StudentProfilePage() {
  const [profile, setProfile] = useState<StudentProfile | null>(null);
  const [domains, setDomains] = useState<MentorshipDomain[]>([]);
  const [allSkills, setAllSkills] = useState<Skill[]>([]);

  // Form states
  const [careerGoal, setCareerGoal] = useState('');
  const [bio, setBio] = useState('');
  const [gradYear, setGradYear] = useState('');

  // Skills & Domains state
  const [userSkills, setUserSkills] = useState<{
    skill_id: number;
    skill_name: string;
    proficiency_level: string;
    years_experience?: number;
  }[]>([]);

  const [userDomains, setUserDomains] = useState<{
    domain_id: number;
    domain_name: string;
    priority_order?: number;
  }[]>([]);

  // Picker states
  const [selectedSkillId, setSelectedSkillId] = useState<number | ''>('');
  const [selectedProficiency, setSelectedProficiency] = useState<string>('INTERMEDIATE');
  const [selectedDomainId, setSelectedDomainId] = useState<number | ''>('');

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      api.getStudentProfile(),
      api.getDomains().catch(() => []),
      api.getSkills().catch(() => [])
    ])
      .then(([p, doms, sks]) => {
        setProfile(p);
        setDomains(doms);
        setAllSkills(sks);

        setCareerGoal(p.career_goal || (doms.length > 0 ? doms[0].domain_name : 'Machine Learning & AI'));
        setBio(p.bio || '');
        setGradYear(p.expected_graduation_year ? String(p.expected_graduation_year) : '');

        setUserSkills(
          (p.skills || []).map(s => ({
            skill_id: s.skill_id,
            skill_name: s.skill_name,
            proficiency_level: s.proficiency_level || 'INTERMEDIATE'
          }))
        );

        setUserDomains(
          (p.domain_interests || []).map(d => ({
            domain_id: d.domain_id,
            domain_name: d.domain_name,
            priority_order: d.priority_order || 1
          }))
        );

        // Pre-select first unadded skill/domain
        const unaddedSkill = sks.find(s => !p.skills?.some(ps => ps.skill_id === s.skill_id));
        if (unaddedSkill) setSelectedSkillId(unaddedSkill.skill_id);

        const unaddedDomain = doms.find(d => !p.domain_interests?.some(pd => pd.domain_id === d.domain_id));
        if (unaddedDomain) setSelectedDomainId(unaddedDomain.domain_id);
      })
      .catch(err => {
        console.error("Profile load error:", err);
        setErrorMessage(err.message || "Failed to load profile details");
      })
      .finally(() => setLoading(false));
  }, []);

  const handleAddSkill = () => {
    if (!selectedSkillId) return;
    const skillObj = allSkills.find(s => s.skill_id === Number(selectedSkillId));
    if (!skillObj) return;

    if (userSkills.some(s => s.skill_id === skillObj.skill_id)) return;

    const updated = [
      ...userSkills,
      {
        skill_id: skillObj.skill_id,
        skill_name: skillObj.skill_name,
        proficiency_level: selectedProficiency,
        years_experience: 1.0
      }
    ];
    setUserSkills(updated);

    // Update picker to next available
    const nextSkill = allSkills.find(s => !updated.some(us => us.skill_id === s.skill_id));
    setSelectedSkillId(nextSkill ? nextSkill.skill_id : '');
  };

  const handleRemoveSkill = (skillId: number) => {
    setUserSkills(prev => prev.filter(s => s.skill_id !== skillId));
  };

  const handleAddDomain = () => {
    if (!selectedDomainId) return;
    const domainObj = domains.find(d => d.domain_id === Number(selectedDomainId));
    if (!domainObj) return;

    if (userDomains.some(d => d.domain_id === domainObj.domain_id)) return;

    const updated = [
      ...userDomains,
      {
        domain_id: domainObj.domain_id,
        domain_name: domainObj.domain_name,
        priority_order: userDomains.length + 1
      }
    ];
    setUserDomains(updated);

    // Update picker to next available
    const nextDomain = domains.find(d => !updated.some(ud => ud.domain_id === d.domain_id));
    setSelectedDomainId(nextDomain ? nextDomain.domain_id : '');
  };

  const handleRemoveDomain = (domainId: number) => {
    setUserDomains(prev => prev.filter(d => d.domain_id !== domainId));
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setSaveSuccess(false);
    setErrorMessage(null);

    try {
      // 1. Update core profile
      const updatedProfile = await api.updateStudentProfile({
        career_goal: careerGoal,
        bio: bio,
        expected_graduation_year: gradYear ? parseInt(gradYear) : undefined
      });

      // 2. Synchronize skills and domains in SQL & Neo4j graph, invalidating Redis cache
      const syncedProfile = await api.syncStudentSkillsAndDomains({
        skills: userSkills.map(s => ({
          skill_id: s.skill_id,
          proficiency_level: s.proficiency_level,
          years_experience: s.years_experience || 0
        })),
        domains: userDomains.map((d, idx) => ({
          domain_id: d.domain_id,
          priority_order: idx + 1
        }))
      });

      setProfile(syncedProfile || updatedProfile);
      setSaveSuccess(true);
    } catch (err: any) {
      console.error("Save profile error:", err);
      setErrorMessage(err.message || 'Failed to save profile changes');
    } finally {
      setSaving(false);
    }
  };

  const availableSkillsToAdd = allSkills.filter(
    s => !userSkills.some(us => us.skill_id === s.skill_id)
  );

  const availableDomainsToAdd = domains.filter(
    d => !userDomains.some(ud => ud.domain_id === d.domain_id)
  );

  return (
    <div className="flex-1 flex">
      <Sidebar role="STUDENT" />

      <main className="flex-1 p-8 overflow-y-auto max-w-4xl">
        <div className="pb-6 border-b border-slate-200">
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight flex items-center space-x-2">
            <User className="w-6 h-6 text-emerald-600" />
            <span>Student Profile & Skills</span>
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Keep your skills and career interests updated to activate AI graph recommendations and receive high-affinity mentor matches.
          </p>
        </div>

        {/* Success Alert Banner with Direct Link to Mentor Discovery */}
        {saveSuccess && (
          <div className="my-6 p-4 bg-emerald-50 border border-emerald-200 rounded-2xl flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 shadow-sm">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center shrink-0">
                <CheckCircle2 className="w-5 h-5 text-emerald-600" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-emerald-900">Graph Relationships & Profile Updated!</h4>
                <p className="text-xs text-emerald-700 mt-0.5">
                  Your skill and domain nodes are synchronized in Neo4j and fresh mentor recommendations are ready.
                </p>
              </div>
            </div>
            <Link
              href="/student/mentors"
              className="btn-primary text-xs px-4 py-2 flex items-center space-x-1.5 shrink-0"
            >
              <span>Explore Recommended Mentors</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        )}

        {errorMessage && (
          <div className="my-6 p-4 bg-rose-50 border border-rose-200 rounded-xl flex items-center space-x-2 text-rose-700 text-sm">
            <AlertCircle className="w-5 h-5 text-rose-600 shrink-0" />
            <span>{errorMessage}</span>
          </div>
        )}

        {loading ? (
          <div className="py-20 text-center text-slate-400">Loading student profile...</div>
        ) : profile && (
          <form className="space-y-6 my-8" onSubmit={handleSave}>
            {/* Academic Information */}
            <div className="card space-y-4">
              <h2 className="text-base font-bold text-slate-900 flex items-center space-x-2">
                <GraduationCap className="w-4 h-4 text-blue-600" />
                <span>Academic Information</span>
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
                  <label className="block text-xs font-semibold text-slate-500 mb-1">Student Roll Number</label>
                  <input
                    type="text"
                    disabled
                    value={profile.student_number}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-600"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-500 mb-1">Department</label>
                  <input
                    type="text"
                    disabled
                    value={profile.department_name || 'Computer Science and Engineering'}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-600"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Expected Graduation Year</label>
                  <input
                    type="number"
                    value={gradYear}
                    onChange={e => setGradYear(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-emerald-500 outline-none"
                  />
                </div>
              </div>

              {/* Career Goal Statement Dropdown */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Career Goal Statement</label>
                <select
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
                  Populated from authoritative platform mentorship domain catalogues.
                </p>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Biography / About Me</label>
                <textarea
                  rows={3}
                  value={bio}
                  onChange={e => setBio(e.target.value)}
                  placeholder="Briefly describe your interests and project portfolio..."
                  className="w-full p-3 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-emerald-500 outline-none"
                />
              </div>
            </div>

            {/* Current Skills & Domain Interests with Onboarding Callout & Full Editors */}
            <div className="card space-y-6">
              <div className="flex items-center justify-between">
                <h2 className="text-base font-bold text-slate-900 flex items-center space-x-2">
                  <BookOpen className="w-4 h-4 text-purple-600" />
                  <span>Current Skills & Domain Interests</span>
                </h2>
                <span className="text-xs text-slate-400 font-medium">
                  {userSkills.length} skills • {userDomains.length} domains
                </span>
              </div>

              {/* Unconfigured New User Banner */}
              {userSkills.length === 0 && userDomains.length === 0 && (
                <div className="p-5 bg-gradient-to-r from-emerald-50 to-teal-50 border-2 border-dashed border-emerald-300 rounded-2xl text-center space-y-2">
                  <div className="w-10 h-10 bg-emerald-100 text-emerald-700 rounded-full flex items-center justify-center mx-auto">
                    <Sparkles className="w-5 h-5 text-emerald-600" />
                  </div>
                  <h3 className="text-sm font-bold text-emerald-950">Activate AI Graph Recommendations</h3>
                  <p className="text-xs text-emerald-800 max-w-lg mx-auto leading-relaxed">
                    Choose your technical skills and domain interests below to enable our multi-hop graph recommendation pipeline to calculate personalized mentor affinity scores.
                  </p>
                </div>
              )}

              {/* 1. Technical Skills Management */}
              <div className="space-y-3 pt-2">
                <label className="block text-xs font-semibold text-slate-700">
                  Technical Skills & Proficiencies
                </label>

                {userSkills.length === 0 ? (
                  <p className="text-xs text-slate-400 italic">No skills added yet. Select a skill below.</p>
                ) : (
                  <div className="flex flex-wrap gap-2">
                    {userSkills.map(s => (
                      <div
                        key={s.skill_id}
                        className="inline-flex items-center space-x-2 px-3 py-1.5 bg-blue-50 border border-blue-200 text-blue-800 rounded-lg text-xs font-semibold shadow-xs"
                      >
                        <span>{s.skill_name}</span>
                        <span className="text-[10px] uppercase px-1.5 py-0.5 rounded bg-blue-200/70 text-blue-900 font-bold">
                          {s.proficiency_level}
                        </span>
                        <button
                          type="button"
                          onClick={() => handleRemoveSkill(s.skill_id)}
                          className="text-blue-400 hover:text-rose-600 transition p-0.5"
                          title="Remove skill"
                        >
                          <X className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}

                {/* Add Skill Controls */}
                <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 pt-2">
                  <select
                    value={selectedSkillId}
                    onChange={e => setSelectedSkillId(e.target.value ? Number(e.target.value) : '')}
                    className="flex-1 px-3 py-2 border border-slate-300 bg-white rounded-lg text-xs focus:ring-2 focus:ring-blue-500 outline-none"
                  >
                    <option value="">-- Choose Technical Skill --</option>
                    {availableSkillsToAdd.map(s => (
                      <option key={s.skill_id} value={s.skill_id}>
                        {s.skill_name}
                      </option>
                    ))}
                  </select>

                  <select
                    value={selectedProficiency}
                    onChange={e => setSelectedProficiency(e.target.value)}
                    className="w-full sm:w-48 px-3 py-2 border border-slate-300 bg-white rounded-lg text-xs focus:ring-2 focus:ring-blue-500 outline-none"
                  >
                    {PROFICIENCY_OPTIONS.map(opt => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>

                  <button
                    type="button"
                    onClick={handleAddSkill}
                    disabled={!selectedSkillId}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-200 disabled:text-slate-400 text-white rounded-lg text-xs font-bold transition flex items-center justify-center space-x-1"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>Add Skill</span>
                  </button>
                </div>
              </div>

              {/* 2. Mentorship Domain Interests Management */}
              <div className="space-y-3 pt-4 border-t border-slate-100">
                <label className="block text-xs font-semibold text-slate-700">
                  Mentorship Domain Interests
                </label>

                {userDomains.length === 0 ? (
                  <p className="text-xs text-slate-400 italic">No domain interests added yet. Select a domain below.</p>
                ) : (
                  <div className="flex flex-wrap gap-2">
                    {userDomains.map((d, idx) => (
                      <div
                        key={d.domain_id}
                        className="inline-flex items-center space-x-2 px-3 py-1.5 bg-purple-50 border border-purple-200 text-purple-800 rounded-lg text-xs font-semibold shadow-xs"
                      >
                        <span className="w-4 h-4 rounded-full bg-purple-200 text-purple-800 text-[10px] flex items-center justify-center font-bold">
                          {idx + 1}
                        </span>
                        <span>{d.domain_name}</span>
                        <button
                          type="button"
                          onClick={() => handleRemoveDomain(d.domain_id)}
                          className="text-purple-400 hover:text-rose-600 transition p-0.5"
                          title="Remove domain"
                        >
                          <X className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}

                {/* Add Domain Controls */}
                <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 pt-2">
                  <select
                    value={selectedDomainId}
                    onChange={e => setSelectedDomainId(e.target.value ? Number(e.target.value) : '')}
                    className="flex-1 px-3 py-2 border border-slate-300 bg-white rounded-lg text-xs focus:ring-2 focus:ring-purple-500 outline-none"
                  >
                    <option value="">-- Choose Mentorship Domain --</option>
                    {availableDomainsToAdd.map(d => (
                      <option key={d.domain_id} value={d.domain_id}>
                        {d.domain_name}
                      </option>
                    ))}
                  </select>

                  <button
                    type="button"
                    onClick={handleAddDomain}
                    disabled={!selectedDomainId}
                    className="px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-slate-200 disabled:text-slate-400 text-white rounded-lg text-xs font-bold transition flex items-center justify-center space-x-1"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>Add Domain</span>
                  </button>
                </div>
              </div>
            </div>

            <div className="flex items-center justify-between pt-2">
              <span className="text-xs text-slate-400">
                Saving synchronizes MySQL, Redis cache, and Neo4j graph relationships.
              </span>

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
