"""Read-only database queries for doctors, slots, and appointments."""

from typing import Optional, List, Dict, Any

from .connection import get_db_connection


def get_all_doctors(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Helper to list all registered doctors."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, specialty, hospital_or_clinic FROM doctors ORDER BY id ASC;")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_doctors_with_slots(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Lists all doctors along with their open and booked slots for today and tomorrow."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                d.id AS doctor_id,
                d.name,
                d.specialty,
                d.hospital_or_clinic,
                s.id AS slot_id,
                s.date,
                s.time_slot,
                s.is_available
            FROM doctors d
            LEFT JOIN slots s ON d.id = s.doctor_id
            WHERE s.date >= date('now')
            ORDER BY d.id ASC, s.date ASC, s.time_slot ASC;
        """)
        rows = cursor.fetchall()

        doctors_map: Dict[int, Dict[str, Any]] = {}
        for row in rows:
            doc_id = row["doctor_id"]
            if doc_id not in doctors_map:
                doctors_map[doc_id] = {
                    "id": doc_id,
                    "name": row["name"],
                    "specialty": row["specialty"],
                    "hospital_or_clinic": row["hospital_or_clinic"],
                    "slots": [],
                }
            if row["slot_id"] is not None:
                doctors_map[doc_id]["slots"].append({
                    "slot_id": row["slot_id"],
                    "date": row["date"],
                    "time_slot": row["time_slot"],
                    "is_available": bool(row["is_available"]),
                })

        return list(doctors_map.values())


def get_all_appointments(db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Returns all booked appointments (both confirmed and cancelled)."""
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                a.id,
                a.appointment_id,
                a.patient_name,
                a.phone_number,
                a.status,
                a.created_at,
                a.cancelled_at,
                d.name AS doctor_name,
                d.specialty,
                d.hospital_or_clinic,
                s.date AS appointment_date,
                s.time_slot
            FROM appointments a
            JOIN doctors d ON a.doctor_id = d.id
            JOIN slots s ON a.slot_id = s.id
            ORDER BY a.created_at DESC;
        """)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
