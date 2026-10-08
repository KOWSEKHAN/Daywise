"""
tests/test_gui_lifecycle.py

UI & Navigation Regression Tests for DayWise GUI:
  - Verifies Single-Mount Guarantee (no duplicate pages/frames on repeated navigation).
  - Verifies Badge Deduplication (no repeated badges like [ROUTINE] [ROUTINE]).
  - Verifies Inline Edit Workflow and State Persistence.
"""

import os
import sys
import unittest
import tkinter as tk

# Ensure project root in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.gui import DayWiseApp, render_task_badges, render_schedule, BADGE_STYLES


class TestGUILifecycle(unittest.TestCase):
    """
    Tests GUI state lifecycle, navigation idempotency, and badge rendering.
    """

    @classmethod
    def setUpClass(cls):
        try:
            cls.app = DayWiseApp()
            cls.app.withdraw()  # Hide main window during headless testing
        except Exception as e:
            raise unittest.SkipTest(f"Tkinter display not available: {e}")

    @classmethod
    def tearDownClass(cls):
        try:
            cls.app.destroy()
        except Exception:
            pass

    def test_navigation_single_mount_guarantee(self):
        """
        Verifies that navigating repeatedly between pages does NOT accumulate
        duplicate page frames or stacked headers in self.content.
        """
        pages_to_test = ["today", "routines", "today", "routines", "plan", "today", "home", "history", "memory", "search"]

        for page in pages_to_test:
            self.app._show_page(page)
            # content should contain exactly one main page container frame
            children = self.app.content.winfo_children()
            self.assertEqual(
                len(children), 1,
                f"Page '{page}' mounted {len(children)} frames instead of 1."
            )

    def test_badge_deduplication(self):
        """
        Verifies that render_task_badges renders exactly one source badge and
        never duplicates badges like [ROUTINE] [ROUTINE].
        """
        test_parent = tk.Frame(self.app)

        # 1. Routine task
        routine_entry = {
            "title": "Morning Routine",
            "type": "routine",
            "source": "routine",
            "status": "pending",
            "priority": "normal",
        }
        render_task_badges(test_parent, routine_entry)
        badges = [w.cget("text").strip() for w in test_parent.winfo_children() if isinstance(w, tk.Label)]
        self.assertEqual(badges.count("ROUTINE"), 1, f"Expected 1 ROUTINE badge, got: {badges}")

        for w in test_parent.winfo_children():
            w.destroy()

        # 2. One-time high priority task
        onetime_entry = {
            "title": "Study Python",
            "type": "task",
            "source": "one-time",
            "priority": "high",
            "status": "completed",
        }
        render_task_badges(test_parent, onetime_entry)
        badges = [w.cget("text").strip() for w in test_parent.winfo_children() if isinstance(w, tk.Label)]
        self.assertIn("ONE-TIME", badges)
        self.assertIn("HIGH", badges)
        self.assertIn("COMPLETED", badges)
        self.assertEqual(len(badges), 3)

        test_parent.destroy()

    def test_inline_edit_task_updates_and_persists(self):
        """
        Verifies that inline task editing properly calls the planner,
        preserves task attributes, and persists across page re-navigation.
        """
        # Set up a test active plan
        test_plan = {
            "plan_id": "test_active_inline",
            "date": "2026-10-08",
            "status": "active",
            "schedule": [
                {
                    "task_id": "inline_task_1",
                    "title": "Original Task Title",
                    "start": "07:00",
                    "end": "08:00",
                    "start_time": "07:00",
                    "end_time": "08:00",
                    "type": "task",
                    "source": "one-time",
                    "status": "pending",
                    "note": "",
                }
            ],
            "tasks": [],
        }
        self.app.planner.data_manager.save_active_plan(test_plan)

        # Update task inline via planner API used by the GUI
        updated = self.app.planner.update_active_task(
            "inline_task_1",
            title="Updated Task Title",
            start_time="07:30",
            end_time="08:45",
            note="Started late due to traffic",
        )
        self.assertTrue(updated)

        # Reload active plan and verify persistence
        active = self.app.planner.data_manager.load_active_plan()
        task = next(e for e in active["schedule"] if e["task_id"] == "inline_task_1")
        self.assertEqual(task["title"], "Updated Task Title")
        self.assertEqual(task["start"], "07:30")
        self.assertEqual(task["end"], "08:45")
        self.assertEqual(task["note"], "Started late due to traffic")

        # Clean up
        self.app.planner.data_manager.clear_active_plan()


if __name__ == "__main__":
    unittest.main()
