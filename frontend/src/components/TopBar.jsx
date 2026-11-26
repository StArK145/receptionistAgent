import React from 'react';
import { HeartPulse } from 'lucide-react';

/**
 * Top bar header with clinical title and real-time sync badge.
 */
export function TopBar({ connectionStatus }) {
  return (
    <header className="sticky top-0 z-30 bg-white/90 backdrop-blur-md border-b border-slate-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        
        {/* Brand / Clinic Title */}
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-teal-50 border border-teal-200 flex items-center justify-center text-teal-700 shadow-xs">
            <HeartPulse className="w-5 h-5 stroke-[2.2]" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-base font-semibold tracking-tight text-slate-900 leading-tight">
                Metro Health Clinic
              </h1>
              <span className="hidden sm:inline-block text-[11px] font-medium text-slate-500 bg-slate-100 border border-slate-200 px-2 py-0.5 rounded-full">
                Voice Assistant
              </span>
            </div>
            <p className="text-xs text-slate-500 hidden sm:block">
              Cardiology · Dermatology · Pediatrics · Orthopedics · General Medicine
            </p>
          </div>
        </div>

        {/* Status Badge */}
        <div className="flex items-center gap-4">
          {/* Connection Status Badge */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium bg-slate-50 border border-slate-200">
            <span className="relative flex h-2 w-2">
              {connectionStatus === 'connected' ? (
                <>
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                </>
              ) : connectionStatus === 'connecting' ? (
                <span className="relative inline-flex rounded-full h-2 w-2 bg-amber-400"></span>
              ) : (
                <span className="relative inline-flex rounded-full h-2 w-2 bg-slate-400"></span>
              )}
            </span>
            <span className="text-slate-600">
              {connectionStatus === 'connected'
                ? 'Live Sync'
                : connectionStatus === 'connecting'
                ? 'Connecting...'
                : 'Offline'}
            </span>
          </div>
        </div>

      </div>
    </header>
  );
}
