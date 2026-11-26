"""Input normalization helpers for phone numbers, dates, and time slots."""

import re
from datetime import date, datetime, timedelta
from typing import Optional


def normalize_phone_number(raw_phone: str) -> str:
    """
    Normalizes incoming phone numbers to a consistent E.164-compatible format.
    Strips punctuation, spaces, and handles 10-digit US / international formats.
    """
    if not raw_phone:
        raise ValueError("Phone number is required.")

    # Remove all characters except digits and leading '+'
    cleaned = re.sub(r"[^\d+]", "", raw_phone.strip())

    # Handle multiple '+' or stray characters
    if cleaned.startswith("+"):
        digits_only = re.sub(r"\D", "", cleaned[1:])
        return f"+{digits_only}"
    else:
        digits_only = re.sub(r"\D", "", cleaned)
        # If 10 digits, assume standard US country code +1
        if len(digits_only) == 10:
            return f"+1{digits_only}"
        elif len(digits_only) == 11 and digits_only.startswith("1"):
            return f"+{digits_only}"
        return f"+{digits_only}"


def normalize_date_input(raw_date: Optional[str]) -> Optional[str]:
    """
    Normalizes natural language date strings like 'today' or 'tomorrow'
    into ISO 'YYYY-MM-DD'.
    """
    if not raw_date:
        return None

    cleaned = raw_date.strip().lower()
    today = date.today()

    if cleaned in ("today", "todays"):
        return today.isoformat()
    elif cleaned in ("tomorrow", "tomorrows"):
        return (today + timedelta(days=1)).isoformat()

    # Try parsing standard date formats
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%B %d, %Y", "%b %d, %Y"):
        try:
            parsed = datetime.strptime(cleaned, fmt).date()
            return parsed.isoformat()
        except ValueError:
            continue

    # Return as-is if already YYYY-MM-DD
    return raw_date.strip()


def normalize_time_slot_input(raw_time: str) -> str:
    """
    Normalizes time slot input to match 'HH:MM AM/PM' format
    (e.g., '9am' -> '09:00 AM', '2:00 pm' -> '02:00 PM').
    """
    cleaned = raw_time.strip().upper()

    # Try different time formats
    for fmt in ("%I:%M %p", "%I:%M%p", "%I %p", "%I%p", "%H:%M"):
        try:
            t = datetime.strptime(cleaned, fmt).time()
            return t.strftime("%I:%M %p")
        except ValueError:
            continue

    return cleaned
