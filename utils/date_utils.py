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
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
        friendly = d.strftime("%a, %d %b %Y")
        today = date.today()
        if d == today:
            return f"Today ({friendly})"
        if d == today + timedelta(days=1):
            return f"Tomorrow ({friendly})"
        return friendly
    except ValueError:
        return date_str


def parse_date_str(text):
    """
    Tries to parse a date string in YYYY-MM-DD format.
    Returns a date object or None.
    """
    try:
        return datetime.strptime(text.strip(), "%Y-%m-%d").date()
    except ValueError:
        return None
