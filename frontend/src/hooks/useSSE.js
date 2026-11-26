import { useState, useEffect, useRef } from 'react';

/**
 * Hook to manage Server-Sent Events (SSE) connection from /api/events.
 * Delivers real-time transcript frames and appointment state updates.
 *
 * The callback is stored in a ref so the SSE connection is never torn down
 * and re-opened when the parent component re-renders (which was the cause of
 * duplicate transcript events on every render cycle).
 */
export function useSSE(onEventReceived) {
  const [connectionStatus, setConnectionStatus] = useState('connecting');
  const [lastEvent, setLastEvent] = useState(null);

  // Stable ref: always points to the latest callback without being a dep
  const callbackRef = useRef(onEventReceived);
  useEffect(() => {
    callbackRef.current = onEventReceived;
  });

  useEffect(() => {
    let isMounted = true;
    let eventSource = null;
    let reconnectTimer = null;

    function connect() {
      if (eventSource) {
        eventSource.close();
      }

      setConnectionStatus('connecting');
      eventSource = new EventSource('/api/events');

      eventSource.onopen = () => {
        if (isMounted) setConnectionStatus('connected');
      };

      eventSource.onmessage = (msg) => {
        if (!isMounted || !msg.data) return;
        try {
          const parsed = JSON.parse(msg.data);
          setLastEvent(parsed);
          if (callbackRef.current) {
            callbackRef.current(parsed);
          }
        } catch {
          // Heartbeat or malformed comment — ignore
        }
      };

      eventSource.onerror = () => {
        if (!isMounted) return;
        setConnectionStatus('disconnected');
        eventSource.close();
        clearTimeout(reconnectTimer);
        reconnectTimer = setTimeout(() => {
          if (isMounted) connect();
        }, 3000);
      };
    }

    connect();

    return () => {
      isMounted = false;
      clearTimeout(reconnectTimer);
      if (eventSource) eventSource.close();
    };
  }, []); // ← empty deps: connect once, never tear down on re-render

  return { connectionStatus, lastEvent };
}
