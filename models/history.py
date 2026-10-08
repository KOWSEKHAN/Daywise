"""
models/history.py

Data models for Historical Records and Audit Trails.
"""

import uuid
from datetime import datetime


class HistoricalEditAudit:
    """
    Audit record for a controlled historical edit.
    """

    def __init__(
        self,
        task_id,
        task_title,
        original_state,
        new_state,
        edit_reason,
        edit_id=None,
        edited_at=None,
    ):
        self.edit_id = edit_id or uuid.uuid4().hex[:8]
        self.edited_at = edited_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.task_id = task_id
        self.task_title = task_title
        self.original_state = original_state
        self.new_state = new_state
        self.edit_reason = edit_reason.strip()

    def to_dict(self):
        return {
            "edit_id": self.edit_id,
            "edited_at": self.edited_at,
            "task_id": self.task_id,
            "task_title": self.task_title,
            "original_state": self.original_state,
            "new_state": self.new_state,
            "edit_reason": self.edit_reason,
        }

    @classmethod
    def from_dict(cls, data):
        if not data:
            return cls(task_id="", task_title="", original_state={}, new_state={}, edit_reason="")
        return cls(
            edit_id=data.get("edit_id"),
            edited_at=data.get("edited_at"),
            task_id=data.get("task_id", ""),
            task_title=data.get("task_title", ""),
            original_state=data.get("original_state", {}),
            new_state=data.get("new_state", {}),
            edit_reason=data.get("edit_reason", ""),
        )


class HistoricalRecord:
    """
    Immutable-by-default historical plan record with audit tracking.
    """

    def __init__(
        self,
        date,
        schedule=None,
        tasks=None,
        record_id=None,
        created_at=None,
        finalized_at=None,
        input_text="",
        audit_trail=None,
        is_edited=False,
    ):
        self.record_id = record_id or uuid.uuid4().hex[:8]
        self.date = date
        self.schedule = schedule or []
        self.tasks = tasks or []
        self.created_at = created_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.finalized_at = finalized_at or self.created_at
        self.input_text = input_text or ""
        self.audit_trail = [
            a if isinstance(a, HistoricalEditAudit) else HistoricalEditAudit.from_dict(a)
            for a in (audit_trail or [])
        ]
        self.is_edited = bool(is_edited or len(self.audit_trail) > 0)

    def to_dict(self):
        return {
            "record_id": self.record_id,
            "date": self.date,
            "created_at": self.created_at,
            "finalized_at": self.finalized_at,
            "schedule": self.schedule,
            "tasks": self.tasks,
            "input_text": self.input_text,
            "audit_trail": [a.to_dict() for a in self.audit_trail],
            "is_edited": self.is_edited,
        }

    @classmethod
    def from_dict(cls, data):
        if not data:
            return cls(date=datetime.now().strftime("%Y-%m-%d"))
        return cls(
            record_id=data.get("record_id"),
            date=data.get("date"),
            created_at=data.get("created_at"),
            finalized_at=data.get("finalized_at"),
            schedule=data.get("schedule", []),
            tasks=data.get("tasks", []),
            input_text=data.get("input_text", ""),
            audit_trail=data.get("audit_trail", []),
            is_edited=data.get("is_edited", False),
        )
