"""
Backend package for Voice Doctor Assistant.
"""
from .tools import check_doctor_availability, book_appointment, cancel_appointment
from .db import (
    init_db,
    seed_database,
    get_all_doctors,
    get_doctors_with_slots,
    get_all_appointments,
)

__all__ = [
    "check_doctor_availability",
    "book_appointment",
    "cancel_appointment",
    "init_db",
    "seed_database",
    "get_all_doctors",
    "get_doctors_with_slots",
    "get_all_appointments",
]
