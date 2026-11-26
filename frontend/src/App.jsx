import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Building2, PhoneCall, Stethoscope, CalendarCheck2, Clock } from 'lucide-react';
import { TopBar } from './components/TopBar';
import { DoctorsList } from './components/DoctorsList';
import { AppointmentsList } from './components/AppointmentsList';
import { PhoneModal } from './components/PhoneModal';
import { useSSE } from './hooks/useSSE';
import { useWebRTC } from './hooks/useWebRTC';
import { getDoctors, getAppointments, cancelAppointment } from './api/client';

export function App() {
  const [doctors, setDoctors] = useState([]);
  const [appointments, setAppointments] = useState([]);
  const [highlightedIds, setHighlightedIds] = useState({});
  const [transcripts, setTranscripts] = useState([]);
  const [latestBooking, setLatestBooking] = useState(null);
  const [isCallModalOpen, setIsCallModalOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  // Dedup ref: map of "role:text" → timestamp, cleared after 3s
  const seenTranscriptsRef = useRef(new Map());

  // Load initial data
  const refreshData = useCallback(async () => {
    try {
      const [docsRes, apptsRes] = await Promise.all([
        getDoctors(),
        getAppointments(),
      ]);
      if (docsRes?.doctors) setDoctors(docsRes.doctors);
      if (apptsRes?.appointments) setAppointments(apptsRes.appointments);
    } catch (err) {
      console.error('Error refreshing clinic data:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshData();
  }, [refreshData]);

  // Handle live Server-Sent Events (SSE)
  const handleLiveEvent = useCallback((event) => {
    const { type, data } = event;

    /**
     * Dedup helper: returns true if this (role, text) was already seen within
     * the last 3 seconds (guards against SSE reconnect replays and backend
     * emitting the same transcript multiple times).
     */
    function isDuplicate(role, text) {
      const key = `${role}:${text.trim().toLowerCase()}`;
      const now = Date.now();
      const seen = seenTranscriptsRef.current;
      // Purge stale entries
      for (const [k, ts] of seen.entries()) {
        if (now - ts > 3000) seen.delete(k);
      }
      if (seen.has(key)) return true;
      seen.set(key, now);
      return false;
    }

    if (type === 'caller_transcript') {
      if (data?.text) {
        const trimmed = data.text.trim();
        if (!isDuplicate('user', trimmed)) {
          setTranscripts((prev) => [...prev, { role: 'user', text: trimmed }]);
        }
      }
    } else if (type === 'agent_transcript') {
      if (data?.text) {
        const trimmed = data.text.trim();
        if (!isDuplicate('agent', trimmed)) {
          setTranscripts((prev) => [...prev, { role: 'agent', text: trimmed }]);
        }
      }
    } else if (type === 'appointment_booked') {
      if (data?.appointment_id) {
        const apptId = data.appointment_id;
        setLatestBooking(data);
        setHighlightedIds((prev) => ({ ...prev, [apptId]: 'booked' }));

        // Clear highlight after 3 seconds
        setTimeout(() => {
          setHighlightedIds((prev) => {
            const next = { ...prev };
            delete next[apptId];
            return next;
          });
        }, 3000);

        refreshData();
      }
    } else if (type === 'appointment_cancelled') {
      if (data?.appointment_id) {
        const apptId = data.appointment_id;
        setHighlightedIds((prev) => ({ ...prev, [apptId]: 'cancelled' }));

        setTimeout(() => {
          setHighlightedIds((prev) => {
            const next = { ...prev };
            delete next[apptId];
            return next;
          });
        }, 3000);

        refreshData();
      }
    }
  }, [refreshData]);

  const { connectionStatus } = useSSE(handleLiveEvent);
  const webrtc = useWebRTC();

  // Direct cancel appointment action from the table
  const handleCancelAppointment = async (phone, apptId) => {
    try {
      await cancelAppointment(phone, apptId);
      refreshData();
    } catch (err) {
      alert(`Could not cancel appointment: ${err.message}`);
    }
  };

  const resetCallSession = useCallback(() => {
    setTranscripts([]);
    setLatestBooking(null);
    seenTranscriptsRef.current.clear();
  }, []);

  const handleOpenCallModal = () => {
    setIsCallModalOpen(true);
  };

  const handleCloseCallModal = () => {
    setIsCallModalOpen(false);
    if (webrtc.callState === 'ended') {
      webrtc.resetCall();
      resetCallSession();
    }
  };

  const openSlotsCount = doctors.reduce(
    (sum, doc) => sum + (doc.slots ? doc.slots.filter((s) => s.is_available).length : 0),
    0
  );
  const confirmedCount = appointments.filter((a) => a.status === 'CONFIRMED').length;

  return (
    <div className="min-h-screen flex flex-col text-slate-800 relative">
      {/* Top Bar Header */}
      <TopBar connectionStatus={connectionStatus} />

      {/* Main Content Dashboard */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        
        {/* Hospital Reception Desk Welcome Banner */}
        <section className="mb-6 relative overflow-hidden rounded-2xl bg-gradient-to-r from-teal-900 via-teal-800 to-cyan-900 text-white shadow-lg border border-teal-700/60">
          {/* Subtle architectural atrium lighting */}
          <div className="pointer-events-none absolute -right-12 -top-12 w-56 h-56 rounded-full bg-teal-400/15 blur-2xl" />
          <div className="pointer-events-none absolute left-1/3 -bottom-16 w-64 h-64 rounded-full bg-cyan-300/10 blur-2xl" />

          <div className="relative px-5 py-5 sm:px-7 sm:py-6 flex flex-col lg:flex-row lg:items-center lg:justify-between gap-5">
            <div>
              <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-white/10 border border-white/15 text-teal-100 text-[11px] font-medium tracking-wide mb-2.5">
                <Building2 className="w-3.5 h-3.5 text-teal-200" />
                <span>Main Hospital Reception · Ground Floor Check-In &amp; Scheduling</span>
              </div>
              <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-white">
                Metro Health Clinic Reception Desk
              </h2>
              <p className="text-xs sm:text-sm text-teal-100/90 mt-1 max-w-2xl">
                Speak directly with Chloe, our AI reception desk coordinator, to check specialist availability, book visits, or manage existing appointments.
              </p>

              {/* Live Reception Desk Counters */}
              <div className="mt-4 flex flex-wrap items-center gap-2.5 text-xs">
                <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/10 border border-white/15 text-teal-50">
                  <Stethoscope className="w-3.5 h-3.5 text-teal-200" />
                  <span className="font-semibold">{doctors.length}</span>
                  <span className="text-teal-100/80">Specialists On Duty</span>
                </div>
                <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/10 border border-white/15 text-teal-50">
                  <Clock className="w-3.5 h-3.5 text-emerald-300" />
                  <span className="font-semibold">{openSlotsCount}</span>
                  <span className="text-teal-100/80">Open Slots</span>
                </div>
                <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/10 border border-white/15 text-teal-50">
                  <CalendarCheck2 className="w-3.5 h-3.5 text-cyan-200" />
                  <span className="font-semibold">{confirmedCount}</span>
                  <span className="text-teal-100/80">Confirmed Visits</span>
                </div>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row lg:flex-col items-stretch sm:items-center lg:items-end gap-2.5 shrink-0">
              <button
                onClick={handleOpenCallModal}
                className="inline-flex items-center justify-center gap-2 px-5 py-3 rounded-xl bg-white text-teal-900 hover:bg-teal-50 text-xs font-bold tracking-wide shadow-md transition-all"
              >
                <PhoneCall className="w-4 h-4 text-teal-700" />
                <span>{webrtc.callState === 'connected' ? 'Return to Reception Call' : 'Call Reception Desk'}</span>
              </button>
              <span className="text-[11px] text-teal-100/80 text-center lg:text-right">
                Live WebRTC Voice · Instant DB Sync
              </span>
            </div>
          </div>
        </section>

        {/* Two-Column Dashboard */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          
          {/* Left Column: Doctors & Available Slots (7 cols on lg) */}
          <div className="lg:col-span-7">
            <DoctorsList doctors={doctors} isLoading={isLoading} />
          </div>

          {/* Right Column: Appointments List (5 cols on lg) */}
          <div className="lg:col-span-5">
            <AppointmentsList
              appointments={appointments}
              highlightedIds={highlightedIds}
              onCancelAppointment={handleCancelAppointment}
              isLoading={isLoading}
            />
          </div>

        </div>
      </main>

      {/* Phone-Style Call Modal */}
      <PhoneModal
        isOpen={isCallModalOpen}
        onClose={handleCloseCallModal}
        webrtc={webrtc}
        transcripts={transcripts}
        latestBooking={latestBooking}
        onResetSession={resetCallSession}
      />
    </div>
  );
}

export default App;
