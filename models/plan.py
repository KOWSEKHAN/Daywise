"""
models/plan.py

Data models and status definitions for Plans across their lifecycle.
"""

import uuid
from datetime import datetime


class PlanStatus:
    DRAFT = "draft"
    GENERATED = "generated"
    FUTURE_CONFIRMED = "future_confirmed"
    ACTIVE = "active"
    FINALIZED = "finalized"
    HISTORICAL = "historical"
    EDITED = "edited"


class PlanRecord:
    """
    Representation of a daily plan instance.
    """

    def __init__(
        self,
        date,
        schedule=None,
        tasks=None,
        status=PlanStatus.GENERATED,
        plan_id=None,
        input_text="",
        created_at=None,
        confirmed_at=None,
        finalized_at=None,
        modifications=None,
    ):
        self.plan_id = plan_id or uuid.uuid4().hex[:8]
        self.date = date
        self.schedule = schedule or []
        self.tasks = tasks or []
        self.status = status
        self.input_text = input_text or ""
        self.created_at = created_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.confirmed_at = confirmed_at
        self.finalized_at = finalized_at
        self.modifications = modifications or []

    def to_dict(self):
        return {
            "plan_id": self.plan_id,
            "date": self.date,
            "status": self.status,
            "schedule": self.schedule,
            "tasks": self.tasks,
            "input_text": self.input_text,
            "created_at": self.created_at,
            "confirmed_at": self.confirmed_at,
            "finalized_at": self.finalized_at,
            "modifications": self.modifications,
        }

    @classmethod
    def from_dict(cls, data):
        if not data:
            return cls(date=datetime.now().strftime("%Y-%m-%d"))
        return cls(
            plan_id=data.get("plan_id"),
            date=data.get("date"),
            status=data.get("status", PlanStatus.GENERATED),
            schedule=data.get("schedule", []),
            tasks=data.get("tasks", []),
            input_text=data.get("input_text", ""),
            created_at=data.get("created_at"),
            confirmed_at=data.get("confirmed_at"),
            finalized_at=data.get("finalized_at"),
            modifications=data.get("modifications", []),
        )
