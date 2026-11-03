'use client';

import React, { useEffect, useState } from 'react';
import Sidebar from '@/components/Sidebar';
import { Calendar, Plus, Clock, CheckCircle2, AlertCircle } from 'lucide-react';
import { api } from '@/lib/api';
import { AvailabilitySlot } from '@/types';

export default function MentorAvailabilityPage() {
  const [slots, setSlots] = useState<AvailabilitySlot[]>([]);
  const [loading, setLoading] = useState(true);
  const [startsAt, setStartsAt] = useState('');
  const [endsAt, setEndsAt] = useState('');
  const [publishing, setPublishing] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadSlots = () => {
    setLoading(true);
    api.getMentorSlots()
      .then(setSlots)
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadSlots();
    // Set default initial slot time (tomorrow 10:00 - 10:45)
    const tmrw = new Date();
    tmrw.setDate(tmrw.getDate() + 1);
    tmrw.setHours(10, 0, 0, 0);
    const tmrwEnd = new Date(tmrw);
    tmrwEnd.setMinutes(tmrwEnd.getMinutes() + 45);

    setStartsAt(tmrw.toISOString().slice(0, 16));
    setEndsAt(tmrwEnd.toISOString().slice(0, 16));
  }, []);

  const handlePublish = async (e: React.FormEvent) => {
    e.preventDefault();
    setPublishing(true);
    setMessage(null);
    setError(null);

    try {
      await api.publishAvailabilitySlot({
        starts_at: new Date(startsAt).toISOString(),
        ends_at: new Date(endsAt).toISOString(),
      });
      setMessage("Availability slot published successfully! Mentees can now book this time slot.");
      loadSlots();
    } catch (err: any) {
      setError(err.message || 'Failed to publish slot');
    } finally {
      setPublishing(false);
    }
  };

  return (
    <div className="flex-1 flex">
      <Sidebar role="MENTOR" />

      <main className="flex-1 p-8 overflow-y-auto max-w-7xl">
        <div className="pb-6 border-b border-slate-200">
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight flex items-center space-x-2">
            <Calendar className="w-6 h-6 text-emerald-600" />
            <span>Availability Calendar</span>
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Publish time slots for your active mentees to schedule 1-on-1 mentorship sessions and mock interviews.
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

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 my-8">
          {/* Publish Slot Form */}
          <div className="card lg:col-span-1">
            <h2 className="text-base font-bold text-slate-900 mb-4 flex items-center space-x-2">
              <Plus className="w-4 h-4 text-emerald-600" />
              <span>Publish New Time Slot</span>
            </h2>

            <form className="space-y-4" onSubmit={handlePublish}>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Slot Start Time</label>
                <input
                  type="datetime-local"
                  required
                  value={startsAt}
                  onChange={e => setStartsAt(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs outline-none focus:ring-2 focus:ring-emerald-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Slot End Time</label>
                <input
                  type="datetime-local"
                  required
                  value={endsAt}
                  onChange={e => setEndsAt(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg text-xs outline-none focus:ring-2 focus:ring-emerald-500"
                />
              </div>

              <button
                type="submit"
                disabled={publishing}
                className="w-full btn-primary text-xs py-2.5 flex items-center justify-center space-x-2 mt-2"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>{publishing ? 'Publishing...' : 'Publish Slot'}</span>
              </button>
            </form>
          </div>

          {/* List of Published Slots */}
          <div className="card lg:col-span-2">
            <h2 className="text-base font-bold text-slate-900 mb-4 flex items-center space-x-2">
              <Clock className="w-4 h-4 text-blue-600" />
              <span>Published Availability Slots</span>
            </h2>

            {loading ? (
              <p className="text-xs text-slate-400 py-8 text-center">Loading slots...</p>
            ) : slots.length === 0 ? (
              <p className="text-xs text-slate-500 py-8 text-center">No slots published yet.</p>
            ) : (
              <div className="divide-y divide-slate-100">
                {slots.map(slot => (
                  <div key={slot.availability_id} className="py-3 flex items-center justify-between">
                    <div>
                      <p className="text-sm font-semibold text-slate-800">
                        {new Date(slot.starts_at).toLocaleDateString([], { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' })}
                      </p>
                      <p className="text-xs text-slate-500">
                        {new Date(slot.starts_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} – {new Date(slot.ends_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </p>
                    </div>

                    <span className={`badge ${
                      slot.slot_status === 'OPEN' ? 'badge-active' :
                      slot.slot_status === 'BOOKED' ? 'badge-confirmed' : 'badge-rejected'
                    }`}>
                      {slot.slot_status}
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

