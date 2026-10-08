"""
tests/test_lifecycle.py

Comprehensive test suite for the DayWise Lifecycle System:
  - Routine Periods, Common Library, Mon-Sun Daily Overrides
  - Plan My Day, Date Selection, One-Time Tasks
  - Plan Confirmation (Today → Active | Future → Future Confirmed)
  - Date Rollover & Automatic Finalization
  - History & Controlled Audited Historical Edits
  - Data Integrity, Isolation & Backward Compatibility
"""

import os
import sys
import unittest
import shutil
import tempfile
from datetime import date, datetime, timedelta

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.planner import Planner
from core.scheduler import schedule_tasks, time_to_minutes, minutes_to_time
from models.task import Task
from models.routine import RoutinePeriod, RoutineTaskTemplate, DayRoutineItem, DAYS_OF_WEEK
from models.plan import PlanRecord, PlanStatus
from models.history import HistoricalRecord, HistoricalEditAudit
from storage.data_manager import DataManager
from utils.date_utils import (
    today_str,
    tomorrow_str,
    get_weekday_name,
    is_today,
    is_future_date,
    is_past_date,
    validate_date_range,
    date_ranges_overlap,
)


class TestDayWiseLifecycle(unittest.TestCase):
    """
    Test suite covering all phases of the Personal Planning Lifecycle.
    """

    def setUp(self):
        self.planner = Planner()
        self.dm = DataManager()

    # ========================================================
    # 1. ROUTINE TESTS (Section 40)
    # ========================================================

    def test_routine_period_date_validation(self):
        """Validates that start date cannot be after end date."""
        valid, err = validate_date_range("2026-10-15", "2026-10-01")
        self.assertFalse(valid)
        self.assertIn("cannot be after", err)

        valid2, err2 = validate_date_range("2026-10-01", "2026-10-31")
        self.assertTrue(valid2)
        self.assertIsNone(err2)

    def test_routine_period_overlap_detection(self):
        """Verifies overlapping routine periods are rejected."""
        self.assertTrue(date_ranges_overlap("2026-10-01", "2026-10-15", "2026-10-10", "2026-10-30"))
        self.assertFalse(date_ranges_overlap("2026-10-01", "2026-10-15", "2026-10-16", "2026-10-30"))

    def test_routine_period_creation_and_inheritance(self):
        """
        Tests creation of routine period with common tasks, Mon-Sun assignment,
        and day-specific override on Tuesday without mutating Monday or master template.
        """
        common_tasks = [
            {"name": "Exercise", "default_time": "06:00", "duration": 60, "category": "Health"},
            {"name": "Breakfast", "default_time": "07:30", "duration": 30, "category": "Meal"},
            {"name": "College", "default_time": "09:00", "duration": 240, "category": "Education"},
        ]

        # Monday has default Exercise (06:00)
        # Tuesday overrides Exercise to 06:30
        days_config = {
            "Monday": [
                {"name": "Exercise", "time": "06:00", "duration": 60, "enabled": True, "is_override": False},
                {"name": "Breakfast", "time": "07:30", "duration": 30, "enabled": True, "is_override": False},
            ],
            "Tuesday": [
                {"name": "Exercise", "time": "06:30", "duration": 60, "enabled": True, "is_override": True},
                {"name": "Breakfast", "time": "07:30", "duration": 30, "enabled": True, "is_override": False},
            ],
            "Wednesday": [
                {"name": "Exercise", "time": "06:00", "duration": 60, "enabled": True, "is_override": False},
            ],
            "Thursday": [],
            "Friday": [
                {"name": "Exercise", "time": "06:00", "duration": 60, "enabled": True, "is_override": False},
            ],
            "Saturday": [],
            "Sunday": [],
        }

        period = RoutinePeriod(
            name="Fall 2026 Testing",
            start_date="2026-10-01",
            end_date="2026-10-31",
            common_tasks=common_tasks,
            days_config=days_config,
        )

        p_dict = period.to_dict()
        self.dm.save_routine_period(p_dict)

        # Persistence verification
        loaded_periods = self.dm.load_routine_periods()
        saved = next((p for p in loaded_periods if p["name"] == "Fall 2026 Testing"), None)
        self.assertIsNotNone(saved)

        # Date 2026-10-05 is a Monday
        mon_routines = self.dm.get_routines_for_date("2026-10-05")
        mon_ex = next((r for r in mon_routines if r["name"] == "Exercise"), None)
        self.assertIsNotNone(mon_ex)
        self.assertEqual(mon_ex["start"], "06:00")
        self.assertFalse(mon_ex["is_override"])

        # Date 2026-10-06 is a Tuesday -> must have 06:30 override
        tue_routines = self.dm.get_routines_for_date("2026-10-06")
        tue_ex = next((r for r in tue_routines if r["name"] == "Exercise"), None)
        self.assertIsNotNone(tue_ex)
        self.assertEqual(tue_ex["start"], "06:30")
        self.assertTrue(tue_ex["is_override"])

        # Date 2026-10-07 is a Wednesday -> inherited 06:00 remains intact
        wed_routines = self.dm.get_routines_for_date("2026-10-07")
        wed_ex = next((r for r in wed_routines if r["name"] == "Exercise"), None)
        self.assertIsNotNone(wed_ex)
        self.assertEqual(wed_ex["start"], "06:00")

        # Clean up
        self.dm.delete_routine_period(period.period_id)

    def test_routines_outside_period_range(self):
        """Verifies that routines inside a period do not activate outside that period's date range."""
        period = RoutinePeriod(
            name="Restricted Period",
            start_date="2026-11-01",
            end_date="2026-11-15",
            common_tasks=[],
            days_config={"Monday": [{"name": "Unique Test Habit", "time": "05:00", "duration": 45, "enabled": True}]},
        )
        self.dm.save_routine_period(period.to_dict())

        # Date inside period: 2026-11-02 is Monday
        inside = self.dm.get_routines_for_date("2026-11-02")
        self.assertTrue(any(r["name"] == "Unique Test Habit" for r in inside))

        # Date outside period: 2026-10-05 is Monday
        outside = self.dm.get_routines_for_date("2026-10-05")
        self.assertFalse(any(r.get("name") == "Unique Test Habit" for r in outside))

        self.dm.delete_routine_period(period.period_id)

    # ========================================================
    # 2. PLAN MY DAY & CONFIRMATION TESTS (Section 41)
    # ========================================================

    def test_plan_generation_with_one_time_tasks_and_overrides(self):
        """
        Tests Plan My Day generating a plan with:
        - Applicable routines
        - One-time tasks
        - Date-specific routine overrides
        """
        test_date = "2026-10-15"  # Thursday

        one_time_tasks = [
            {
                "title": "Complete Daywise documentation",
                "duration": 120,
                "deadline": "18:00",
                "priority": "high",
                "source": "one-time",
            }
        ]

        routine_overrides = [
            {
                "name": "Breakfast",
                "start_time": "07:45",
                "duration": 30,
            }
        ]

        plan = self.planner.generate_date_plan(
            plan_date=test_date,
            one_time_tasks=one_time_tasks,
            routine_overrides=routine_overrides,
        )

        self.assertEqual(plan["status"], "generated")
        schedule = plan["schedule"]
        titles = [e["title"] for e in schedule]

        self.assertIn("Complete Daywise documentation", titles)
        doc_entry = next(e for e in schedule if e["title"] == "Complete Daywise documentation")
        self.assertEqual(doc_entry["source"], "one-time")

    def test_confirm_plan_today_becomes_active(self):
        """Confirming a plan for today sets status to 'active' in active_plan.json."""
        current_today = today_str()

        plan = self.planner.generate_date_plan(
            plan_date=current_today,
            one_time_tasks=[{"title": "Today Urgent Task", "duration": 45, "priority": "high"}],
        )

        res = self.planner.confirm_plan(plan)
        self.assertTrue(res["success"])
        self.assertEqual(res["status"], "active")

        active = self.planner.get_active_today_plan()
        self.assertIsNotNone(active)
        self.assertEqual(active["date"], current_today)
        self.assertEqual(active["status"], "active")

        # Test updating task in active plan
        self.planner.update_active_task("Today Urgent Task", status="completed", note="Done early!")
        updated_active = self.planner.get_active_today_plan()
        matched = next(e for e in updated_active["schedule"] if e["title"] == "Today Urgent Task")
        self.assertEqual(matched["status"], "completed")
        self.assertEqual(matched["note"], "Done early!")

    # ========================================================
    # 3. FUTURE PLAN TESTS (Section 42)
    # ========================================================

    def test_future_plan_confirmation_and_isolation(self):
        """
        Confirms a future plan:
        - Stored as future confirmed plan
        - Does NOT appear in today's active plan
        """
        future_d = (date.today() + timedelta(days=7)).isoformat()

        plan = self.planner.generate_date_plan(
            plan_date=future_d,
            one_time_tasks=[{"title": "Future Project Demo", "duration": 60}],
        )

        res = self.planner.confirm_plan(plan)
        self.assertTrue(res["success"])
        self.assertEqual(res["status"], "future_confirmed")

        # Verify stored in future plans
        fut_stored = self.planner.get_future_plan(future_d)
        self.assertIsNotNone(fut_stored)
        self.assertEqual(fut_stored["status"], "future_confirmed")

        # Verify today's plan is NOT overwritten
        active = self.planner.get_active_today_plan()
        if active:
            self.assertNotEqual(active.get("date"), future_d)

        # Cleanup
        self.planner.delete_future_plan(future_d)

    def test_past_date_confirmation_rejected(self):
        """Verifies that confirming a plan for a past date is rejected."""
        past_d = (date.today() - timedelta(days=3)).isoformat()
        plan = {"date": past_d, "schedule": [], "tasks": []}

        with self.assertRaises(ValueError):
            self.planner.confirm_plan(plan)

    # ========================================================
    # 4. DAY CLOSURE, ROLLOVER & HISTORY (Section 43)
    # ========================================================

    def test_active_plan_finalization_to_history(self):
        """Tests manual or rollover finalization of an active plan into permanent History."""
        test_d = today_str()
        plan_data = {
            "plan_id": "test_fin_1",
            "date": test_d,
            "schedule": [
                {"title": "Study Algorithm", "start": "10:00", "end": "11:00", "status": "completed", "note": "Finished Chapter 4"},
                {"title": "Gym", "start": "18:00", "end": "19:00", "status": "not_completed", "note": "Rest day"},
            ],
            "tasks": [{"title": "Study Algorithm"}, {"title": "Gym"}],
            "input_text": "Study Algorithm and Gym",
        }

        self.dm.save_active_plan(plan_data)
        self.dm.finalize_plan_to_history(plan_data)

        # Verify record exists in history
        history = self.dm.load_all_history()
        rec = next((h for h in history if h.get("date") == test_d), None)
        self.assertIsNotNone(rec)
        self.assertEqual(rec["status"], "finalized")

    def test_historical_edit_workflow_and_mandatory_note(self):
        """
        Tests the controlled historical edit workflow:
        - Mandatory note is required
        - Original state preserved in audit trail
        - Marked as edited
        """
        hist_date = "2026-09-20"
        init_record = {
            "record_id": "rec_hist_test",
            "date": hist_date,
            "status": "finalized",
            "schedule": [
                {"task_id": "t_py", "title": "Python Study", "start": "20:00", "end": "21:00", "status": "not_completed", "note": ""}
            ],
            "tasks": [{"task_id": "t_py", "title": "Python Study", "status": "not_completed"}],
            "audit_trail": [],
            "is_edited": False,
        }
        self.dm.finalize_plan_to_history(init_record)

        # 1. Reject empty note
        with self.assertRaises(ValueError):
            self.dm.edit_historical_task(hist_date, "t_py", {"status": "completed"}, mandatory_note="")

        # 2. Accept with valid note
        success, updated = self.dm.edit_historical_task(
            hist_date,
            "t_py",
            {"status": "completed"},
            mandatory_note="Actually completed the task at 10:30 PM.",
        )

        self.assertTrue(success)
        self.assertTrue(updated["is_edited"])
        self.assertEqual(len(updated["audit_trail"]), 1)

        audit = updated["audit_trail"][0]
        self.assertEqual(audit["task_title"], "Python Study")
        self.assertEqual(audit["original_state"]["status"], "not_completed")
        self.assertEqual(audit["new_state"]["status"], "completed")
        self.assertEqual(audit["edit_reason"], "Actually completed the task at 10:30 PM.")

    # ========================================================
    # 5. DATA INTEGRITY & ISOLATION (Section 44)
    # ========================================================

    def test_routine_change_does_not_mutate_history(self):
        """Verifies changing routine definitions does NOT rewrite existing history records."""
        hist_date = "2026-09-01"
        rec = {
            "date": hist_date,
            "schedule": [{"title": "Old Routine", "start": "06:00", "end": "07:00"}],
            "tasks": [],
        }
        self.dm.finalize_plan_to_history(rec)

        # Add or edit routine
        new_r = self.dm.add_routine({"name": "Brand New Routine", "start_time": "14:00", "end_time": "15:00", "days": ["Monday"]})

        try:
            # History remains unchanged
            h_rec = next(h for h in self.dm.load_all_history() if h.get("date") == hist_date)
            titles = [e["title"] for e in h_rec["schedule"]]
            self.assertIn("Old Routine", titles)
            self.assertNotIn("Brand New Routine", titles)
        finally:
            if new_r and new_r.get("routine_id"):
                self.dm.delete_routine(new_r["routine_id"])


if __name__ == "__main__":
    unittest.main()
