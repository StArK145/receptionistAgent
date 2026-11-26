"""Clinic REST API routes (doctors, appointments, availability, booking, cancellation)."""

from typing import Optional
from fastapi import APIRouter, Query, HTTPException, status

from ...core.event_bus import global_event_bus
from ...db import get_doctors_with_slots, get_all_appointments
from ...services import (
    check_doctor_availability,
    book_appointment,
    cancel_appointment,
)
from ..schemas import BookAppointmentRequest, CancelAppointmentRequest

router = APIRouter()


@router.get("/api/doctors", tags=["Doctors"])
async def list_doctors_with_slots():
    """Returns all 5 registered doctors along with their current slot availability for today and tomorrow."""
    doctors_with_slots = get_doctors_with_slots()

    total_slots = sum(len(d["slots"]) for d in doctors_with_slots)
    available_slots = sum(
        sum(1 for s in d["slots"] if s["is_available"])
        for d in doctors_with_slots
    )

    return {
        "status": "success",
        "count": len(doctors_with_slots),
        "total_slots": total_slots,
        "available_slots": available_slots,
        "doctors": doctors_with_slots,
    }


@router.get("/api/appointments", tags=["Appointments"])
async def list_all_appointments():
    """Returns all appointments recorded in the system (both confirmed and cancelled)."""
    appointments = get_all_appointments()
    confirmed = sum(1 for a in appointments if a["status"] == "CONFIRMED")
    cancelled = sum(1 for a in appointments if a["status"] == "CANCELLED")

    return {
        "status": "success",
        "total_count": len(appointments),
        "confirmed_count": confirmed,
        "cancelled_count": cancelled,
        "appointments": appointments,
    }


@router.get("/api/availability", tags=["Tools"])
async def get_availability(
    doctor_name: Optional[str] = Query(None, description="Filter by doctor name"),
    specialty: Optional[str] = Query(None, description="Filter by medical specialty"),
    date: Optional[str] = Query(None, description="Filter by date ('today', 'tomorrow', or 'YYYY-MM-DD')"),
):
    """Checks doctor availability and returns open slots."""
    return await check_doctor_availability(
        doctor_name=doctor_name,
        specialty=specialty,
        date=date,
    )


@router.post("/api/appointments/book", tags=["Tools"])
async def book_appointment_endpoint(request: BookAppointmentRequest):
    """Atomically books an appointment and broadcasts the booking event."""
    result = await book_appointment(
        doctor_name=request.doctor_name,
        date=request.date,
        time_slot=request.time_slot,
        phone_number=request.phone_number,
        patient_name=request.patient_name,
    )
    if result.get("status") == "error":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result)

    await global_event_bus.broadcast("appointment_booked", result.get("appointment", {}))
    return result


@router.post("/api/appointments/cancel", tags=["Tools"])
async def cancel_appointment_endpoint(request: CancelAppointmentRequest):
    """Cancels an existing appointment, restores the slot, and broadcasts cancellation."""
    result = await cancel_appointment(
        phone_number=request.phone_number,
        appointment_id=request.appointment_id,
    )
    if result.get("status") in ("error", "not_found"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result)

    await global_event_bus.broadcast("appointment_cancelled", result.get("cancelled_appointment", {}))
    return result
