import React, { useState } from 'react';
import { Stethoscope, Calendar, Clock, Check, X, Building2 } from 'lucide-react';

/**
 * Doctors & Available Slots column.
 * Clean, calm clinical design showing doctors, specialties, and time slot availability.
 */
export function DoctorsList({ doctors, isLoading }) {
  const [selectedDateFilter, setSelectedDateFilter] = useState('all'); // 'all' | 'today' | 'tomorrow'

  // Extract unique dates from slots
  const allDates = Array.from(
    new Set(
      doctors.flatMap((doc) => doc.slots.map((s) => s.date))
    )
  ).sort();

  const todayStr = allDates[0] || '';
  const tomorrowStr = allDates[1] || '';

  const filteredDoctors = doctors.map((doc) => {
    let slots = doc.slots;
    if (selectedDateFilter === 'today') {
      slots = slots.filter((s) => s.date === todayStr);
    } else if (selectedDateFilter === 'tomorrow') {
      slots = slots.filter((s) => s.date === tomorrowStr);
    }
    return { ...doc, filteredSlots: slots };
  });

  const totalOpenSlots = filteredDoctors.reduce(
    (acc, doc) => acc + doc.filteredSlots.filter((s) => s.is_available).length,
    0
  );

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-xs flex flex-col h-full">
      {/* Header */}
      <div className="px-5 py-4 border-b border-slate-100 flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-sm font-semibold text-slate-900 tracking-tight">
              Doctors & Availability
            </h2>
            <span className="text-[11px] font-medium text-teal-700 bg-teal-50 border border-teal-200 px-2 py-0.5 rounded-full">
              {totalOpenSlots} Open Slots
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Real-time schedule for today and tomorrow
          </p>
        </div>

        {/* Date Filter Tabs */}
        <div className="flex items-center bg-slate-50 border border-slate-200 p-0.5 rounded-lg text-xs font-medium">
          <button
            onClick={() => setSelectedDateFilter('all')}
            className={`px-2.5 py-1 rounded-md transition-all ${
              selectedDateFilter === 'all'
                ? 'bg-white text-slate-900 shadow-xs font-semibold'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            All Dates
          </button>
          <button
            onClick={() => setSelectedDateFilter('today')}
            className={`px-2.5 py-1 rounded-md transition-all ${
              selectedDateFilter === 'today'
                ? 'bg-white text-slate-900 shadow-xs font-semibold'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Today
          </button>
          <button
            onClick={() => setSelectedDateFilter('tomorrow')}
            className={`px-2.5 py-1 rounded-md transition-all ${
              selectedDateFilter === 'tomorrow'
                ? 'bg-white text-slate-900 shadow-xs font-semibold'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Tomorrow
          </button>
        </div>
      </div>

      {/* Body / Doctors list */}
      <div className="p-5 space-y-4 overflow-y-auto max-h-[calc(100vh-14rem)]">
        {isLoading ? (
          <div className="py-12 text-center text-xs text-slate-400">
            Loading clinic roster...
          </div>
        ) : filteredDoctors.length === 0 ? (
          <div className="py-12 text-center text-xs text-slate-400">
            No doctors found matching criteria.
          </div>
        ) : (
          filteredDoctors.map((doc) => {
            const openCount = doc.filteredSlots.filter((s) => s.is_available).length;
            const bookedCount = doc.filteredSlots.length - openCount;

            return (
              <div
                key={doc.id}
                className="p-4 rounded-xl border border-slate-200/90 hover:border-slate-300 bg-white transition-all shadow-xs"
              >
                {/* Doctor Header */}
                <div className="flex items-start justify-between gap-2 mb-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-sm font-semibold text-slate-900">
                        {doc.name}
                      </h3>
                      <span className="text-[11px] font-medium text-slate-700 bg-slate-100 border border-slate-200 px-2 py-0.5 rounded-full">
                        {doc.specialty}
                      </span>
                    </div>
                    <div className="flex items-center gap-1.5 text-xs text-slate-500 mt-0.5">
                      <Building2 className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                      <span>{doc.hospital_or_clinic}</span>
                    </div>
                  </div>

                  <span className="text-[11px] font-mono font-medium text-slate-500 bg-slate-50 px-2 py-0.5 rounded border border-slate-100">
                    {openCount} open / {doc.filteredSlots.length}
                  </span>
                </div>

                {/* Slots Grid */}
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-1.5 pt-1">
                  {doc.filteredSlots.map((slot) => {
                    const isAvailable = slot.is_available;
                    const dateLabel =
                      slot.date === todayStr
                        ? 'Today'
                        : slot.date === tomorrowStr
                        ? 'Tomorrow'
                        : slot.date;

                    return (
                      <div
                        key={slot.slot_id}
                        className={`px-2.5 py-1.5 rounded-lg border text-xs flex items-center justify-between transition-all ${
                          isAvailable
                            ? 'bg-slate-50/70 border-slate-200/90 text-slate-700 hover:border-teal-300 hover:bg-teal-50/40'
                            : 'bg-slate-100/60 border-slate-200/50 text-slate-400 line-through'
                        }`}
                      >
                        <div className="flex flex-col">
                          <span className="font-mono text-[11px] font-medium">
                            {slot.time_slot}
                          </span>
                          <span className="text-[9px] text-slate-400 no-underline">
                            {dateLabel}
                          </span>
                        </div>
                        {isAvailable ? (
                          <span className="text-[10px] font-medium text-teal-700 bg-teal-50 px-1 rounded">
                            Open
                          </span>
                        ) : (
                          <span className="text-[9px] text-slate-400 no-underline">
                            Booked
                          </span>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
