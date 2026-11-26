"""
Backward-compatible facade for appointment tools.
Actual implementations now live in `backend.services.normalizers` and `backend.services.appointments`.
"""

from .services import (
    normalize_phone_number,
    normalize_date_input,
    normalize_time_slot_input,
    _sync_check_doctor_availability,
    _sync_book_appointment,
    _sync_cancel_appointment,
    check_doctor_availability,
    book_appointment,
    cancel_appointment,
)

__all__ = [
    "normalize_phone_number",
    "normalize_date_input",
    "normalize_time_slot_input",
    "_sync_check_doctor_availability",
    "_sync_book_appointment",
    "_sync_cancel_appointment",
    "check_doctor_availability",
    "book_appointment",
    "cancel_appointment",
]
