"""
utils/text_utils.py

Text formatting helpers for DayWise display.
Uses only Python standard library.
"""


def format_schedule_entry(entry):
    """
    Returns a human-readable one-line string
    for a single schedule entry.

    Example:
      "09:00 - 11:00  |  Study Python  [task]"
    """
    start = entry.get("start", "??:??")
    end   = entry.get("end",   "??:??")
    title = entry.get("title", "Unknown")
    etype = entry.get("type",  "")

    label = f"{start} – {end}  |  {title}"
    if etype:
        label += f"  [{etype}]"
    return label


def format_schedule_block(schedule):
    """
    Returns a multi-line string for a full day's schedule.
    """
    if not schedule:
        return "No schedule entries."
    lines = []
    for entry in schedule:
        lines.append(format_schedule_entry(entry))
    return "\n".join(lines)


def truncate(text, max_len=60):
    """Truncates text to max_len characters."""
    text = str(text)
    if len(text) > max_len:
        return text[: max_len - 3] + "..."
    return text
