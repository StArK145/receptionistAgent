"""Pydantic request schemas for the FastAPI endpoints."""

from typing import Optional
from pydantic import BaseModel, Field


class WebRTCOfferRequest(BaseModel):
    sdp: str = Field(..., description="WebRTC Session Description Protocol (SDP) offer")
    type: str = Field("offer", description="Type of WebRTC message ('offer')")


class BookAppointmentRequest(BaseModel):
    doctor_name: str = Field(..., description="Doctor's name or partial name", example="Dr. Marcus Chen")
    date: str = Field(..., description="Appointment date ('today', 'tomorrow', or 'YYYY-MM-DD')", example="today")
    time_slot: str = Field(..., description="Time slot (e.g. '09:00 AM')", example="09:00 AM")
    phone_number: str = Field(..., description="Patient contact phone number", example="+1 (555) 234-5678")
    patient_name: Optional[str] = Field(None, description="Patient's full name", example="John Doe")


class CancelAppointmentRequest(BaseModel):
    phone_number: str = Field(..., description="Patient phone number associated with booking", example="+1 (555) 234-5678")
    appointment_id: Optional[str] = Field(None, description="Specific appointment ID to cancel", example="APT-20261124-ABCD")
