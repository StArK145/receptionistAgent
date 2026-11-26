"""SQLite connection management and schema DDL."""

import os
import sqlite3
import logging
from typing import Optional

from ..core.config import DEFAULT_DB_PATH

logger = logging.getLogger(__name__)


def get_db_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Creates and returns a SQLite connection configured for row access and foreign keys."""
    target_path = db_path or DEFAULT_DB_PATH
    conn = sqlite3.connect(target_path, timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn


def init_db(db_path: Optional[str] = None) -> None:
    """Initializes the database schema if tables do not already exist."""
    target_path = db_path or DEFAULT_DB_PATH
    os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)

    with get_db_connection(target_path) as conn:
        cursor = conn.cursor()

        # Doctors table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS doctors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                specialty TEXT NOT NULL,
                hospital_or_clinic TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Slots table (doctor availability by date and time)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS slots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doctor_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                time_slot TEXT NOT NULL,
                is_available INTEGER NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE CASCADE,
                UNIQUE (doctor_id, date, time_slot)
            );
        """)

        # Appointments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                appointment_id TEXT NOT NULL UNIQUE,
                slot_id INTEGER NOT NULL,
                doctor_id INTEGER NOT NULL,
                patient_name TEXT,
                phone_number TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'CONFIRMED',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                cancelled_at TIMESTAMP,
                FOREIGN KEY (slot_id) REFERENCES slots(id),
                FOREIGN KEY (doctor_id) REFERENCES doctors(id)
            );
        """)

        # Create indexes for fast lookup
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_slots_lookup ON slots(doctor_id, date, is_available);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_doctors_specialty ON doctors(specialty);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_appointments_phone ON appointments(phone_number, status);")

        conn.commit()
    logger.info("Database schema initialized successfully at %s", target_path)
