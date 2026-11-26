"""Domain services package (input normalizers and appointment operations)."""

from .normalizers import (
    normalize_phone_number,
    normalize_date_input,
    normalize_time_slot_input,
)
from .appointments import (
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
