/**
 * API client for interacting with the FastAPI Voice Doctor Assistant backend.
 */

const API_BASE = import.meta.env.VITE_API_URL || '';

export async function getDoctors() {
  const res = await fetch(`${API_BASE}/api/doctors`);
  if (!res.ok) {
    throw new Error(`Failed to fetch doctors: ${res.statusText}`);
  }
  return res.json();
}

export async function getAppointments() {
  const res = await fetch(`${API_BASE}/api/appointments`);
  if (!res.ok) {
    throw new Error(`Failed to fetch appointments: ${res.statusText}`);
  }
  return res.json();
}

export async function cancelAppointment(phoneNumber, appointmentId) {
  const res = await fetch(`${API_BASE}/api/appointments/cancel`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      phone_number: phoneNumber,
      appointment_id: appointmentId,
    }),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.message || data.detail?.message || 'Cancellation failed');
  }
  return data;
}

export async function sendWebRTCOffer(sdp, type = 'offer') {
  const res = await fetch(`${API_BASE}/api/offer`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ sdp, type }),
  });
  if (!res.ok) {
    throw new Error(`WebRTC offer rejected: ${res.statusText}`);
  }
  return res.json();
}
