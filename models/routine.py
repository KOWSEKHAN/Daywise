"""
models/routine.py

Data models for Routine Templates, Day-Specific Overrides, and Routine Periods.
"""

import uuid
from datetime import datetime

DAYS_OF_WEEK = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]


class RoutineTaskTemplate:
    """
    Reusable routine task definition from the common library.
    Not tied to any particular date or day of the week.
    """

    def __init__(
        self,
        name,
        default_time="08:00",
        duration=60,
        category="General",
        task_id=None,
    ):
        self.task_id = task_id or uuid.uuid4().hex[:8]
        self.name = name.strip()
        self.default_time = default_time
        self.duration = int(duration) if duration else 60
        self.category = category or "General"

    def to_dict(self):
        return {
            "task_id": self.task_id,
            "name": self.name,
            "default_time": self.default_time,
            "duration": self.duration,
            "category": self.category,
        }

    @classmethod
    def from_dict(cls, data):
        if not data:
            return cls(name="Routine")
        return cls(
            name=data.get("name") or data.get("title", "Routine"),
            default_time=data.get("default_time") or data.get("start_time") or data.get("start", "08:00"),
            duration=data.get("duration", 60),
            category=data.get("category", "General"),
            task_id=data.get("task_id") or data.get("routine_id"),
        )


class DayRoutineItem:
    """
    An assignment of a routine task to a specific day of the week.
    Can inherit default properties or specify day-specific overrides.
    """

    def __init__(
        self,
        name,
        time="08:00",
        duration=60,
        category="General",
        task_id=None,
        is_override=False,
        enabled=True,
    ):
        self.task_id = task_id or uuid.uuid4().hex[:8]
        self.name = name.strip()
        self.time = time
        self.duration = int(duration) if duration else 60
        self.category = category or "General"
        self.is_override = bool(is_override)
        self.enabled = bool(enabled)

    def to_dict(self):
        return {
            "task_id": self.task_id,
            "name": self.name,
            "time": self.time,
            "duration": self.duration,
            "category": self.category,
            "is_override": self.is_override,
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, data):
        if not data:
            return cls(name="Routine")
        return cls(
            name=data.get("name") or data.get("title", "Routine"),
            time=data.get("time") or data.get("start_time") or data.get("start", "08:00"),
            duration=data.get("duration", 60),
            category=data.get("category", "General"),
            task_id=data.get("task_id") or data.get("routine_id"),
            is_override=data.get("is_override", False),
            enabled=data.get("enabled", True),
        )


class RoutinePeriod:
    """
    A date-bounded routine period (e.g. 10-Oct-2026 to 30-Nov-2026)
    with a common task library and independent Monday-Sunday daily configs.
    """

    def __init__(
        self,
        name,
        start_date,
        end_date,
        period_id=None,
        common_tasks=None,
        days_config=None,
        enabled=True,
        created_at=None,
        updated_at=None,
    ):
        self.period_id = period_id or uuid.uuid4().hex[:8]
        self.name = name.strip()
        self.start_date = start_date.strip()
        self.end_date = end_date.strip()
        self.common_tasks = [
            t if isinstance(t, RoutineTaskTemplate) else RoutineTaskTemplate.from_dict(t)
            for t in (common_tasks or [])
        ]
        self.days_config = {}
        days_raw = days_config or {}
        for day in DAYS_OF_WEEK:
            day_items = days_raw.get(day, [])
            self.days_config[day] = [
                item if isinstance(item, DayRoutineItem) else DayRoutineItem.from_dict(item)
                for item in day_items
            ]
        self.enabled = bool(enabled)
        self.created_at = created_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.updated_at = updated_at or self.created_at

    def contains_date(self, date_str):
        """Checks if a date YYYY-MM-DD falls within this period's range [start_date, end_date]."""
        if not self.enabled:
            return False
        return self.start_date <= date_str <= self.end_date

    def get_tasks_for_weekday(self, weekday_name):
        """Returns the list of active DayRoutineItem for a weekday (e.g. 'Monday')."""
        day_items = self.days_config.get(weekday_name, [])
        return [item for item in day_items if item.enabled]

    def to_dict(self):
        return {
            "period_id": self.period_id,
            "name": self.name,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "common_tasks": [t.to_dict() for t in self.common_tasks],
            "days_config": {
                day: [item.to_dict() for item in items]
                for day, items in self.days_config.items()
            },
            "enabled": self.enabled,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data):
        if not data:
            return cls(name="Default Period", start_date="2026-01-01", end_date="2026-12-31")
        return cls(
            name=data.get("name", "Routine Period"),
            start_date=data.get("start_date", "2026-01-01"),
            end_date=data.get("end_date", "2026-12-31"),
            period_id=data.get("period_id"),
            common_tasks=data.get("common_tasks", []),
            days_config=data.get("days_config", {}),
            enabled=data.get("enabled", True),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )