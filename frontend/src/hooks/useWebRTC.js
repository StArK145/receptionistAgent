import { useState, useRef, useCallback, useEffect } from 'react';
import { sendWebRTCOffer } from '../api/client';

/**
 * Hook to manage browser WebRTC audio streaming, peer connection,
 * microphone track muting, and Web Audio API analyser levels for waveforms.
 */
export function useWebRTC({ onRemoteTrack, onError } = {}) {
  const [callState, setCallState] = useState('idle'); // 'idle' | 'connecting' | 'connected' | 'ended'
  const [isMuted, setIsMuted] = useState(false);
  const [analyser, setAnalyser] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);

  const pcRef = useRef(null);
  const localStreamRef = useRef(null);
  const audioContextRef = useRef(null);
  const remoteAudioRef = useRef(null);

  // Initialize a hidden audio element for remote agent audio playback
  useEffect(() => {
    const audioEl = new Audio();
    audioEl.autoplay = true;
    audioEl.playsInline = true;
    remoteAudioRef.current = audioEl;

    return () => {
      audioEl.pause();
      audioEl.srcObject = null;
    };
  }, []);

  const cleanup = useCallback(() => {
    if (pcRef.current) {
      pcRef.current.close();
      pcRef.current = null;
    }

    if (localStreamRef.current) {
      localStreamRef.current.getTracks().forEach((t) => t.stop());
      localStreamRef.current = null;
    }

    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      try {
        audioContextRef.current.close();
      } catch (e) {
        // Ignored
      }
      audioContextRef.current = null;
    }

    if (remoteAudioRef.current) {
      remoteAudioRef.current.pause();
      remoteAudioRef.current.srcObject = null;
    }

    setAnalyser(null);
  }, []);

  const startCall = useCallback(async () => {
    cleanup();
    setIsMuted(false);
    setErrorMessage(null);
    setCallState('connecting');

    try {
      // 1. Request microphone access (ideal mono voice avoids laptop stereo-array phase cancellation)
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          channelCount: { ideal: 1 },
          sampleRate: { ideal: 48000 },
        },
      });
      localStreamRef.current = stream;

      // 2. Setup Web Audio API Analyser for real-time waveform reactivity
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      const ctx = new AudioCtx();
      if (ctx.state === 'suspended') {
        await ctx.resume();
      }
      audioContextRef.current = ctx;

      const source = ctx.createMediaStreamSource(stream);
      const analyserNode = ctx.createAnalyser();
      analyserNode.fftSize = 64;
      analyserNode.smoothingTimeConstant = 0.8;
      source.connect(analyserNode);
      setAnalyser(analyserNode);

      // 3. Create WebRTC PeerConnection
      const pc = new RTCPeerConnection({
        iceServers: [{ urls: 'stun:stun.l.google.com:19302' }],
      });
      pcRef.current = pc;

      // Add local audio track (ensure enabled)
      stream.getAudioTracks().forEach((track) => {
        track.enabled = true;
        console.info('Mic track:', track.label, track.getSettings?.());
        pc.addTrack(track, stream);
      });

      // Create WebRTC DataChannel expected by SmallWebRTC for control messages
      try {
        const dc = pc.createDataChannel('data');
        dc.onopen = () => console.log('WebRTC DataChannel opened');
        dc.onmessage = (e) => console.log('DataChannel message:', e.data);
      } catch (e) {
        console.warn('Could not create DataChannel:', e);
      }

      // Handle incoming remote audio track from Pipecat bot
      pc.ontrack = (event) => {
        const remoteStream = event.streams?.[0] || (event.track ? new MediaStream([event.track]) : null);
        if (remoteAudioRef.current && remoteStream) {
          remoteAudioRef.current.srcObject = remoteStream;
          remoteAudioRef.current.play().catch((err) => {
            console.warn('Autoplay blocked; waiting for user interaction', err);
          });
        }
        if (onRemoteTrack) {
          onRemoteTrack(event);
        }
      };

      let statsLogged = false;
      pc.onconnectionstatechange = () => {
        if (pc.connectionState === 'connected') {
          setCallState('connected');
          if (!statsLogged) {
            statsLogged = true;
            setTimeout(async () => {
              if (pcRef.current !== pc || pc.connectionState !== 'connected') return;
              try {
                const st = await pc.getStats();
                st.forEach((r) => {
                  if (r.type === 'outbound-rtp' && r.kind === 'audio') {
                    console.info('WebRTC outbound-rtp:', { packetsSent: r.packetsSent, bytesSent: r.bytesSent, targetBitrate: r.targetBitrate });
                  } else if (r.type === 'media-source' && r.kind === 'audio') {
                    console.info('WebRTC media-source:', { audioLevel: r.audioLevel, totalSamplesDuration: r.totalSamplesDuration });
                  }
                });
              } catch { /* ignore */ }
            }, 3500);
          }
        } else if (['failed', 'closed'].includes(pc.connectionState)) {
          setCallState('ended');
        }
      };

      pc.oniceconnectionstatechange = () => {
        if (pc.iceConnectionState === 'connected' || pc.iceConnectionState === 'completed') {
          setCallState('connected');
        } else if (pc.iceConnectionState === 'failed' || pc.iceConnectionState === 'closed') {
          setCallState('ended');
        }
      };

      // 4. Create offer and send to FastAPI /api/offer
      const offer = await pc.createOffer();
      await pc.setLocalDescription(offer);

      // Wait briefly for ICE gathering
      await new Promise((resolve) => {
        if (pc.iceGatheringState === 'complete') {
          resolve();
        } else {
          const checkState = () => {
            if (pc.iceGatheringState === 'complete') {
              pc.removeEventListener('icegatheringstatechange', checkState);
              resolve();
            }
          };
          pc.addEventListener('icegatheringstatechange', checkState);
          setTimeout(resolve, 1000); // Max 1s wait
        }
      });

      const sdpPayload = pc.localDescription.sdp;
      const answer = await sendWebRTCOffer(sdpPayload, 'offer');

      // 5. Apply SDP answer
      if (answer && answer.mode === 'simulation') {
        console.info('Voice assistant connected in simulation mode.');
        setCallState('connected');
        return;
      }

      if (answer && answer.sdp) {
        await pc.setRemoteDescription(
          new RTCSessionDescription({
            type: answer.type || 'answer',
            sdp: answer.sdp,
          })
        );
        if (pc.connectionState === 'connected') {
          setCallState('connected');
        }
      } else {
        setCallState('connected');
      }
    } catch (err) {
      console.error('WebRTC initialization failed:', err);
      setErrorMessage(err.message || 'Could not connect audio call.');
      setCallState('ended');
      cleanup();
      if (onError) onError(err);
    }
  }, [cleanup, onRemoteTrack, onError]);

  const endCall = useCallback(() => {
    cleanup();
    setIsMuted(false);
    setCallState('ended');
  }, [cleanup]);

  const resetCall = useCallback(() => {
    cleanup();
    setIsMuted(false);
    setErrorMessage(null);
    setCallState('idle');
  }, [cleanup]);

  const toggleMute = useCallback(() => {
    if (localStreamRef.current) {
      localStreamRef.current.getAudioTracks().forEach((track) => {
        track.enabled = !track.enabled;
        setIsMuted(!track.enabled);
      });
    }
  }, []);

  return {
    callState,
    isMuted,
    analyser,
    errorMessage,
    startCall,
    endCall,
    resetCall,
    toggleMute,
  };
}
