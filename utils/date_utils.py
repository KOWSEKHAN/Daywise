"""
utils/date_utils.py

Date and time helper utilities for DayWise.
Uses only Python standard library.
"""

from datetime import date, datetime, timedelta


def today_str():
    """Returns today's date as YYYY-MM-DD."""
    return date.today().isoformat()


def tomorrow_str():
    """Returns tomorrow's date as YYYY-MM-DD."""
    return (date.today() + timedelta(days=1)).isoformat()


def format_date_display(date_str):
    """
    Converts YYYY-MM-DD into a friendlier label.

    Examples:
      "2026-10-06"  →  "Today (Tue, 06 Oct 2026)"
      "2026-10-07"  →  "Tomorrow (Wed, 07 Oct 2026)"
      "2026-10-05"  →  "Mon, 05 Oct 2026"
    """
    if not date_str:
        return "Unknown date"
    try:
        d = datetime.strptime(str(date_str).strip(), "%Y-%m-%d").date()
        friendly = d.strftime("%a, %d %b %Y")
        today = date.today()
        if d == today:
            return f"Today ({friendly})"
        if d == today + timedelta(days=1):
            return f"Tomorrow ({friendly})"
        return friendly
    except ValueError:
        return str(date_str)


def parse_date_str(text):
    """
    Tries to parse a date string in YYYY-MM-DD format.
    Returns a date object or None.
    """
    if not text:
        return None
    try:
        return datetime.strptime(str(text).strip(), "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def get_weekday_name(date_str):
    """
    Returns full weekday name (e.g. 'Monday', 'Tuesday') for a given YYYY-MM-DD.
    """
    d = parse_date_str(date_str)
    if d:
        return d.strftime("%A")
    return ""


def is_today(date_str, reference_date=None):
    """Returns True if date_str represents today (or reference_date)."""
    ref = reference_date or today_str()
    return str(date_str).strip() == str(ref).strip()


def is_future_date(date_str, reference_date=None):
    """Returns True if date_str is strictly after today (or reference_date)."""
    d = parse_date_str(date_str)
    ref = parse_date_str(reference_date) if reference_date else date.today()
    if d and ref:
        return d > ref
    return False


def is_past_date(date_str, reference_date=None):
    """Returns True if date_str is strictly before today (or reference_date)."""
    d = parse_date_str(date_str)
    ref = parse_date_str(reference_date) if reference_date else date.today()
    if d and ref:
        return d < ref
    return False


def validate_date_range(start_date_str, end_date_str):
    """
    Validates that both dates are valid YYYY-MM-DD and start_date <= end_date.
    Returns (True, None) or (False, error_message).
    """
    d1 = parse_date_str(start_date_str)
    d2 = parse_date_str(end_date_str)
    if not d1:
        return False, f"Invalid start date: '{start_date_str}'. Expected format YYYY-MM-DD."
    if not d2:
        return False, f"Invalid end date: '{end_date_str}'. Expected format YYYY-MM-DD."
    if d1 > d2:
        return False, f"Start date ({start_date_str}) cannot be after end date ({end_date_str})."
    return True, None


def date_ranges_overlap(start1, end1, start2, end2):
    """
    Returns True if [start1, end1] and [start2, end2] overlap.
    Assumes all dates in YYYY-MM-DD format.
    """
    return max(start1, start2) <= min(end1, end2)
