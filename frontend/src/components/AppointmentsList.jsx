import React, { useState } from 'react';
import { CalendarCheck, User, Stethoscope, Clock, Calendar, XCircle } from 'lucide-react';

/**
 * Appointments list column.
 * Displays appointments with caller phone number, doctor, time, and status.
 * Automatically highlights newly booked or cancelled rows in real time.
 */
export function AppointmentsList({
  appointments,
  highlightedIds,
  onCancelAppointment,
  isLoading,
}) {
  const [filter, setFilter] = useState('all'); // 'all' | 'confirmed' | 'cancelled'

  const filteredAppointments = appointments.filter((appt) => {
    if (filter === 'confirmed') return appt.status === 'CONFIRMED';
    if (filter === 'cancelled') return appt.status === 'CANCELLED';
    return true;
  });

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-xs flex flex-col h-full">
      {/* Header */}
      <div className="px-5 py-4 border-b border-slate-100 flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-sm font-semibold text-slate-900 tracking-tight">
              Patient Appointments
            </h2>
            <span className="text-[11px] font-medium text-slate-700 bg-slate-100 border border-slate-200 px-2 py-0.5 rounded-full">
              {appointments.length} Total
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Real-time feed synced with voice receptionist
          </p>
        </div>

        {/* Status Filter */}
        <div className="flex items-center bg-slate-50 border border-slate-200 p-0.5 rounded-lg text-xs font-medium">
          <button
            onClick={() => setFilter('all')}
            className={`px-2.5 py-1 rounded-md transition-all ${
              filter === 'all'
                ? 'bg-white text-slate-900 shadow-xs font-semibold'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            All
          </button>
          <button
            onClick={() => setFilter('confirmed')}
            className={`px-2.5 py-1 rounded-md transition-all ${
              filter === 'confirmed'
                ? 'bg-white text-slate-900 shadow-xs font-semibold'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Confirmed
          </button>
          <button
            onClick={() => setFilter('cancelled')}
            className={`px-2.5 py-1 rounded-md transition-all ${
              filter === 'cancelled'
                ? 'bg-white text-slate-900 shadow-xs font-semibold'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Cancelled
          </button>
        </div>
      </div>

      {/* Appointments List Body */}
      <div className="p-5 space-y-3 overflow-y-auto max-h-[calc(100vh-14rem)]">
        {isLoading ? (
          <div className="py-12 text-center text-xs text-slate-400">
            Loading appointments...
          </div>
        ) : filteredAppointments.length === 0 ? (
          <div className="py-16 text-center">
            <CalendarCheck className="w-8 h-8 text-slate-300 mx-auto mb-2 stroke-[1.5]" />
            <p className="text-xs font-medium text-slate-600">
              No appointments recorded
            </p>
            <p className="text-[11px] text-slate-400 mt-0.5">
              Click "Try Call" to book an appointment with Chloe via voice.
            </p>
          </div>
        ) : (
          filteredAppointments.map((appt) => {
            const isConfirmed = appt.status === 'CONFIRMED';
            const highlightType = highlightedIds[appt.appointment_id]; // 'booked' | 'cancelled' | undefined

            let highlightClass = '';
            if (highlightType === 'booked') {
              highlightClass = 'animate-highlight-booked ring-2 ring-teal-400/50';
            } else if (highlightType === 'cancelled') {
              highlightClass = 'animate-highlight-cancelled ring-2 ring-red-400/50';
            }

            return (
              <div
                key={appt.appointment_id || appt.id}
                className={`p-3.5 rounded-xl border border-slate-200/90 bg-white transition-all shadow-xs ${highlightClass}`}
              >
                <div className="flex items-start justify-between gap-3">
                  {/* Left: Patient name and Doctor */}
                  <div className="space-y-1">
                    <div className="flex items-center gap-1.5">
                      <User className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                      <span className="text-xs font-semibold text-slate-900">
                        {appt.patient_name || 'Patient'}
                      </span>
                    </div>

                    <div className="flex items-center gap-1.5 text-xs text-slate-700">
                      <Stethoscope className="w-3.5 h-3.5 text-teal-600 shrink-0" />
                      <span className="font-medium">{appt.doctor_name}</span>
                      <span className="text-slate-400">· {appt.specialty}</span>
                    </div>

                    <div className="flex items-center gap-3 text-[11px] text-slate-500 pt-0.5">
                      <span className="flex items-center gap-1">
                        <Calendar className="w-3 h-3 text-slate-400" />
                        {appt.appointment_date || appt.date}
                      </span>
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3 text-slate-400" />
                        {appt.time_slot}
                      </span>
                    </div>
                  </div>

                  {/* Right: Status badge & Action */}
                  <div className="flex flex-col items-end gap-2">
                    <span
                      className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${
                        isConfirmed
                          ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                          : 'bg-slate-100 text-slate-500 border-slate-200 line-through'
                      }`}
                    >
                      {appt.status}
                    </span>

                    <span className="text-[10px] font-mono text-slate-400">
                      {appt.appointment_id}
                    </span>

                    {isConfirmed && onCancelAppointment && (
                      <button
                        onClick={() => onCancelAppointment(appt.phone_number, appt.appointment_id)}
                        className="text-[10px] font-medium text-slate-400 hover:text-red-600 transition-colors flex items-center gap-1 pt-0.5"
                        title="Cancel this appointment"
                      >
                        <XCircle className="w-3 h-3" />
                        <span>Cancel</span>
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
