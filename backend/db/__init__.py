"""SQLite database package for schema initialization, seeding, and read queries."""

from ..core.config import DEFAULT_DB_PATH
from .connection import get_db_connection, init_db
from .seed import SEED_DOCTORS, DEFAULT_TIME_SLOTS, seed_database
from .queries import get_all_doctors, get_doctors_with_slots, get_all_appointments

__all__ = [
    "DEFAULT_DB_PATH",
    "SEED_DOCTORS",
    "DEFAULT_TIME_SLOTS",
    "get_db_connection",
    "init_db",
    "seed_database",
    "get_all_doctors",
    "get_doctors_with_slots",
    "get_all_appointments",
]
