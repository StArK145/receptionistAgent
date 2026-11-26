"""Appointment availability lookup, atomic booking, and cancellation services."""

import re
import uuid
import asyncio
from datetime import date
from typing import Optional, List, Dict, Any

from ..db import get_db_connection
from .normalizers import (
    normalize_phone_number,
    normalize_date_input,
    normalize_time_slot_input,
)


def _sync_check_doctor_availability(
    doctor_name: Optional[str] = None,
    specialty: Optional[str] = None,
    date_str: Optional[str] = None,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Synchronous implementation of doctor availability lookup."""
    target_date = normalize_date_input(date_str)

    query = """
        SELECT 
            d.id AS doctor_id,
            d.name AS doctor_name,
            d.specialty,
            d.hospital_or_clinic,
            s.id AS slot_id,
            s.date AS slot_date,
            s.time_slot
        FROM doctors d
        JOIN slots s ON d.id = s.doctor_id
        WHERE s.is_available = 1
    """
    params: List[Any] = []

    if doctor_name:
        clean_doc = f"%{doctor_name.strip()}%"
        query += " AND (d.name LIKE ? OR d.name LIKE ?)"
        # Handle search with or without 'Dr.' prefix
        stripped_prefix = re.sub(r"^dr\.?\s*", "", doctor_name.strip(), flags=re.IGNORECASE)
        params.extend([clean_doc, f"%{stripped_prefix}%"])

    if specialty:
        query += " AND d.specialty LIKE ?"
        params.append(f"%{specialty.strip()}%")

    if target_date:
        query += " AND s.date = ?"
        params.append(target_date)
    else:
        # Default: slots from today onward
        today_iso = date.today().isoformat()
        query += " AND s.date >= ?"
        params.append(today_iso)

    query += " ORDER BY d.id ASC, s.date ASC, s.time_slot ASC;"

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()

    if not rows:
        filter_details = []
        if doctor_name:
            filter_details.append(f"doctor '{doctor_name}'")
        if specialty:
            filter_details.append(f"specialty '{specialty}'")
        if target_date:
            filter_details.append(f"date '{target_date}'")

        desc = " for " + ", ".join(filter_details) if filter_details else ""
        return {
            "status": "not_found",
            "count": 0,
            "doctors": [],
            "message": f"No available appointments found{desc}.",
        }

    # Group slots under respective doctors
    doctors_map: Dict[int, Dict[str, Any]] = {}
    total_slots = 0

    for row in rows:
        doc_id = row["doctor_id"]
        if doc_id not in doctors_map:
            doctors_map[doc_id] = {
                "doctor_id": doc_id,
                "name": row["doctor_name"],
                "specialty": row["specialty"],
                "hospital": row["hospital_or_clinic"],
                "available_slots": [],
            }

        doctors_map[doc_id]["available_slots"].append({
            "slot_id": row["slot_id"],
            "date": row["slot_date"],
            "time_slot": row["time_slot"],
        })
        total_slots += 1

    doctors_list = list(doctors_map.values())

    return {
        "status": "success",
        "count": len(doctors_list),
        "total_available_slots": total_slots,
        "doctors": doctors_list,
        "message": f"Found {len(doctors_list)} doctor(s) with {total_slots} available slot(s).",
    }


def _sync_book_appointment(
    doctor_name: str,
    date_str: str,
    time_slot: str,
    phone_number: str,
    patient_name: Optional[str] = None,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Synchronous implementation of atomic appointment booking."""
    if not doctor_name or not date_str or not time_slot or not phone_number:
        return {
            "status": "error",
            "error_code": "MISSING_REQUIRED_FIELDS",
            "message": "doctor_name, date, time_slot, and phone_number are all required to book an appointment.",
        }

    try:
        normalized_phone = normalize_phone_number(phone_number)
    except Exception as e:
        return {
            "status": "error",
            "error_code": "INVALID_PHONE_NUMBER",
            "message": f"Invalid phone number format: {str(e)}",
        }

    target_date = normalize_date_input(date_str) or date_str
    normalized_slot = normalize_time_slot_input(time_slot)
    clean_patient_name = patient_name.strip() if patient_name else "Valued Patient"

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()

        # 1. Resolve doctor
        clean_doc = f"%{doctor_name.strip()}%"
        stripped_prefix = re.sub(r"^dr\.?\s*", "", doctor_name.strip(), flags=re.IGNORECASE)
        cursor.execute(
            """
            SELECT id, name, specialty, hospital_or_clinic 
            FROM doctors 
            WHERE name LIKE ? OR name LIKE ?
            LIMIT 1;
            """,
            (clean_doc, f"%{stripped_prefix}%"),
        )
        doctor = cursor.fetchone()

        if not doctor:
            return {
                "status": "error",
                "error_code": "DOCTOR_NOT_FOUND",
                "message": f"Could not find doctor matching '{doctor_name}'.",
            }

        doctor_id = doctor["id"]
        doctor_full_name = doctor["name"]

        # 2. Check if the slot exists and is available
        cursor.execute(
            """
            SELECT id, is_available 
            FROM slots 
            WHERE doctor_id = ? AND date = ? AND (time_slot = ? OR time_slot LIKE ?)
            LIMIT 1;
            """,
            (doctor_id, target_date, normalized_slot, f"%{time_slot.strip()}%"),
        )
        slot = cursor.fetchone()

        if not slot:
            return {
                "status": "error",
                "error_code": "SLOT_NOT_FOUND",
                "message": f"No slot exists for {doctor_full_name} on {target_date} at {time_slot}.",
            }

        if slot["is_available"] == 0:
            return {
                "status": "error",
                "error_code": "SLOT_ALREADY_BOOKED",
                "message": f"The requested slot on {target_date} at {normalized_slot} for {doctor_full_name} is already booked.",
            }

        slot_id = slot["id"]

        # 3. Atomically mark slot unavailable
        cursor.execute(
            """
            UPDATE slots 
            SET is_available = 0 
            WHERE id = ? AND is_available = 1;
            """,
            (slot_id,),
        )

        if cursor.rowcount == 0:
            return {
                "status": "error",
                "error_code": "SLOT_ALREADY_BOOKED",
                "message": f"Slot on {target_date} at {normalized_slot} was just taken by another booking.",
            }

        # 4. Generate unique appointment ID
        appt_code = f"APT-{target_date.replace('-', '')}-{uuid.uuid4().hex[:4].upper()}"

        # 5. Insert appointment
        cursor.execute(
            """
            INSERT INTO appointments (appointment_id, slot_id, doctor_id, patient_name, phone_number, status)
            VALUES (?, ?, ?, ?, ?, 'CONFIRMED');
            """,
            (appt_code, slot_id, doctor_id, clean_patient_name, normalized_phone),
        )

        conn.commit()

        return {
            "status": "success",
            "appointment": {
                "appointment_id": appt_code,
                "patient_name": clean_patient_name,
                "phone_number": normalized_phone,
                "doctor_name": doctor_full_name,
                "specialty": doctor["specialty"],
                "hospital": doctor["hospital_or_clinic"],
                "date": target_date,
                "time_slot": normalized_slot,
                "status": "CONFIRMED",
            },
            "message": f"Appointment successfully confirmed for {clean_patient_name} with {doctor_full_name} ({doctor['specialty']}) on {target_date} at {normalized_slot}. Appointment ID: {appt_code}.",
        }


def _sync_cancel_appointment(
    phone_number: str,
    appointment_id: Optional[str] = None,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Synchronous implementation of appointment cancellation."""
    if not phone_number:
        return {
            "status": "error",
            "error_code": "MISSING_PHONE_NUMBER",
            "message": "A phone number is required to look up and cancel an appointment.",
        }

    try:
        normalized_phone = normalize_phone_number(phone_number)
    except Exception as e:
        return {
            "status": "error",
            "error_code": "INVALID_PHONE_NUMBER",
            "message": f"Invalid phone number format: {str(e)}",
        }

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()

        # Find active appointments for this normalized phone
        query = """
            SELECT 
                a.id,
                a.appointment_id,
                a.slot_id,
                a.patient_name,
                a.phone_number,
                d.name AS doctor_name,
                d.specialty,
                s.date AS appointment_date,
                s.time_slot
            FROM appointments a
            JOIN doctors d ON a.doctor_id = d.id
            JOIN slots s ON a.slot_id = s.id
            WHERE a.phone_number = ? AND a.status = 'CONFIRMED'
        """
        params: List[Any] = [normalized_phone]

        if appointment_id:
            query += " AND (a.appointment_id = ? OR a.appointment_id LIKE ?)"
            params.extend([appointment_id.strip(), f"%{appointment_id.strip()}%"])

        query += " ORDER BY a.created_at DESC;"

        cursor.execute(query, params)
        active_appts = cursor.fetchall()

        if not active_appts:
            msg = f"No active confirmed appointments found for phone number {normalized_phone}"
            if appointment_id:
                msg += f" matching appointment ID '{appointment_id}'"
            return {
                "status": "not_found",
                "error_code": "NO_ACTIVE_APPOINTMENT",
                "message": f"{msg}.",
            }

        # If appointment_id is not specified and multiple exist, cancel the most recent one
        target_appt = active_appts[0]

        # 1. Update appointment status to CANCELLED
        cursor.execute(
            """
            UPDATE appointments
            SET status = 'CANCELLED', cancelled_at = CURRENT_TIMESTAMP
            WHERE id = ?;
            """,
            (target_appt["id"],),
        )

        # 2. Mark the slot available again
        cursor.execute(
            """
            UPDATE slots
            SET is_available = 1
            WHERE id = ?;
            """,
            (target_appt["slot_id"],),
        )

        conn.commit()

        cancelled_info = {
            "appointment_id": target_appt["appointment_id"],
            "patient_name": target_appt["patient_name"],
            "phone_number": target_appt["phone_number"],
            "doctor_name": target_appt["doctor_name"],
            "specialty": target_appt["specialty"],
            "date": target_appt["appointment_date"],
            "time_slot": target_appt["time_slot"],
            "status": "CANCELLED",
        }

        remaining_count = len(active_appts) - 1

        return {
            "status": "success",
            "cancelled_appointment": cancelled_info,
            "remaining_active_appointments": remaining_count,
            "message": f"Appointment {target_appt['appointment_id']} with {target_appt['doctor_name']} on {target_appt['appointment_date']} at {target_appt['time_slot']} has been successfully cancelled and the slot is open again.",
        }


# ============================================================================
# Asynchronous Public Tool Interfaces (Required by Pipecat & Voice Agents)
# ============================================================================

async def check_doctor_availability(
    doctor_name: Optional[str] = None,
    specialty: Optional[str] = None,
    date: Optional[str] = None,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Checks doctor availability and returns matching doctors with their open slots."""
    return await asyncio.to_thread(
        _sync_check_doctor_availability,
        doctor_name=doctor_name,
        specialty=specialty,
        date_str=date,
        db_path=db_path,
    )


async def book_appointment(
    doctor_name: str,
    date: str,
    time_slot: str,
    phone_number: str,
    patient_name: Optional[str] = None,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Validates the slot is open, marks it booked, and stores the appointment keyed by phone_number."""
    return await asyncio.to_thread(
        _sync_book_appointment,
        doctor_name=doctor_name,
        date_str=date,
        time_slot=time_slot,
        phone_number=phone_number,
        patient_name=patient_name,
        db_path=db_path,
    )


async def cancel_appointment(
    phone_number: str,
    appointment_id: Optional[str] = None,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Finds active appointment(s) for that phone number and marks the slot available again."""
    return await asyncio.to_thread(
        _sync_cancel_appointment,
        phone_number=phone_number,
        appointment_id=appointment_id,
        db_path=db_path,
    )
