'use client';

import React, { useEffect, useState } from 'react';
import Sidebar from '@/components/Sidebar';
import {
  Calendar, Clock, CheckCircle2, Star, Award,
  AlertCircle, X, CheckSquare, MessageSquare
} from 'lucide-react';
import { api } from '@/lib/api';
import { MentorAllocation, AvailabilitySlot, Booking, MentorshipSession } from '@/types';

export default function StudentSessionsPage() {
  const [allocations, setAllocations] = useState<MentorAllocation[]>([]);
  const [sessions, setSessions] = useState<MentorshipSession[]>([]);
  const [openSlots, setOpenSlots] = useState<{ [mentorId: number]: AvailabilitySlot[] }>({});
  const [loading, setLoading] = useState(true);

  // Booking Modal State
  const [selectedSlot, setSelectedSlot] = useState<{ slot: AvailabilitySlot; alloc: MentorAllocation } | null>(null);
  const [bookingType, setBookingType] = useState<'MENTORSHIP' | 'MOCK_INTERVIEW'>('MENTORSHIP');
  const [bookingSubmitting, setBookingSubmitting] = useState(false);
  const [bookingError, setBookingError] = useState<string | null>(null);

  // Review Modal State
  const [reviewSession, setReviewSession] = useState<MentorshipSession | null>(null);
  const [rating, setRating] = useState<number>(5);
  const [reviewText, setReviewText] = useState('');
  const [reviewSubmitting, setReviewSubmitting] = useState(false);
  const [reviewError, setReviewError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const [allocs, sess] = await Promise.all([
        api.getStudentAllocations(),
        api.getStudentSessions()
      ]);
      setAllocations(allocs);
      setSessions(sess);

      // Load open slots for each allocated mentor
      const slotsMap: { [mentorId: number]: AvailabilitySlot[] } = {};
      for (const a of allocs) {
        if (a.allocation_status === 'ACTIVE') {
          try {
            const slots = await api.getOpenSlotsForMentor(a.mentor_user_id);
            slotsMap[a.mentor_user_id] = slots;
          } catch (e) {
            console.error(e);
          }
        }
      }
      setOpenSlots(slotsMap);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleBookSlot = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedSlot) return;

    setBookingSubmitting(true);
    setBookingError(null);
    try {
      await api.createBooking({
        availability_id: selectedSlot.slot.availability_id,
        allocation_id: selectedSlot.alloc.allocation_id,
        booking_type: bookingType
      });
      setSelectedSlot(null);
      setSuccessMessage("Session booked successfully! Stored procedure SP02 executed ACID transaction.");
      await loadData();
    } catch (err: any) {
      setBookingError(err.message || 'Booking failed');
    } finally {
      setBookingSubmitting(false);
    }
  };

  const handleSubmitReview = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reviewSession) return;

    setReviewSubmitting(true);
    setReviewError(null);
    try {
      await api.submitMentorReview({
        session_id: reviewSession.session_id,
        rating,
        review_text: reviewText
      });
      setReviewSession(null);
      setSuccessMessage("Thank you! Review and rating recorded (SP05) and Bayesian quality score updated.");
      await loadData();
    } catch (err: any) {
      setReviewError(err.message || 'Failed to submit review');
    } finally {
      setReviewSubmitting(false);
    }
  };

  return (
    <div className="flex-1 flex">
      <Sidebar role="STUDENT" />

      <main className="flex-1 p-8 overflow-y-auto max-w-7xl">
        <div className="pb-6 border-b border-slate-200">
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight flex items-center space-x-2">
            <Calendar className="w-6 h-6 text-emerald-600" />
            <span>Sessions & Bookings</span>
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Book open slots with your assigned mentors and view completed session assessments.
          </p>
        </div>

        {successMessage && (
          <div className="my-6 p-4 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center space-x-2 text-emerald-800 text-sm">
            <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
            <span>{successMessage}</span>
          </div>
        )}

        {/* Section 1: Book Open Availability Slots */}
        <div className="my-8">
          <h2 className="text-lg font-bold text-slate-900 mb-4 flex items-center space-x-2">
            <Clock className="w-5 h-5 text-blue-600" />
            <span>Available Slots from Your Mentors</span>
          </h2>

          {loading ? (
            <div className="card text-center text-slate-400 py-8">Checking availability calendars...</div>
          ) : allocations.length === 0 ? (
            <div className="card text-center py-8">
              <p className="text-sm text-slate-500">You do not have any active mentor allocations yet.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {allocations.map(alloc => {
                const slots = openSlots[alloc.mentor_user_id] || [];
                return (
                  <div key={alloc.allocation_id} className="card">
                    <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                      <div>
                        <h3 className="font-bold text-slate-900">{alloc.mentor_name}</h3>
                        <p className="text-xs text-slate-500">Domain: {alloc.domain_name || 'General'}</p>
                      </div>
                      <span className="badge badge-active">{alloc.allocation_status}</span>
                    </div>

                    <div className="mt-4">
                      {slots.length === 0 ? (
                        <p className="text-xs text-slate-400 italic">No open slots currently published by this mentor.</p>
                      ) : (
                        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                          {slots.map(slot => (
                            <div key={slot.availability_id} className="p-3 bg-slate-50 rounded-xl border border-slate-200 flex flex-col justify-between">
                              <div>
                                <p className="text-xs font-bold text-slate-800">
                                  {new Date(slot.starts_at).toLocaleDateString([], { weekday: 'short', month: 'short', day: 'numeric' })}
                                </p>
                                <p className="text-[11px] text-slate-500 mt-0.5">
                                  {new Date(slot.starts_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} – {new Date(slot.ends_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                </p>
                              </div>
                              <button
                                onClick={() => setSelectedSlot({ slot, alloc })}
                                className="btn-primary text-xs py-1 px-3 mt-3 w-full"
                              >
                                Reserve Slot
                              </button>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Section 2: Session Records (Upcoming & Completed) */}
        <div className="my-8">
          <h2 className="text-lg font-bold text-slate-900 mb-4 flex items-center space-x-2">
            <CheckSquare className="w-5 h-5 text-emerald-600" />
            <span>My Session Records & Evaluations</span>
          </h2>

          {sessions.length === 0 ? (
            <div className="card text-center py-8">
              <p className="text-sm text-slate-500">No session history yet.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {sessions.map(sess => (
                <div key={sess.session_id} className="card">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
                    <div className="flex items-center space-x-3">
                      <h3 className="font-bold text-slate-900 text-base">
                        Session with {sess.mentor_name || 'Mentor'}
                      </h3>
                      <span className={`badge ${
                        sess.session_status === 'COMPLETED' ? 'badge-completed' :
                        sess.session_status === 'SCHEDULED' ? 'badge-pending' : 'badge-rejected'
                      }`}>
                        {sess.session_status}
                      </span>
                    </div>

                    {sess.slot_starts_at && (
                      <span className="text-xs text-slate-500 flex items-center space-x-1">
                        <Clock className="w-3.5 h-3.5" />
                        <span>{new Date(sess.slot_starts_at).toLocaleString()}</span>
                      </span>
                    )}
                  </div>

                  {/* If completed, show mentor outcome evaluation */}
                  {sess.session_status === 'COMPLETED' && (
                    <div className="mt-4 space-y-3 bg-slate-50 p-4 rounded-xl border border-slate-200 text-xs">
                      {sess.discussion_summary && (
                        <div>
                          <p className="font-bold text-slate-700">Discussion Summary:</p>
                          <p className="text-slate-600 mt-0.5">{sess.discussion_summary}</p>
                        </div>
                      )}
                      {sess.performance_observations && (
                        <div>
                          <p className="font-bold text-slate-700">Performance Observations:</p>
                          <p className="text-slate-600 mt-0.5">{sess.performance_observations}</p>
                        </div>
                      )}
                      {sess.next_steps && (
                        <div>
                          <p className="font-bold text-slate-700">Action Items & Next Steps:</p>
                          <p className="text-slate-600 mt-0.5">{sess.next_steps}</p>
                        </div>
                      )}

                      {/* Skill assessments rubric */}
                      {sess.skill_assessments && sess.skill_assessments.length > 0 && (
                        <div className="pt-2 border-t border-slate-200">
                          <p className="font-bold text-slate-700 mb-2">Evaluated Skills Rubric:</p>
                          <div className="flex flex-wrap gap-2">
                            {sess.skill_assessments.map(sa => (
                              <span key={sa.skill_id} className="px-2 py-1 bg-white rounded border border-slate-200 text-[11px]">
                                <span className="font-semibold text-slate-800">{sa.skill_name}: </span>
                                <span className="text-emerald-700 font-bold">{sa.assessment_result}</span>
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Review action for completed session */}
                  {sess.session_status === 'COMPLETED' && (
                    <div className="mt-4 pt-3 border-t border-slate-100 flex justify-end">
                      <button
                        onClick={() => {
                          setReviewSession(sess);
                          setReviewError(null);
                        }}
                        className="btn-secondary text-xs py-1.5 px-3 flex items-center space-x-1 text-amber-700 border-amber-200 bg-amber-50 hover:bg-amber-100"
                      >
                        <Star className="w-3.5 h-3.5 fill-current" />
                        <span>Submit / Update Mentor Rating</span>
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Reserve Slot Modal */}
        {selectedSlot && (
          <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 max-w-md w-full p-6">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                <h3 className="text-base font-bold text-slate-900">Confirm Session Reservation</h3>
                <button onClick={() => setSelectedSlot(null)} className="text-slate-400 hover:text-slate-600">
                  <X className="w-5 h-5" />
                </button>
              </div>

              {bookingError && (
                <div className="mt-4 p-3 bg-rose-50 border border-rose-200 rounded-xl text-rose-700 text-xs flex items-center space-x-2">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{bookingError}</span>
                </div>
              )}

              <form className="mt-4 space-y-4" onSubmit={handleBookSlot}>
                <div className="p-3 bg-slate-50 rounded-lg text-xs space-y-1">
                  <p><span className="font-semibold">Mentor:</span> {selectedSlot.alloc.mentor_name}</p>
                  <p><span className="font-semibold">Starts:</span> {new Date(selectedSlot.slot.starts_at).toLocaleString()}</p>
                  <p><span className="font-semibold">Ends:</span> {new Date(selectedSlot.slot.ends_at).toLocaleString()}</p>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Session Type</label>
                  <select
                    value={bookingType}
                    onChange={e => setBookingType(e.target.value as any)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs outline-none"
                  >
                    <option value="MENTORSHIP">1-on-1 Mentorship & Career Guidance</option>
                    <option value="MOCK_INTERVIEW">Offline Technical Mock Interview</option>
                  </select>
                </div>

                <div className="flex justify-end space-x-3 pt-3">
                  <button
                    type="button"
                    onClick={() => setSelectedSlot(null)}
                    className="btn-secondary text-xs py-2 px-4"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={bookingSubmitting}
                    className="btn-primary text-xs py-2 px-4"
                  >
                    {bookingSubmitting ? 'Reserving...' : 'Confirm Booking'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Submit Review Modal */}
        {reviewSession && (
          <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 max-w-md w-full p-6">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                <h3 className="text-base font-bold text-slate-900">Review Your Mentorship Session</h3>
                <button onClick={() => setReviewSession(null)} className="text-slate-400 hover:text-slate-600">
                  <X className="w-5 h-5" />
                </button>
              </div>

              {reviewError && (
                <div className="mt-4 p-3 bg-rose-50 border border-rose-200 rounded-xl text-rose-700 text-xs flex items-center space-x-2">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{reviewError}</span>
                </div>
              )}

              <form className="mt-4 space-y-4" onSubmit={handleSubmitReview}>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Rating (1 to 5 Stars)</label>
                  <div className="flex space-x-2">
                    {[1, 2, 3, 4, 5].map(star => (
                      <button
                        key={star}
                        type="button"
                        onClick={() => setRating(star)}
                        className={`p-2 rounded-lg border text-sm font-bold flex items-center space-x-1 ${
                          rating >= star ? 'bg-amber-100 border-amber-300 text-amber-800' : 'bg-slate-50 border-slate-200 text-slate-400'
                        }`}
                      >
                        <Star className={`w-4 h-4 ${rating >= star ? 'fill-current' : ''}`} />
                        <span>{star}</span>
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Feedback Comments</label>
                  <textarea
                    rows={4}
                    value={reviewText}
                    onChange={e => setReviewText(e.target.value)}
                    placeholder="Share how this session assisted your career or technical preparation..."
                    className="w-full p-3 border border-slate-300 rounded-lg text-xs outline-none focus:ring-2 focus:ring-emerald-500"
                  />
                </div>

                <div className="flex justify-end space-x-3 pt-3">
                  <button
                    type="button"
                    onClick={() => setReviewSession(null)}
                    className="btn-secondary text-xs py-2 px-4"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={reviewSubmitting}
                    className="btn-primary text-xs py-2 px-4"
                  >
                    {reviewSubmitting ? 'Submitting...' : 'Submit Review'}
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

