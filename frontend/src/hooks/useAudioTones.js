import { useRef, useCallback } from 'react';

/**
 * Hook to play subtle synthesized phone tones using the standard Web Audio API.
 * No external mp3/wav files required.
 */
export function useAudioTones() {
  const ctxRef = useRef(null);
  const ringIntervalRef = useRef(null);

  const getAudioContext = useCallback(() => {
    if (!ctxRef.current) {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (AudioCtx) {
        ctxRef.current = new AudioCtx();
      }
    }
    if (ctxRef.current && ctxRef.current.state === 'suspended') {
      ctxRef.current.resume();
    }
    return ctxRef.current;
  }, []);

  const stopAll = useCallback(() => {
    if (ringIntervalRef.current) {
      clearInterval(ringIntervalRef.current);
      ringIntervalRef.current = null;
    }
  }, []);

  // Subtle US standard ringback tone (440Hz + 480Hz)
  const playRingTone = useCallback(() => {
    stopAll();
    const ctx = getAudioContext();
    if (!ctx) return;

    const playBurst = () => {
      try {
        const osc1 = ctx.createOscillator();
        const osc2 = ctx.createOscillator();
        const gain = ctx.createGain();

        osc1.frequency.value = 440;
        osc2.frequency.value = 480;

        gain.gain.setValueAtTime(0.04, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 1.4);

        osc1.connect(gain);
        osc2.connect(gain);
        gain.connect(ctx.destination);

        osc1.start();
        osc2.start();
        osc1.stop(ctx.currentTime + 1.4);
        osc2.stop(ctx.currentTime + 1.4);
      } catch (err) {
        console.warn('Audio tone error:', err);
      }
    };

    playBurst();
    ringIntervalRef.current = setInterval(playBurst, 3000);
  }, [getAudioContext, stopAll]);

  // Subtle hangup / disconnect tone (480Hz + 620Hz, 3 quick beeps)
  const playHangupTone = useCallback(() => {
    stopAll();
    const ctx = getAudioContext();
    if (!ctx) return;

    try {
      [0, 0.25, 0.5].forEach((offset) => {
        const osc1 = ctx.createOscillator();
        const osc2 = ctx.createOscillator();
        const gain = ctx.createGain();

        osc1.frequency.value = 480;
        osc2.frequency.value = 620;

        gain.gain.setValueAtTime(0.05, ctx.currentTime + offset);
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + offset + 0.18);

        osc1.connect(gain);
        osc2.connect(gain);
        gain.connect(ctx.destination);

        osc1.start(ctx.currentTime + offset);
        osc2.start(ctx.currentTime + offset);
        osc1.stop(ctx.currentTime + offset + 0.18);
        osc2.stop(ctx.currentTime + offset + 0.18);
      });
    } catch (err) {
      console.warn('Hangup tone error:', err);
    }
  }, [getAudioContext, stopAll]);

  // Gentle confirmation chime when booking succeeds
  const playBookingChime = useCallback(() => {
    const ctx = getAudioContext();
    if (!ctx) return;

    try {
      const notes = [523.25, 659.25, 783.99]; // C5, E5, G5
      notes.forEach((freq, i) => {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'sine';
        osc.frequency.value = freq;

        const startTime = ctx.currentTime + i * 0.12;
        gain.gain.setValueAtTime(0.06, startTime);
        gain.gain.exponentialRampToValueAtTime(0.0001, startTime + 0.4);

        osc.connect(gain);
        gain.connect(ctx.destination);

        osc.start(startTime);
        osc.stop(startTime + 0.4);
      });
    } catch (err) {
      console.warn('Booking chime error:', err);
    }
  }, [getAudioContext]);

  return {
    playRingTone,
    playHangupTone,
    playBookingChime,
    stopAll,
  };
}
