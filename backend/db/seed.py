"""Initial doctor roster and daily time-slot seeding."""

from datetime import date, timedelta
from typing import Optional, Dict, Any

from ..core.config import DEFAULT_DB_PATH
from .connection import get_db_connection, init_db

# 5 realistic doctors across Cardiology, Dermatology, Pediatrics, Orthopedics, General Medicine
SEED_DOCTORS = [
    {
        "name": "Dr. Evelyn Vance",
        "specialty": "Cardiology",
        "hospital_or_clinic": "City Heart & Vascular Institute",
    },
    {
        "name": "Dr. Marcus Chen",
        "specialty": "Dermatology",
        "hospital_or_clinic": "Apex Skin & Laser Clinic",
    },
    {
        "name": "Dr. Sarah Jenkins",
        "specialty": "Pediatrics",
        "hospital_or_clinic": "Sunshine Children's Clinic",
    },
    {
        "name": "Dr. David Miller",
        "specialty": "Orthopedics",
        "hospital_or_clinic": "Summit Bone & Joint Center",
    },
    {
        "name": "Dr. Anita Patel",
        "specialty": "General Medicine",
        "hospital_or_clinic": "Downtown Family Medical Practice",
    },
]

# Standard available appointment slots per day
DEFAULT_TIME_SLOTS = [
    "09:00 AM",
    "10:30 AM",
    "11:45 AM",
    "02:00 PM",
    "03:30 PM",
    "04:45 PM",
]


def seed_database(db_path: Optional[str] = None, force_refresh_slots: bool = False) -> Dict[str, Any]:
    """
    Seeds the database with 5 realistic doctors and available time slots
    for today and tomorrow.
    """
    target_path = db_path or DEFAULT_DB_PATH
    init_db(target_path)

    today = date.today()
    tomorrow = today + timedelta(days=1)
    target_dates = [today.isoformat(), tomorrow.isoformat()]

    doctors_inserted = 0
    slots_inserted = 0

    with get_db_connection(target_path) as conn:
        cursor = conn.cursor()

        # 1. Insert doctors
        for doc in SEED_DOCTORS:
            cursor.execute(
                """
                INSERT INTO doctors (name, specialty, hospital_or_clinic)
                VALUES (?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    specialty=excluded.specialty,
                    hospital_or_clinic=excluded.hospital_or_clinic;
                """,
                (doc["name"], doc["specialty"], doc["hospital_or_clinic"]),
            )
            if cursor.rowcount > 0:
                doctors_inserted += 1

        # Retrieve all doctor IDs
        cursor.execute("SELECT id, name FROM doctors;")
        doctors = cursor.fetchall()

        # 2. Insert slots for today and tomorrow for each doctor
        for doc_row in doctors:
            doc_id = doc_row["id"]
            for slot_date in target_dates:
                for time_slot in DEFAULT_TIME_SLOTS:
                    if force_refresh_slots:
                        cursor.execute(
                            """
                            INSERT INTO slots (doctor_id, date, time_slot, is_available)
                            VALUES (?, ?, ?, 1)
                            ON CONFLICT(doctor_id, date, time_slot) DO UPDATE SET
                                is_available=1;
                            """,
                            (doc_id, slot_date, time_slot),
                        )
                        slots_inserted += 1
                    else:
                        cursor.execute(
                            """
                            INSERT OR IGNORE INTO slots (doctor_id, date, time_slot, is_available)
                            VALUES (?, ?, ?, 1);
                            """,
                            (doc_id, slot_date, time_slot),
                        )
                        if cursor.rowcount > 0:
                            slots_inserted += 1

        conn.commit()

    return {
        "status": "success",
        "dates_seeded": target_dates,
        "doctors_count": len(doctors),
        "doctors_inserted_or_updated": doctors_inserted,
        "slots_inserted": slots_inserted,
        "db_path": target_path,
    }
