import React, { useEffect, useRef, useState } from 'react';
import {
  Phone,
  PhoneOff,
  Mic,
  MicOff,
  X,
  Volume2,
  Sparkles,
  User,
  Bot,
  Activity,
} from 'lucide-react';
import { AudioWaveform } from './AudioWaveform';
import { BookingCard } from './BookingCard';
import { useAudioTones } from '../hooks/useAudioTones';

/**
 * Phone-style Call Modal mimicking a clinical mobile handset interface.
 * Connects WebRTC audio, streams transcripts, displays waveforms, and shows booking cards.
 */
export function PhoneModal({
  isOpen,
  onClose,
  webrtc,
  transcripts,
  latestBooking,
  onResetSession,
}) {
  const { callState, isMuted, analyser, startCall, endCall, toggleMute, errorMessage } = webrtc;
  const { playRingTone, playHangupTone, playBookingChime, stopAll } = useAudioTones();

  const [callDuration, setCallDuration] = useState(0);
  const transcriptBottomRef = useRef(null);
  const lastStateRef = useRef(callState);

  // Auto-scroll transcript container
  useEffect(() => {
    transcriptBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [transcripts, latestBooking]);

  // Handle ringtones and call timer
  useEffect(() => {
    let timer = null;

    if (callState === 'connecting') {
      playRingTone();
    } else if (callState === 'connected') {
      stopAll();
      timer = setInterval(() => {
        setCallDuration((prev) => prev + 1);
      }, 1000);
    } else if (callState === 'ended') {
      stopAll();
      if (lastStateRef.current === 'connected') {
        playHangupTone();
      }
    }

    lastStateRef.current = callState;

    return () => {
      if (timer) clearInterval(timer);
      stopAll();
    };
  }, [callState, playRingTone, playHangupTone, stopAll]);

  // Play chime when new booking arrives during call
  useEffect(() => {
    if (latestBooking && callState === 'connected') {
      playBookingChime();
    }
  }, [latestBooking, callState, playBookingChime]);

  // Reset duration on start
  useEffect(() => {
    if (isOpen && callState === 'idle') {
      setCallDuration(0);
      startCall();
    }
  }, [isOpen, callState, startCall]);

  if (!isOpen) return null;

  const formatTimer = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const handleHangup = () => {
    endCall();
  };

  const handleRestart = () => {
    onResetSession?.();
    setCallDuration(0);
    startCall();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm animate-fade-in">
      {/* Handset Frame */}
      <div className="relative w-full max-w-[360px] bg-slate-900 rounded-[2.5rem] p-3.5 shadow-2xl border-4 border-slate-700/80 flex flex-col items-center">
        
        {/* Phone Top Notch / Speaker slit */}
        <div className="w-full flex items-center justify-center pt-1 pb-2">
          <div className="w-16 h-1 bg-slate-700 rounded-full"></div>
        </div>

        {/* Close Button top-right */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-slate-400 hover:text-white transition-colors p-1"
          title="Minimize / Close"
        >
          <X className="w-4 h-4" />
        </button>

        {/* Inner Phone Screen */}
        <div className="w-full bg-[#FAFAFA] rounded-[1.8rem] flex flex-col h-[560px] border border-slate-200 shadow-inner overflow-hidden">
          
          {/* Header Info Area */}
          <div className="pt-6 pb-3 px-4 bg-white border-b border-slate-100 flex flex-col items-center text-center">
            
            {/* Receptionist Avatar */}
            <div className="w-12 h-12 rounded-full bg-teal-50 border border-teal-200 flex items-center justify-center text-teal-700 mb-2 shadow-xs">
              <Bot className="w-6 h-6 stroke-[1.8]" />
            </div>

            <h3 className="text-sm font-semibold text-slate-900">
              Chloe — Clinic Receptionist
            </h3>

            {/* Call State & Live Timer */}
            <div className="flex items-center gap-2 mt-1">
              {callState === 'connecting' && (
                <span className="text-xs text-amber-600 font-medium animate-pulse flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-amber-500 animate-ping"></span>
                  Connecting audio...
                </span>
              )}
              {callState === 'connected' && (
                <span className="text-xs text-emerald-700 font-mono font-medium flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                  {formatTimer(callDuration)}
                </span>
              )}
              {callState === 'ended' && (
                <span className="text-xs text-slate-500 font-medium">
                  Call Ended
                </span>
              )}
            </div>

            {/* Live Audio Waveform */}
            <div className="w-full mt-1">
              <AudioWaveform
                analyser={analyser}
                isActive={callState === 'connected'}
                isMuted={isMuted}
              />
            </div>
          </div>

          {/* Transcript & Messages Display Area */}
          <div className="flex-1 p-3.5 overflow-y-auto transcript-scroll flex flex-col gap-2.5">
            {transcripts.length === 0 ? (
              <div className="my-auto text-center px-4">
                <p className="text-xs text-slate-600 font-medium">
                  {callState === 'connecting'
                    ? 'Establishing secure WebRTC channel...'
                    : callState === 'connected'
                    ? 'Speak naturally to book or cancel an appointment.'
                    : 'Call has ended.'}
                </p>
                <p className="text-[11px] text-slate-400 mt-1">
                  Example: "I'd like to book an appointment with Dr. Chen for tomorrow."
                </p>
              </div>
            ) : (
              transcripts.map((item, idx) => {
                const isUser = item.role === 'user';
                return (
                  <div
                    key={idx}
                    className={`flex flex-col ${isUser ? 'items-end' : 'items-start'} max-w-[88%] ${isUser ? 'self-end' : 'self-start'}`}
                  >
                    <span className="text-[9px] font-medium text-slate-400 mb-0.5 px-1">
                      {isUser ? 'You' : 'Chloe'}
                    </span>
                    <div
                      className={`px-3 py-2 rounded-2xl text-xs leading-relaxed ${
                        isUser
                          ? 'bg-teal-700 text-white rounded-br-xs'
                          : 'bg-white border border-slate-200 text-slate-800 rounded-bl-xs shadow-xs'
                      }`}
                    >
                      {item.text}
                    </div>
                  </div>
                );
              })
            )}

            {/* Booking Card Display Inside Phone Screen */}
            {latestBooking && (
              <div className="w-full">
                <BookingCard booking={latestBooking} />
              </div>
            )}

            {errorMessage && (
              <div className="p-2.5 rounded-lg bg-red-50 border border-red-200 text-[11px] text-red-700 text-center">
                {errorMessage}
              </div>
            )}

            <div ref={transcriptBottomRef} />
          </div>

          {/* Bottom Action Controls */}
          <div className="p-4 bg-white border-t border-slate-100 flex items-center justify-around">
            {callState !== 'ended' ? (
              <>
                {/* Mute Button */}
                <button
                  onClick={toggleMute}
                  disabled={callState !== 'connected'}
                  className={`w-12 h-12 rounded-full flex items-center justify-center transition-all ${
                    isMuted
                      ? 'bg-red-100 text-red-700 border border-red-200'
                      : 'bg-slate-100 hover:bg-slate-200 text-slate-700'
                  }`}
                  title={isMuted ? 'Unmute microphone' : 'Mute microphone'}
                >
                  {isMuted ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
                </button>

                {/* Hangup Button */}
                <button
                  onClick={handleHangup}
                  className="w-14 h-14 rounded-full bg-red-600 hover:bg-red-700 text-white flex items-center justify-center shadow-md hover:shadow-lg transition-all"
                  title="End Call"
                >
                  <PhoneOff className="w-6 h-6" />
                </button>
              </>
            ) : (
              /* Call Ended / Call Again Button */
              <button
                onClick={handleRestart}
                className="w-full py-3 px-4 rounded-xl bg-teal-700 hover:bg-teal-800 text-white text-xs font-semibold flex items-center justify-center gap-2 shadow-sm transition-all"
              >
                <Phone className="w-4 h-4" />
                <span>Call Clinic Again</span>
              </button>
            )}
          </div>

        </div>

        {/* Phone Bottom Pill bar */}
        <div className="pt-2 pb-1">
          <div className="w-24 h-1 bg-slate-700 rounded-full"></div>
        </div>

      </div>
    </div>
  );
}
