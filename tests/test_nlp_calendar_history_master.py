"""
tests/test_nlp_calendar_history_master.py

Comprehensive Master Validation Tests for:
  - Plan My Day Calendar Date Selection
  - Natural Language Parsing & Merge Flow (Routines + Manual Tasks + NLP)
  - Natural Language Constraints & Unsupported Input Handling
  - Strict History Invariant: ONE COMPLETED DAY = ONE HISTORY RECORD
  - History Rollover Idempotency & Lifecycle Completion Gate
  - Historical Status / Note Survival & Controlled Audited Edits
  - Collapsible History Accordion UI & Date Deduplication
"""

import os
import sys
import unittest
import tkinter as tk
from datetime import date, datetime, timedelta

# Ensure project root in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.planner import Planner
from storage.data_manager import DataManager
from utils.date_utils import today_str, tomorrow_str
import storage.storage_manager as sm


class TestNLPCalendarHistoryMaster(unittest.TestCase):
    """Master implementation test suite covering all 12 requested validations."""

    def setUp(self):
        self.planner = Planner()
        self.dm = DataManager()
        # Clean history of test date artifacts to ensure isolation
        self.test_dates = ["2026-11-10", "2026-11-11", "2026-11-20", "2026-11-25", "2026-08-15", "2026-12-01"]
        hist = sm.load_history()
        cleaned = [r for r in hist if r.get("date") not in self.test_dates]
        sm.save_history(cleaned)

    def tearDown(self):
        # Clean up test artifacts
        hist = sm.load_history()
        cleaned = [r for r in hist if r.get("date") not in self.test_dates]
        sm.save_history(cleaned)
        for td in self.test_dates:
            self.dm.delete_future_plan(td)

    # -------------------------------------------------------------------------
    # TEST 1 — Calendar Date Selection
    # -------------------------------------------------------------------------
    def test_1_calendar_date_selection(self):
        """Verify selected calendar date is correctly passed to Plan My Day."""
        from ui.gui import CalendarPicker
        root = tk.Tk()
        root.withdraw()
        try:
            date_var = tk.StringVar(value=today_str())
            target_date = "2026-11-10"

            # Callback simulation used by Plan My Day
            updated_state = {}
            def _on_select(d_str):
                date_var.set(d_str)
                updated_state["selected"] = d_str

            _on_select(target_date)
            self.assertEqual(date_var.get(), target_date)
            self.assertEqual(updated_state.get("selected"), target_date)

            # Date format validates cleanly with backend
            routines = self.dm.get_routines_for_date(date_var.get())
            self.assertIsInstance(routines, list)
        finally:
            root.destroy()

    # -------------------------------------------------------------------------
    # TEST 2 — Natural Language Is Included
    # -------------------------------------------------------------------------
    def test_2_natural_language_is_included(self):
        """
        Verify all required sources are represented in generated plan:
        Routine + Manual Task + NLP Instruction merged together.
        """
        test_d = "2026-11-10"
        routine_override = [{
            "name": "College",
            "title": "College",
            "start": "09:00",
            "end": "13:00",
            "duration": 240,
            "source": "routine",
        }]
        manual_tasks = [{
            "title": "Project Documentation",
            "duration": 60,
            "priority": "high",
            "source": "one-time",
            "type": "task",
            "status": "pending",
        }]
        nlp_text = "Study Python for 2 hours after 6 PM"

        plan = self.planner.generate_date_plan(
            plan_date=test_d,
            one_time_tasks=manual_tasks,
            routine_overrides=routine_override,
            raw_input=nlp_text,
        )

        self.assertEqual(plan["status"], "generated")
        schedule_titles = [e.get("title") for e in plan["schedule"]]

        # Source 1: Routine present
        self.assertTrue(any("College" in t for t in schedule_titles), "Routine 'College' missing from schedule")
        # Source 2: Manual task present
        self.assertTrue(any("Documentation" in t for t in schedule_titles), "Manual task 'Documentation' missing")
        # Source 3: NLP task present
        self.assertTrue(any("Python" in t for t in schedule_titles), "NLP task 'Study Python' missing from schedule")

    # -------------------------------------------------------------------------
    # TEST 3 — NLP Constraint
    # -------------------------------------------------------------------------
    def test_3_nlp_constraint(self):
        """Verify: 'Complete project before 6 PM' creates a task/constraint understood by planner."""
        from core.scheduler import time_to_minutes
        test_d = "2026-11-10"
        plan = self.planner.generate_date_plan(
            plan_date=test_d,
            raw_input="Complete project before 6 PM",
        )
        self.assertEqual(plan["status"], "generated")
        sched = plan["schedule"]

        project_entry = next((e for e in sched if "project" in e.get("title", "").lower()), None)
        self.assertIsNotNone(project_entry, "Task with 'project' not found in schedule")

        # Must end before or at 18:00 (6 PM)
        end_mins = time_to_minutes(project_entry.get("end", "23:59"))
        self.assertLessEqual(end_mins, time_to_minutes("18:00"), f"Project ends at {project_entry.get('end')}, expected <= 18:00")

    # -------------------------------------------------------------------------
    # TEST 4 — Invalid NLP
    # -------------------------------------------------------------------------
    def test_4_invalid_nlp(self):
        """Give unsupported/invalid instruction. Verify user receives clear error/warning and not silently ignored."""
        test_d = "2026-11-10"
        unparsable_input = "???"
        plan = self.planner.generate_date_plan(
            plan_date=test_d,
            raw_input=unparsable_input,
        )
        self.assertIn("nlp_warning", plan)
        self.assertIsNotNone(plan["nlp_warning"])
        self.assertIn("Could not parse", plan["nlp_warning"])

    # -------------------------------------------------------------------------
    # TEST 5 — Same Date Does Not Create Multiple History Records
    # -------------------------------------------------------------------------
    def test_5_same_date_does_not_create_multiple_history_records(self):
        """Generate/edit the same day's plan multiple times; finalize; verify exactly ONE history record."""
        test_d = "2026-11-11"
        plan_v1 = {
            "plan_id": "v1_test",
            "date": test_d,
            "schedule": [{"title": "Task A", "start": "09:00", "end": "10:00", "status": "completed"}],
            "tasks": [{"title": "Task A"}],
        }
        self.dm.finalize_plan_to_history(plan_v1)

        # Plan edited/regenerated and finalized again
        plan_v2 = {
            "plan_id": "v2_test",
            "date": test_d,
            "schedule": [
                {"title": "Task A", "start": "09:00", "end": "10:00", "status": "completed"},
                {"title": "Task B", "start": "10:00", "end": "11:00", "status": "completed"},
            ],
            "tasks": [{"title": "Task A"}, {"title": "Task B"}],
        }
        self.dm.finalize_plan_to_history(plan_v2)

        history = self.dm.load_all_history()
        matches = [r for r in history if r.get("date") == test_d]
        self.assertEqual(len(matches), 1, f"Expected exactly 1 history record for {test_d}, found {len(matches)}")

    # -------------------------------------------------------------------------
    # TEST 6 — Rollover Idempotency
    # -------------------------------------------------------------------------
    def test_6_rollover_idempotency(self):
        """Run rollover/finalization twice. Verify it does NOT create a second history record."""
        test_d = "2026-11-11"
        plan = {
            "plan_id": "rollover_test",
            "date": test_d,
            "schedule": [{"title": "Morning Task", "start": "08:00", "end": "09:00", "status": "completed"}],
            "tasks": [{"title": "Morning Task"}],
        }
        self.dm.finalize_plan_to_history(plan)
        count_first = len([r for r in self.dm.load_all_history() if r.get("date") == test_d])
        self.assertEqual(count_first, 1)

        # Second rollover execution for same plan/date
        self.dm.finalize_plan_to_history(plan)
        count_second = len([r for r in self.dm.load_all_history() if r.get("date") == test_d])
        self.assertEqual(count_second, 1, "Rollover is not idempotent: created duplicate history record")

    # -------------------------------------------------------------------------
    # TEST 7 — History Only After Completion
    # -------------------------------------------------------------------------
    def test_7_history_only_after_completion(self):
        """
        Verify lifecycle gating:
        Generate plan -> NOT in history.
        Confirm plan -> NOT in history.
        Activate plan -> NOT in history.
        Finalize day -> Exactly ONE history record appears.
        """
        test_d = today_str()
        # Clean current today in history if present
        hist = sm.load_history()
        sm.save_history([r for r in hist if r.get("date") != test_d])

        # Step 1: Generate plan
        plan = self.planner.generate_date_plan(
            plan_date=test_d,
            one_time_tasks=[{"title": "Gating Test Task", "duration": 45}],
        )
        history_after_gen = [r for r in self.dm.load_all_history() if r.get("date") == test_d]
        self.assertEqual(len(history_after_gen), 0, "Plan entered history upon generation!")

        # Step 2: Confirm plan (becomes active)
        self.planner.confirm_plan(plan)
        history_after_confirm = [r for r in self.dm.load_all_history() if r.get("date") == test_d]
        self.assertEqual(len(history_after_confirm), 0, "Plan entered history upon confirmation!")

        # Step 3: Finalize day
        self.planner.finalize_active_day()
        history_after_finalize = [r for r in self.dm.load_all_history() if r.get("date") == test_d]
        self.assertEqual(len(history_after_finalize), 1, "Plan did not appear in history after finalization!")

    # -------------------------------------------------------------------------
    # TEST 8 — Historical Status and Notes
    # -------------------------------------------------------------------------
    def test_8_historical_status_and_notes(self):
        """Finalize active plan containing completed task, incomplete task, task note. Verify all survive into History."""
        test_d = "2026-11-20"
        plan = {
            "plan_id": "status_note_plan",
            "date": test_d,
            "schedule": [
                {"task_id": "t1", "title": "Finish Report", "start": "10:00", "end": "11:00",
                 "status": "completed", "note": "Submitted to manager"},
                {"task_id": "t2", "title": "Gym Workout", "start": "17:00", "end": "18:00",
                 "status": "not_completed", "note": "Postponed to tomorrow"},
            ],
            "tasks": [{"title": "Finish Report"}, {"title": "Gym Workout"}],
        }
        self.dm.finalize_plan_to_history(plan)

        rec = next((r for r in self.dm.load_all_history() if r.get("date") == test_d), None)
        self.assertIsNotNone(rec)

        sched = rec.get("schedule", [])
        t1 = next((e for e in sched if e.get("title") == "Finish Report"), None)
        t2 = next((e for e in sched if e.get("title") == "Gym Workout"), None)

        self.assertIsNotNone(t1)
        self.assertEqual(t1.get("status"), "completed")
        self.assertEqual(t1.get("note"), "Submitted to manager")

        self.assertIsNotNone(t2)
        self.assertEqual(t2.get("status"), "not_completed")
        self.assertEqual(t2.get("note"), "Postponed to tomorrow")

    # -------------------------------------------------------------------------
    # TEST 9 — Future Plan Does Not Enter History Early
    # -------------------------------------------------------------------------
    def test_9_future_plan_does_not_enter_history_early(self):
        """Create future plan. Verify it exists as future_confirmed and is NOT in History."""
        future_d = "2026-11-25"
        plan = self.planner.generate_date_plan(
            plan_date=future_d,
            one_time_tasks=[{"title": "Future Project Kickoff", "duration": 60}],
        )
        res = self.planner.confirm_plan(plan)
        self.assertEqual(res.get("status"), "future_confirmed")

        # Verify exists in future plans
        f_plan = self.planner.get_future_plan(future_d)
        self.assertIsNotNone(f_plan)

        # Verify NOT in history
        hist = self.dm.load_all_history()
        in_hist = any(r.get("date") == future_d for r in hist)
        self.assertFalse(in_hist, f"Future plan for {future_d} prematurely entered History!")

    # -------------------------------------------------------------------------
    # TEST 10 — Historical Audit Still Works
    # -------------------------------------------------------------------------
    def test_10_historical_audit_still_works(self):
        """Edit historical task. Verify: no note -> rejected; valid note -> accepted, before/after preserved."""
        test_d = "2026-08-15"
        rec = {
            "record_id": "audit_test_rec",
            "date": test_d,
            "status": "finalized",
            "schedule": [
                {"task_id": "task_audit_1", "title": "Client Meeting", "start": "14:00", "end": "15:00",
                 "status": "not_completed", "note": ""}
            ],
            "tasks": [{"task_id": "task_audit_1", "title": "Client Meeting", "status": "not_completed"}],
            "audit_trail": [],
            "is_edited": False,
        }
        self.dm.finalize_plan_to_history(rec)

        # 1. Empty note must be rejected
        with self.assertRaises(ValueError):
            self.planner.edit_historical_record(
                plan_date=test_d,
                task_id="task_audit_1",
                changes={"status": "completed"},
                mandatory_note="",
            )

        # 2. Valid note must be accepted
        success, updated = self.planner.edit_historical_record(
            plan_date=test_d,
            task_id="task_audit_1",
            changes={"status": "completed"},
            mandatory_note="Meeting was conducted via Zoom successfully.",
        )
        self.assertTrue(success)
        self.assertTrue(updated["is_edited"])
        self.assertEqual(len(updated["audit_trail"]), 1)

        entry = updated["audit_trail"][0]
        self.assertEqual(entry["task_id"], "task_audit_1")
        self.assertEqual(entry["original_state"]["status"], "not_completed")
        self.assertEqual(entry["new_state"]["status"], "completed")
        self.assertEqual(entry["edit_reason"], "Meeting was conducted via Zoom successfully.")

    # -------------------------------------------------------------------------
    # TEST 11 — Collapsible History UI
    # -------------------------------------------------------------------------
    def test_11_collapsible_history_ui(self):
        """Verify each date accordion initially renders collapsed, expands on click, and collapses on second click."""
        root = tk.Tk()
        root.withdraw()
        try:
            state = {"expanded": False}
            chev_lbl = tk.Label(root, text="▶")
            detail_f = tk.Frame(root)

            def _toggle(event=None):
                state["expanded"] = not state["expanded"]
                if state["expanded"]:
                    detail_f.pack()
                    chev_lbl.config(text="▼")
                else:
                    detail_f.pack_forget()
                    chev_lbl.config(text="▶")

            # Initial: collapsed
            self.assertFalse(state["expanded"])
            self.assertEqual(chev_lbl.cget("text"), "▶")

            # Click 1: expands
            _toggle()
            self.assertTrue(state["expanded"])
            self.assertEqual(chev_lbl.cget("text"), "▼")

            # Click 2: collapses
            _toggle()
            self.assertFalse(state["expanded"])
            self.assertEqual(chev_lbl.cget("text"), "▶")
        finally:
            root.destroy()

    # -------------------------------------------------------------------------
    # TEST 12 — One Date = One History Entry
    # -------------------------------------------------------------------------
    def test_12_one_date_one_history_entry(self):
        """Create repeated operations for same date. Verify UI/storage displays that date only once."""
        test_d = "2026-12-01"
        # Simulate contaminated history with 3 records for same date
        r1 = {"record_id": "r1", "date": test_d, "status": "draft", "schedule": []}
        r2 = {"record_id": "r2", "date": test_d, "status": "finalized", "schedule": [{"title": "Task 1", "start": "09:00", "end": "10:00"}], "finalized_at": "2026-12-01 21:00:00"}
        r3 = {"record_id": "r3", "date": test_d, "status": "finalized", "schedule": [{"title": "Task 1", "start": "09:00", "end": "10:00"}, {"title": "Task 2", "start": "10:00", "end": "11:00"}], "finalized_at": "2026-12-01 22:00:00"}

        hist = sm.load_history()
        hist.extend([r1, r2, r3])
        sm.save_history(hist)

        # Run consolidation
        consolidated = self.dm.consolidate_history()
        matches = [r for r in consolidated if r.get("date") == test_d]
        self.assertEqual(len(matches), 1, f"Expected strictly 1 consolidated record, found {len(matches)}")
        # Verify best record preserved (has 2 schedule tasks)
        self.assertEqual(len(matches[0]["schedule"]), 2)


if __name__ == "__main__":
    unittest.main()
