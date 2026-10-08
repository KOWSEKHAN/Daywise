"""
models/task.py

Domain model for Tasks in DayWise.
Supports both legacy tasks and new lifecycle tasks (routines, one-time, overrides).
"""

import uuid
from datetime import datetime


class Task:
    """
    Task model representing an actionable item in DayWise.
    """

    def __init__(
        self,
        title,
        duration=60,
        priority="normal",
        deadline=None,
        status="pending",
        task_id=None,
        date=None,
        start_time=None,
        end_time=None,
        source="one-time",
        note="",
        routine_id=None,
        category="general",
        created_at=None,
        updated_at=None,
    ):
        self.task_id = task_id or uuid.uuid4().hex[:8]
        self.title = title
        self.duration = int(duration) if duration is not None else 60
        self.priority = priority or "normal"
        self.deadline = deadline
        self.status = status or "pending"
        self.date = date
        self.start_time = start_time
        self.end_time = end_time
        self.source = source or "one-time"  # 'routine', 'one-time', 'override', 'fixed'
        self.note = note or ""
        self.routine_id = routine_id
        self.category = category or "general"
        self.created_at = created_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.updated_at = updated_at or self.created_at

    def to_dict(self):
        """Serializes task to a dictionary representation."""
        return {
            "task_id": self.task_id,
            "title": self.title,
            "duration": self.duration,
            "priority": self.priority,
            "deadline": self.deadline,
            "status": self.status,
            "date": self.date,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "source": self.source,
            "note": self.note,
            "routine_id": self.routine_id,
            "category": self.category,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data):
        """Constructs a Task instance from a dictionary safely."""
        if not data or not isinstance(data, dict):
            return cls(title="Untitled Task")
        return cls(
            title=data.get("title", "Untitled Task"),
            duration=data.get("duration", 60),
            priority=data.get("priority", "normal"),
            deadline=data.get("deadline"),
            status=data.get("status", "pending"),
            task_id=data.get("task_id"),
            date=data.get("date"),
            start_time=data.get("start_time") or data.get("start"),
            end_time=data.get("end_time") or data.get("end"),
            source=data.get("source", "one-time"),
            note=data.get("note", ""),
            routine_id=data.get("routine_id"),
            category=data.get("category", "general"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )