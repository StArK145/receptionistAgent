import React from 'react';
import { CheckCircle2, Calendar, Clock, Stethoscope, Phone } from 'lucide-react';

/**
 * Compact confirmation card displayed inside the phone modal when an appointment is booked.
 */
export function BookingCard({ booking }) {
  if (!booking) return null;

  return (
    <div className="bg-teal-50/90 border border-teal-200/90 rounded-xl p-3 my-2 text-left shadow-sm backdrop-blur-sm animate-fade-in transition-all">
      <div className="flex items-center gap-2 mb-2 pb-1.5 border-b border-teal-100">
        <CheckCircle2 className="w-4 h-4 text-teal-600 shrink-0" />
        <span className="text-xs font-semibold text-teal-900 tracking-wide">
          Appointment Confirmed
        </span>
        <span className="ml-auto text-[10px] font-mono font-medium text-teal-700 bg-teal-100/80 px-1.5 py-0.5 rounded">
          {booking.appointment_id}
        </span>
      </div>

      <div className="space-y-1 text-[11px] text-slate-700">
        <div className="flex items-center gap-1.5 font-medium text-slate-900">
          <Stethoscope className="w-3.5 h-3.5 text-teal-600 shrink-0" />
          <span>{booking.doctor_name}</span>
          <span className="text-slate-400 font-normal">· {booking.specialty}</span>
        </div>

        <div className="flex items-center gap-1.5 text-slate-600">
          <Calendar className="w-3.5 h-3.5 text-slate-400 shrink-0" />
          <span>{booking.date}</span>
          <Clock className="w-3.5 h-3.5 text-slate-400 shrink-0 ml-1.5" />
          <span>{booking.time_slot}</span>
        </div>

        <div className="flex items-center gap-1.5 text-slate-500 pt-0.5">
          <Phone className="w-3.5 h-3.5 text-slate-400 shrink-0" />
          <span className="font-mono text-[10px]">{booking.phone_number}</span>
          {booking.patient_name && (
            <span className="ml-auto text-[10px] text-slate-600 font-medium truncate max-w-[100px]">
              {booking.patient_name}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
