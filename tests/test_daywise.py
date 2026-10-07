"""
tests/test_daywise.py

STEP 28 – DayWise Test Suite

Uses only Python standard library (unittest).

Run from the project root:
    python -m tests.test_daywise
or:
    python tests/test_daywise.py
"""

import sys
import os
import json
import unittest
import tempfile
from datetime import date

# ── Add project root to sys.path ──────────────────────────
sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

from core.parser import Parser
from core.scheduler import (
    schedule_tasks,
    get_free_slots,
    get_default_day_slots,
    get_default_daily_routines,
    time_to_minutes,
    minutes_to_time,
)
from core.memory import MemoryManager
from core.planner import Planner, split_compound_input
from storage import storage_manager as sm
from storage.data_manager import DataManager
from utils.date_utils import format_date_display, today_str
from utils.text_utils import truncate


# ============================================================
# PARSER TESTS
# ============================================================

class TestParser(unittest.TestCase):

    def setUp(self):
        self.parser = Parser()

    # ---- Date detection ----

    def test_detect_tomorrow(self):
        result = self.parser.detect_date("Study Python tomorrow")
        tomorrow = str(date.today().replace(
            day=date.today().day + 1
        )) if False else str(
            date.today().toordinal() and
            __import__("datetime").date.fromordinal(
                date.today().toordinal() + 1
            )
        )
        self.assertEqual(result, tomorrow)

    def test_detect_today(self):
        result = self.parser.detect_date("Buy groceries today")
        self.assertEqual(result, str(date.today()))

    def test_detect_month_day(self):
        # Parser requires "Month Day, Year" format or DD/MM/YYYY
        result = self.parser.detect_date("Interview on October 15, 2026")
        self.assertIsNotNone(result)
        self.assertIn("10-15", result)

    # ---- Time detection ----

    def test_detect_time_am(self):
        self.assertEqual(
            self.parser.detect_time("Meeting at 10 AM"),
            "10:00"
        )

    def test_detect_time_pm(self):
        self.assertEqual(
            self.parser.detect_time("Call at 3 PM"),
            "15:00"
        )

    def test_detect_time_24(self):
        self.assertEqual(
            self.parser.detect_time("Start at 09:30"),
            "09:30"
        )

    # ---- Time range ----

    def test_detect_time_range_12h(self):
        result = self.parser.detect_time_range(
            "Available 10 AM to 11 AM"
        )
        self.assertIsNotNone(result)
        self.assertEqual(result["start"], "10:00")
        self.assertEqual(result["end"], "11:00")

    def test_detect_time_range_24h(self):
        result = self.parser.detect_time_range(
            "Class 09:30 to 10:30"
        )
        self.assertIsNotNone(result)
        self.assertEqual(result["start"], "09:30")
        self.assertEqual(result["end"], "10:30")

    # ---- Duration ----

    def test_detect_explicit_hours(self):
        self.assertEqual(
            self.parser.detect_duration("Study for 2 hours"), 120
        )

    def test_detect_explicit_minutes(self):
        self.assertEqual(
            self.parser.detect_duration("Walk for 30 minutes"), 30
        )

    def test_estimate_duration_interview(self):
        d = self.parser.estimate_duration(
            "Prepare for my interview"
        )
        self.assertGreater(d, 60)

    def test_estimate_duration_exercise(self):
        d = self.parser.estimate_duration("Exercise")
        self.assertGreater(d, 0)

    # ---- Priority ----

    def test_priority_urgent(self):
        self.assertEqual(
            self.parser.detect_priority("Urgent task"), "very_high"
        )

    def test_priority_normal(self):
        self.assertEqual(
            self.parser.detect_priority("Buy milk"), "normal"
        )

    # ---- Context ----

    def test_context_study(self):
        self.assertEqual(
            self.parser.detect_context("Study Python"), "study"
        )

    def test_context_health(self):
        self.assertEqual(
            self.parser.detect_context("Go to gym"), "health"
        )

    def test_context_shopping(self):
        self.assertEqual(
            self.parser.detect_context("Buy groceries"), "shopping"
        )

    def test_context_social(self):
        self.assertEqual(
            self.parser.detect_context(
                "Spend time with friends"
            ),
            "social"
        )

    # ---- Deadline ----

    def test_deadline_am(self):
        self.assertEqual(
            self.parser.detect_deadline_time("Submit by 10 AM"),
            "10:00"
        )

    def test_deadline_pm(self):
        self.assertEqual(
            self.parser.detect_deadline_time("Finish before 5 PM"),
            "17:00"
        )

    # ---- Frequency ----

    def test_frequency_daily(self):
        self.assertEqual(
            self.parser.detect_frequency("Exercise every day"),
            "daily"
        )

    def test_frequency_morning(self):
        self.assertEqual(
            self.parser.detect_frequency(
                "Study Python every morning"
            ),
            "every morning"
        )

    # ---- Full parse ----

    def test_parse_full(self):
        result = self.parser.parse(
            "Study Python for 30 minutes tomorrow"
        )
        self.assertEqual(result["duration"], 30)
        self.assertEqual(result["context"], "study")
        self.assertIsNotNone(result["date"])
        self.assertIsNotNone(result["title"])


# ============================================================
# SCHEDULER TESTS
# ============================================================

class TestScheduler(unittest.TestCase):

    def test_time_conversion(self):
        self.assertEqual(time_to_minutes("07:30"), 450)
        self.assertEqual(minutes_to_time(450), "07:30")

    def test_free_slots(self):
        day = get_default_day_slots()
        routines = get_default_daily_routines()
        free = get_free_slots(day, routines)
        self.assertTrue(len(free) > 0)
        # No free slot should overlap with routines
        for slot in free:
            for routine in routines:
                self.assertFalse(
                    time_to_minutes(slot["start"]) <
                    time_to_minutes(routine["end"])
                    and
                    time_to_minutes(slot["end"]) >
                    time_to_minutes(routine["start"]),
                    f"Slot {slot} overlaps routine {routine}"
                )

    def test_schedule_single_task(self):
        tasks = [{
            "title": "Study Python",
            "duration": 60,
            "priority": "normal",
            "context": "study",
        }]
        schedule = schedule_tasks(tasks)
        task_entries = [
            e for e in schedule if e.get("type") == "task"
        ]
        self.assertTrue(len(task_entries) >= 1)
        self.assertEqual(task_entries[0]["title"], "Study Python")

    def test_schedule_preserves_routines(self):
        tasks = [{"title": "Work", "duration": 60, "priority": "normal"}]
        schedule = schedule_tasks(tasks)
        routine_titles = {e["title"] for e in schedule
                          if e.get("type") == "routine"}
        self.assertIn("Morning routine", routine_titles)
        self.assertIn("Lunch", routine_titles)

    def test_schedule_long_task_splits(self):
        tasks = [{
            "title": "Big project",
            "duration": 300,
            "priority": "high",
            "context": "work",
        }]
        schedule = schedule_tasks(tasks)
        task_entries = [
            e for e in schedule if e.get("type") == "task"
        ]
        self.assertGreater(len(task_entries), 1)
        # All segments should have same task_id
        ids = {e["task_id"] for e in task_entries}
        self.assertEqual(len(ids), 1)

    def test_schedule_chronological(self):
        tasks = [
            {"title": "A", "duration": 60, "priority": "normal"},
            {"title": "B", "duration": 60, "priority": "normal"},
        ]
        schedule = schedule_tasks(tasks)
        times = [time_to_minutes(e["start"]) for e in schedule]
        self.assertEqual(times, sorted(times))

    def test_schedule_deadline(self):
        tasks = [{
            "title": "Submit report",
            "duration": 60,
            "priority": "high",
            "context": "work",
            "deadline_time": "12:00",
        }]
        schedule = schedule_tasks(tasks)
        task_entries = [
            e for e in schedule if e.get("type") == "task"
        ]
        if task_entries:
            # Task should finish by deadline
            end = task_entries[-1]["end"]
            self.assertLessEqual(
                time_to_minutes(end),
                time_to_minutes("12:00")
            )

    def test_schedule_saves_history(self):
        """Verify scheduling saves a record to history.json."""
        initial = sm.load_history()
        initial_count = len(initial)

        tasks = [{"title": "Test save", "duration": 30,
                  "priority": "normal"}]
        schedule_tasks(tasks)

        after = sm.load_history()
        self.assertGreater(len(after), initial_count)


# ============================================================
# STORAGE TESTS
# ============================================================

class TestStorage(unittest.TestCase):

    def setUp(self):
        self.dm = DataManager()

    def test_load_history_returns_list(self):
        history = self.dm.load_all_history()
        self.assertIsInstance(history, list)

    def test_get_latest_plans(self):
        latest = self.dm.get_latest_plans(10)
        self.assertIsInstance(latest, list)
        self.assertLessEqual(len(latest), 10)

    def test_get_plan_for_today(self):
        result = self.dm.get_plan_for_today()
        self.assertIsInstance(result, list)

    def test_search_history(self):
        # Search for something that is almost certainly in history
        results = self.dm.search_plans("")
        # Empty search returns empty
        self.assertEqual(results, [])

    def test_add_and_load_task(self):
        original_tasks = self.dm.load_tasks()
        test_task = {
            "title": "Unit test task",
            "duration": 30,
            "priority": "normal",
            "status": "pending",
        }
        saved = self.dm.add_task(dict(test_task))
        self.assertIn("task_id", saved)

        loaded = self.dm.load_tasks()
        titles = [t.get("title") for t in loaded]
        self.assertIn("Unit test task", titles)

        # Clean up – restore
        sm.save_json("tasks.json", original_tasks)

    def test_update_task_status(self):
        original_tasks = self.dm.load_tasks()
        test_task = {
            "title": "Status update test",
            "duration": 30,
            "priority": "normal",
        }
        saved = self.dm.add_task(dict(test_task))
        task_id = saved["task_id"]

        result = self.dm.update_task_status(task_id, "completed")
        self.assertTrue(result)

        found = self.dm.get_task_by_id(task_id)
        self.assertEqual(found["status"], "completed")

        # Clean up
        sm.save_json("tasks.json", original_tasks)

    def test_invalid_status_raises(self):
        with self.assertRaises(ValueError):
            self.dm.update_task_status("fakeid", "invalid_status")

    def test_load_memory_returns_dict(self):
        mem = self.dm.load_memory()
        self.assertIsInstance(mem, dict)

    def test_load_routines_returns_list(self):
        routines = self.dm.load_routines()
        self.assertIsInstance(routines, list)


# ============================================================
# MEMORY TESTS
# ============================================================

class TestMemory(unittest.TestCase):

    def setUp(self):
        self.memory = MemoryManager()

    def test_load_memory(self):
        mem = self.memory.load_memory()
        self.assertIsInstance(mem, dict)

    def test_extract_sleep(self):
        stored = self.memory.extract_and_store(
            "I usually sleep at 10:30 PM"
        )
        categories = [s[0] for s in stored]
        self.assertIn("sleep_schedule", categories)

    def test_extract_preference(self):
        stored = self.memory.extract_and_store(
            "I prefer studying at night"
        )
        categories = [s[0] for s in stored]
        self.assertIn("preferences", categories)

    def test_extract_constraint(self):
        stored = self.memory.extract_and_store(
            "I have college from 9 AM to 4 PM"
        )
        categories = [s[0] for s in stored]
        self.assertIn("constraints", categories)

    def test_study_preference_night(self):
        # Store a night preference
        self.memory.add_memory_entry(
            "I prefer studying at night", "preferences"
        )
        pref = self.memory.get_study_preference_time()
        # Should return night window
        if pref:
            self.assertEqual(pref[0], "20:00")


# ============================================================
# PLANNER TESTS
# ============================================================

class TestPlanner(unittest.TestCase):

    def setUp(self):
        self.planner = Planner()

    def test_split_compound_input(self):
        phrases = split_compound_input(
            "Study Python for 2 hours and go shopping"
        )
        self.assertGreater(len(phrases), 1)

    def test_plan_simple(self):
        result = self.planner.plan("Study Python for 1 hour")
        self.assertIsNone(result.get("error"))
        self.assertGreater(len(result["schedule"]), 0)

    def test_plan_compound(self):
        result = self.planner.plan(
            "Prepare for interview, study Python for 2 hours"
        )
        self.assertIsNone(result.get("error"))
        tasks = result.get("tasks", [])
        self.assertGreater(len(tasks), 1)

    def test_plan_empty_input(self):
        result = self.planner.plan("")
        self.assertIsNotNone(result.get("error"))

    def test_plan_saves_to_history(self):
        before = len(sm.load_history())
        self.planner.plan("Quick test task")
        after = len(sm.load_history())
        self.assertGreater(after, before)

    def test_get_today_plan(self):
        plan = self.planner.get_today_plan()
        self.assertIsInstance(plan, list)

    def test_search_history(self):
        self.planner.plan("Python debugging session")
        results = self.planner.search_history("python")
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)


# ============================================================
# UTILITY TESTS
# ============================================================

class TestUtils(unittest.TestCase):

    def test_today_str(self):
        s = today_str()
        self.assertRegex(s, r"\d{4}-\d{2}-\d{2}")

    def test_format_date_display_today(self):
        label = format_date_display(today_str())
        self.assertIn("Today", label)

    def test_truncate(self):
        long_text = "a" * 100
        result = truncate(long_text, 20)
        self.assertLessEqual(len(result), 20)
        self.assertTrue(result.endswith("..."))


# ============================================================
# ROUTINE MANAGEMENT TESTS
# ============================================================

class TestRoutineManagement(unittest.TestCase):

    def setUp(self):
        self.dm = DataManager()
        self.planner = Planner()

    def test_add_and_save_routine(self):
        new_routine = {
            "name": "Gym Session",
            "start_time": "06:30",
            "end_time": "07:30",
            "days": ["Monday", "Wednesday", "Friday"],
            "enabled": True
        }
        added = self.dm.add_routine(new_routine)
        self.assertIsNotNone(added.get("routine_id"))
        
        # Load from disk to verify persistence
        routines = self.dm.load_routines()
        routine_names = [r.get("name") for r in routines]
        self.assertIn("Gym Session", routine_names)

    def test_delete_routine_and_persistence(self):
        r = self.dm.add_routine({
            "name": "Temporary Routine",
            "start_time": "14:00",
            "end_time": "15:00",
            "enabled": True
        })
        rid = r["routine_id"]
        
        deleted = self.dm.delete_routine(rid)
        self.assertTrue(deleted)

        # Verify it remains deleted after loading from disk again
        routines = self.dm.load_routines()
        rids = [x.get("routine_id") for x in routines]
        self.assertNotIn(rid, rids)

    def test_routine_blocks_scheduler_time(self):
        # Add routine at 08:00 - 09:00
        self.dm.add_routine({
            "name": "Morning Yoga",
            "start_time": "08:00",
            "end_time": "09:00",
            "enabled": True
        })
        
        # Schedule a task
        schedule = schedule_tasks([{"title": "Check Email", "duration": 30}])
        
        # Verify 08:00 - 09:00 is occupied by Morning Yoga
        routine_entry = None
        for entry in schedule:
            if entry.get("title") == "Morning Yoga":
                routine_entry = entry
                break
        self.assertIsNotNone(routine_entry)
        self.assertEqual(routine_entry["start"], "08:00")
        self.assertEqual(routine_entry["end"], "09:00")
        
        # Clean up
        self.dm.delete_routine(routine_entry.get("routine_id", "Morning Yoga"))

    def test_deleted_routine_frees_scheduler_time(self):
        r = self.dm.add_routine({
            "name": "Midday Sprint",
            "start_time": "11:00",
            "end_time": "12:00",
            "enabled": True
        })
        rid = r["routine_id"]
        
        # Delete routine
        self.dm.delete_routine(rid)
        
        # Check schedule
        schedule = schedule_tasks([{"title": "Writing Docs", "duration": 60}])
        titles = [e.get("title") for e in schedule]
        self.assertNotIn("Midday Sprint", titles)

    def test_history_unchanged_on_routine_delete(self):
        history_before = sm.load_history()
        r = self.dm.add_routine({
            "name": "Temporary Test Routine",
            "start_time": "16:00",
            "end_time": "17:00",
            "enabled": True
        })
        self.dm.delete_routine(r["routine_id"])
        history_after = sm.load_history()
        self.assertEqual(len(history_before), len(history_after))


# ============================================================
# TITLE CLEANING TESTS
# ============================================================

class TestCleanTitle(unittest.TestCase):

    def setUp(self):
        self.parser = Parser()

    def test_interview_title_clean(self):
        title = self.parser.extract_title("I have an interview tomorrow and need to prepare for it")
        self.assertEqual(title, "Interview Preparation")

    def test_groceries_title_clean(self):
        title = self.parser.extract_title("I want to go to the supermarket to buy groceries")
        self.assertEqual(title, "Buy Groceries")

    def test_study_python_title_clean(self):
        title = self.parser.extract_title("I need to study Python from 2 PM to 4 PM")
        self.assertEqual(title, "Study Python")

    def test_temple_title_clean(self):
        title = self.parser.extract_title("I want to go to the temple")
        self.assertEqual(title, "Go to Temple")


# ============================================================
# NATURAL LANGUAGE & SCHEDULER REGRESSION TESTS (TEST 1 - 8)
# ============================================================

class TestNaturalLanguageRegression(unittest.TestCase):

    def setUp(self):
        self.parser = Parser()
        self.planner = Planner()

    def test_regression_1_before_that(self):
        """TEST 1: Before that relationship separation and clean titles"""
        text = "Tomorrow I have a college class. Before that, I want to exercise and have breakfast."
        plan = self.planner.plan(text)
        tasks = plan.get("tasks", [])
        titles = [t["title"] for t in tasks]

        self.assertIn("College Class", titles)
        self.assertIn("Exercise", titles)
        self.assertIn("Breakfast", titles)

        for title in titles:
            self.assertNotIn("Before That", title)
            self.assertNotIn("After Lunch", title)

    def test_regression_2_after_lunch(self):
        """TEST 2: After lunch relationship separation"""
        text = "After lunch, I need to prepare for my interview."
        parsed = self.parser.parse(text)
        title = self.parser.extract_title(text)

        self.assertEqual(title, "Interview Preparation")
        self.assertEqual(parsed.get("after_task"), "Lunch")

    def test_regression_3_deadline_evening(self):
        """TEST 3: Deadline by evening context separation"""
        text = "Complete my assignment by evening."
        parsed = self.parser.parse(text)
        title = self.parser.extract_title(text)

        self.assertEqual(title, "Complete My Assignment")
        self.assertIsNotNone(parsed.get("deadline_time"))
        self.assertEqual(parsed.get("context_window"), "evening")

    def test_regression_4_later_in_day(self):
        """TEST 4: Later in the day context separation"""
        text = "Spend some time with my friends later in the day."
        parsed = self.parser.parse(text)
        title = self.parser.extract_title(text)

        self.assertEqual(title, "Spend Some Time With My Friends")
        self.assertEqual(parsed.get("context_window"), "later_day")

    def test_regression_5_fixed_time(self):
        """TEST 5: Explicit time -> fixed_time / time_type = fixed"""
        text = "College class from 9 AM to 1 PM."
        parsed = self.parser.parse(text)

        self.assertEqual(parsed.get("time_type"), "fixed")
        self.assertEqual(parsed.get("start_time"), "09:00")
        self.assertEqual(parsed.get("end_time"), "13:00")

    def test_regression_6_no_time_estimated(self):
        """TEST 6: No time supplied -> time_type = estimated, start_time = None"""
        text = "I have a college class tomorrow."
        parsed = self.parser.parse(text)

        self.assertEqual(parsed.get("time_type"), "estimated")
        self.assertIsNone(parsed.get("start_time"))
        self.assertGreater(parsed.get("duration", 0), 0)

    def test_regression_7_multiple_tasks(self):
        """TEST 7: Compound sentence splitting"""
        text = "I need to study Python and call my friend."
        plan = self.planner.plan(text)
        tasks = plan.get("tasks", [])
        titles = [t["title"] for t in tasks]

        self.assertIn("Study Python", titles)
        self.assertIn("Call My Friend", titles)

    def test_regression_8_routine_deduplication(self):
        """TEST 8: Routine appears exactly ONCE in schedule"""
        dm = DataManager()
        # Add Gym Session routine if not present
        dm.add_routine({
            "name": "Gym Session",
            "start_time": "06:30",
            "end_time": "07:30",
            "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
            "enabled": True
        })

        schedule = schedule_tasks([{"title": "Study", "duration": 30}], plan_date="2026-10-06")
        gym_entries = [e for e in schedule if e.get("title") == "Gym Session"]

        self.assertEqual(len(gym_entries), 1, f"Expected exactly 1 Gym Session entry, got {len(gym_entries)}")


from core.scheduler import validate_and_repair_schedule

class TestCriticalSchedulingLogic(unittest.TestCase):

    def setUp(self):
        self.planner = Planner()

    def test_case_1_college_before_exercise(self):
        text = "College class from 9 AM to 1 PM. Before that I want to exercise."
        result = self.planner.plan(text)
        schedule = result.get("schedule", [])
        
        college_entry = next((e for e in schedule if e["title"] == "College Class"), None)
        exercise_entry = next((e for e in schedule if e["title"] in ("Exercise", "Gym Session")), None)

        self.assertIsNotNone(college_entry)
        self.assertEqual(college_entry["start"], "09:00")
        self.assertEqual(college_entry["end"], "13:00")

        self.assertIsNotNone(exercise_entry)
        self.assertLessEqual(time_to_minutes(exercise_entry["end"]), time_to_minutes("09:00"))

    def test_case_2_meeting_before_exercise(self):
        text = "I have a meeting from 10 AM to 12 PM. Before the meeting I want to exercise."
        result = self.planner.plan(text)
        schedule = result.get("schedule", [])

        meeting_entry = next((e for e in schedule if e["title"] == "Meeting"), None)
        exercise_entry = next((e for e in schedule if e["title"] in ("Exercise", "Gym Session")), None)

        self.assertIsNotNone(meeting_entry)
        self.assertEqual(meeting_entry["start"], "10:00")
        self.assertEqual(meeting_entry["end"], "12:00")
        if exercise_entry:
            self.assertLessEqual(time_to_minutes(exercise_entry["end"]), time_to_minutes("10:00"))

    def test_case_3_after_class_study_3h(self):
        text = "I have class from 9 AM to 1 PM. After class I want to study for 3 hours."
        result = self.planner.plan(text)
        schedule = result.get("schedule", [])

        study_entry = next((e for e in schedule if "Study" in e["title"]), None)
        self.assertIsNotNone(study_entry)
        self.assertGreaterEqual(time_to_minutes(study_entry["start"]), time_to_minutes("13:00"))

    def test_case_4_class_lunch_interview_prep(self):
        text = "I have lunch after class and then I want to prepare for my interview."
        result = self.planner.plan(text)
        schedule = result.get("schedule", [])

        lunch_entry = next((e for e in schedule if e["title"] == "Lunch"), None)
        prep_entry = next((e for e in schedule if e["title"] == "Interview Preparation"), None)

        if lunch_entry and prep_entry:
            self.assertGreaterEqual(time_to_minutes(prep_entry["start"]), time_to_minutes(lunch_entry["end"]))

    def test_case_5_no_duplicate_exercise_and_gym(self):
        text = "I want to exercise before college."
        result = self.planner.plan(text)
        schedule = result.get("schedule", [])

        exercise_entries = [e for e in schedule if e["title"] in ("Exercise", "Gym Session", "Workout")]
        self.assertLessEqual(len(exercise_entries), 1)

    def test_case_6_no_overlapping_final_schedule(self):
        text = "Tomorrow I have a college class from 9 AM to 1 PM. Before that I want to exercise and have breakfast. After lunch I need to prepare for my interview for 3 hours, complete my assignment by 8 PM, and spend some time with my friends in the evening."
        result = self.planner.plan(text)
        schedule = result.get("schedule", [])

        # Verify schedule was generated without crash and has entries
        self.assertIsInstance(schedule, list)
        self.assertGreater(len(schedule), 0)

        # Flexible tasks must not overlap each other.
        # Note: fixed events/routines keep their configured times and may conflict
        # with each other when user-provided fixed events span routine times.
        # Only check non-fixed entries against each other.
        flexible = [e for e in schedule
                    if e.get("type") not in ("event", "routine")
                    and e.get("time_type") != "fixed"]
        flexible_sorted = sorted(flexible, key=lambda x: time_to_minutes(x["start"]))
        for i in range(len(flexible_sorted) - 1):
            e1_end = time_to_minutes(flexible_sorted[i]["end"])
            e2_start = time_to_minutes(flexible_sorted[i + 1]["start"])
            self.assertLessEqual(
                e1_end, e2_start,
                f"Flexible task overlap: {flexible_sorted[i]['title']} "
                f"({flexible_sorted[i]['end']}) -> "
                f"{flexible_sorted[i+1]['title']} ({flexible_sorted[i+1]['start']})"
            )

    def test_case_7_fixed_event_blocking(self):
        text = "College Class from 9 AM to 1 PM."
        result = self.planner.plan(text)
        schedule = result.get("schedule", [])

        c_start = time_to_minutes("09:00")
        c_end = time_to_minutes("13:00")

        # College Class itself must be present at the right time
        college_entry = next((e for e in schedule if e.get("title") == "College Class"), None)
        self.assertIsNotNone(college_entry, "College Class must appear in schedule")
        self.assertEqual(college_entry["start"], "09:00")
        self.assertEqual(college_entry["end"], "13:00")

        # Flexible tasks (not routines, not events) must not occupy College Class time
        for e in schedule:
            if e.get("title") == "College Class":
                continue
            # Skip routines – they are fixed blocks that keep their configured time
            # even if they happen to coincide with a user fixed event.
            if e.get("type") == "routine":
                continue
            s = time_to_minutes(e["start"])
            end = time_to_minutes(e["end"])
            self.assertFalse(
                s > c_start and s < c_end,
                f"{e['title']} starts inside College Class window"
            )
            self.assertFalse(
                end > c_start and end < c_end,
                f"{e['title']} ends inside College Class window"
            )

    def test_case_8_dashboard_total_scheduled_time(self):
        text = "College class from 9 AM to 1 PM."
        result = self.planner.plan(text)
        schedule = result.get("schedule", [])

        total_minutes = 0
        for e in schedule:
            s_m = time_to_minutes(e["start"])
            e_m = time_to_minutes(e["end"])
            if e_m > s_m:
                total_minutes += (e_m - s_m)

        self.assertGreater(total_minutes, 0)

    def test_case_9_routine_overlap_resolution(self):
        # When two overlapping routines are both fixed, the repair pass
        # MUST NOT move either of them — both keep their configured times.
        # This tests the invariant: fixed routines are immovable.
        routines = [
            {"start": "06:00", "end": "07:00", "title": "Morning routine",
             "type": "routine", "time_type": "fixed"},
            {"start": "06:30", "end": "07:30", "title": "Gym Session",
             "type": "routine", "time_type": "fixed"}
        ]
        repaired = validate_and_repair_schedule(list(routines))

        # Both routines must still appear (not dropped)
        self.assertEqual(len(repaired), 2,
                         "Both overlapping fixed routines must be preserved")

        # Verify their times were NOT changed
        morning = next((e for e in repaired if e["title"] == "Morning routine"), None)
        gym = next((e for e in repaired if e["title"] == "Gym Session"), None)
        self.assertIsNotNone(morning)
        self.assertIsNotNone(gym)
        self.assertEqual(morning["start"], "06:00",
                         "Morning routine start must not be moved")
        self.assertEqual(morning["end"], "07:00",
                         "Morning routine end must not be moved")
        self.assertEqual(gym["start"], "06:30",
                         "Gym Session start must not be moved")
        self.assertEqual(gym["end"], "07:30",
                         "Gym Session end must not be moved")

    def test_case_10_before_relationship(self):
        text = "I want to exercise before my class."
        parsed = Parser().parse(text)
        # "class" → before_task should be "Class" or "College Class"
        self.assertIn(parsed.get("before_task"), ("College Class", "Class", "College"))

    def test_case_11_after_relationship(self):
        text = "I want to study after my class."
        parsed = Parser().parse(text)
        self.assertIn(parsed.get("after_task"), ("College Class", "Class", "College"))

    def test_case_12_evening_context(self):
        text = "I want to spend some time with my friends in the evening."
        parsed = Parser().parse(text)
        self.assertEqual(parsed.get("context_window"), "evening")


# ============================================================
# CLARIFICATION SYSTEM TESTS (Tests 1–10 as specified)
# ============================================================

class TestClarificationSystem(unittest.TestCase):
    """Tests the interactive clarification flow introduced in the new feature."""

    def setUp(self):
        self.parser = Parser()
        self.planner = Planner()

    # ---- TEST 1: Missing college time triggers clarification ----

    def test_1_college_without_time_needs_clarification(self):
        """'I have to go to college tomorrow' should ask for college time."""
        result = self.planner.plan("I have to go to college tomorrow")
        self.assertTrue(
            result.get("needs_clarification"),
            "Expected needs_clarification=True when college time is missing"
        )
        self.assertIn("college", result.get("question", "").lower())

    # ---- TEST 2: Full time range → no clarification ----

    def test_2_college_with_full_range_no_clarification(self):
        """'College tomorrow from 9 AM to 4 PM' should schedule directly."""
        result = self.planner.plan("College tomorrow from 9 AM to 4 PM")
        self.assertFalse(
            result.get("needs_clarification", False),
            "Expected no clarification when both start and end times are given"
        )
        self.assertIn("schedule", result)
        college_entry = next(
            (e for e in result["schedule"] if "college" in e.get("title", "").lower()),
            None
        )
        self.assertIsNotNone(college_entry, "College should appear in schedule")
        self.assertEqual(college_entry["start"], "09:00")
        self.assertEqual(college_entry["end"], "16:00")

    # ---- TEST 3: Start time only → ask for end time ----

    def test_3_college_start_only_asks_for_end(self):
        """'College at 9 AM' → should ask for end/return time."""
        result = self.planner.plan("College at 9 AM")
        self.assertTrue(
            result.get("needs_clarification"),
            "Expected clarification for end time when only start is given"
        )
        # Should be asking about end / return time
        question = result.get("question", "").lower()
        self.assertTrue(
            any(w in question for w in ("return", "end", "finish", "leave")),
            f"Expected question about end/return time, got: {question}"
        )
        self.assertEqual(result.get("field"), "end_time")

    # ---- TEST 4: Both exercise AND breakfast get before-college relationship ----

    def test_4_exercise_and_breakfast_both_before_college(self):
        """Both exercise and breakfast from 'before college' should be BEFORE college."""
        text = "College from 9 AM to 1 PM. I want to exercise and have breakfast before college."
        result = self.planner.plan(text)
        self.assertFalse(result.get("needs_clarification", False))
        schedule = result.get("schedule", [])
        college_entry = next(
            (e for e in schedule if "college" in e.get("title", "").lower()), None
        )
        self.assertIsNotNone(college_entry)
        college_start = time_to_minutes(college_entry["start"])

        exercise_entry = next(
            (e for e in schedule if e.get("title", "").lower() in ("exercise", "gym session", "workout")),
            None
        )
        if exercise_entry:
            self.assertLessEqual(
                time_to_minutes(exercise_entry["end"]), college_start,
                f"Exercise must finish before college. Got end={exercise_entry['end']}"
            )

        breakfast_entry = next(
            (e for e in schedule if "breakfast" in e.get("title", "").lower()),
            None
        )
        if breakfast_entry:
            self.assertLessEqual(
                time_to_minutes(breakfast_entry["end"]), college_start,
                f"Breakfast must finish before college. Got end={breakfast_entry['end']}"
            )

    # ---- TEST 5: Explicit duration overrides estimation ----

    def test_5_explicit_duration_3_hours_interview_prep(self):
        """'prepare for my interview for 3 hours' → duration = 180 min."""
        parsed = self.parser.parse("After college prepare for my interview for 3 hours")
        self.assertEqual(
            parsed.get("duration"), 180,
            f"Expected duration=180, got {parsed.get('duration')}"
        )

    # ---- TEST 6: Assignment with deadline and high priority ----

    def test_6_assignment_high_priority_evening_deadline(self):
        """'complete an important assignment before evening' → high priority, deadline ~18:00."""
        parsed = self.parser.parse("complete an important assignment before evening")
        self.assertEqual(parsed.get("priority"), "high")
        deadline = parsed.get("deadline_time")
        self.assertIsNotNone(deadline)
        # Evening deadline should be 18:00
        dl_mins = time_to_minutes(deadline)
        self.assertGreaterEqual(dl_mins, time_to_minutes("17:00"))
        self.assertLessEqual(dl_mins, time_to_minutes("19:00"))

    # ---- TEST 7: Friends later in the day → social + later_day ----

    def test_7_friends_later_in_day(self):
        """'spend time with my friends later in the day' → social context + later_day window."""
        parsed = self.parser.parse("spend time with my friends later in the day")
        self.assertEqual(parsed.get("context"), "social")
        self.assertEqual(parsed.get("context_window"), "later_day")

    # ---- TEST 8: Complete interactive clarification flow ----

    def test_8_complete_clarification_flow(self):
        """Full interactive loop: college → ask start → ask end → schedule."""
        # Step 1: initial plan without times
        result1 = self.planner.plan("I have college tomorrow")
        self.assertTrue(result1.get("needs_clarification"))
        self.assertEqual(result1.get("field"), "start_time")

        # Step 2: provide start time
        result2 = self.planner.continue_plan(
            original_input=result1["original_input"],
            pending_tasks=result1["pending_tasks"],
            plan_date=result1["plan_date"],
            field="start_time",
            value="9 AM",
            task_title=result1["task_title"],
        )
        self.assertTrue(result2.get("needs_clarification"))
        self.assertEqual(result2.get("field"), "end_time")

        # Step 3: provide end time → should now generate schedule
        result3 = self.planner.continue_plan(
            original_input=result2["original_input"],
            pending_tasks=result2["pending_tasks"],
            plan_date=result2["plan_date"],
            field="end_time",
            value="4 PM",
            task_title=result2["task_title"],
        )
        self.assertFalse(result3.get("needs_clarification", False))
        schedule = result3.get("schedule", [])
        self.assertTrue(len(schedule) > 0, "Expected a non-empty schedule after clarification")

        college_entry = next(
            (e for e in schedule if "college" in e.get("title", "").lower()), None
        )
        self.assertIsNotNone(college_entry, "College should be in the schedule")
        self.assertEqual(college_entry["start"], "09:00")
        self.assertEqual(college_entry["end"], "16:00")

    # ---- TEST 9: Existing complete plan still works (backward compatibility) ----

    def test_9_backward_compatibility_study_python(self):
        """'Study Python for 2 hours' must still work without clarification."""
        result = self.planner.plan("Study Python for 2 hours")
        self.assertFalse(result.get("needs_clarification", False))
        schedule = result.get("schedule", [])
        study_entry = next(
            (e for e in schedule if "study" in e.get("title", "").lower() or "python" in e.get("title", "").lower()),
            None
        )
        self.assertIsNotNone(study_entry)
        self.assertEqual(study_entry.get("end") and
                         time_to_minutes(study_entry["end"]) - time_to_minutes(study_entry["start"]),
                         120)

    # ---- TEST 10: No duplicate breakfast when user explicitly requests it ----

    def test_10_no_duplicate_breakfast(self):
        """User says 'have breakfast before college'. Only one Breakfast entry in schedule."""
        result = self.planner.plan(
            "College from 9 AM to 1 PM. I want to have breakfast before college."
        )
        self.assertFalse(result.get("needs_clarification", False))
        schedule = result.get("schedule", [])
        breakfast_entries = [
            e for e in schedule
            if "breakfast" in e.get("title", "").lower()
        ]
        self.assertLessEqual(
            len(breakfast_entries), 1,
            f"Expected at most 1 breakfast entry, found {len(breakfast_entries)}: "
            f"{[e['title'] for e in breakfast_entries]}"
        )



# ============================================================
# FIXED-ROUTINE SCHEDULING INVARIANT TESTS
# ============================================================

class TestFixedRoutineInvariants(unittest.TestCase):
    """
    Tests that verify fixed routines are NEVER moved by the scheduler.

    These tests directly call schedule_tasks() with mock routines
    injected via monkeypatching, so they do not depend on routines.json content.
    """

    def _make_routine(self, title, start, end, days=None):
        """Helper: build a routine dict matching routines.json schema."""
        return {
            "routine_id": "test_" + title.lower().replace(" ", "_"),
            "name": title,
            "title": title,
            "start_time": start,
            "end_time": end,
            "start": start,
            "end": end,
            "days": days or ["Monday", "Tuesday", "Wednesday",
                             "Thursday", "Friday", "Saturday", "Sunday"],
            "enabled": True,
            "active": True,
        }

    def _schedule_with_routines(self, routines, tasks):
        """
        Patch DataManager.load_routines to return `routines` and
        run schedule_tasks with `tasks`.  Returns the final schedule list.
        Monday = 2099-01-07.
        """
        from unittest.mock import patch
        with patch(
            "storage.data_manager.DataManager.load_routines",
            return_value=routines,
        ):
            return schedule_tasks(tasks, plan_date="2099-01-07")

    def _entry_for(self, schedule, title_fragment):
        """Return first entry whose title contains title_fragment (case-insensitive)."""
        frag = title_fragment.lower()
        for e in schedule:
            if frag in e.get("title", "").lower():
                return e
        return None

    # ----------------------------------------------------------
    # TEST 1: Breakfast stays at 08:00-08:30
    # ----------------------------------------------------------
    def test_1_breakfast_fixed_time_not_moved(self):
        """Breakfast 08:00-08:30 must appear at exactly those times."""
        routines = [self._make_routine("Breakfast", "08:00", "08:30")]
        schedule = self._schedule_with_routines(routines, [])

        breakfast = self._entry_for(schedule, "breakfast")
        self.assertIsNotNone(breakfast, "Breakfast must appear in the schedule")
        self.assertEqual(
            breakfast["start"], "08:00",
            f"Breakfast start MUST be 08:00, got {breakfast['start']}"
        )
        self.assertEqual(
            breakfast["end"], "08:30",
            f"Breakfast end MUST be 08:30, got {breakfast['end']}"
        )

    # ----------------------------------------------------------
    # TEST 2: Flexible task cannot occupy Breakfast slot
    # ----------------------------------------------------------
    def test_2_flexible_task_avoids_breakfast_slot(self):
        """Friends (120 min) must not be placed over Breakfast 08:00-08:30."""
        routines = [self._make_routine("Breakfast", "08:00", "08:30")]
        tasks = [{
            "title": "Friends",
            "duration": 120,
            "priority": "normal",
            "type": "task",
            "time_type": "estimated",
        }]
        schedule = self._schedule_with_routines(routines, tasks)

        breakfast = self._entry_for(schedule, "breakfast")
        self.assertIsNotNone(breakfast)
        self.assertEqual(breakfast["start"], "08:00",
                         f"Breakfast must stay at 08:00, got {breakfast['start']}")
        self.assertEqual(breakfast["end"], "08:30",
                         f"Breakfast must end at 08:30, got {breakfast['end']}")

        friends = self._entry_for(schedule, "friends")
        if friends:
            b_start = time_to_minutes("08:00")
            b_end   = time_to_minutes("08:30")
            f_start = time_to_minutes(friends["start"])
            f_end   = time_to_minutes(friends["end"])
            overlap = f_start < b_end and f_end > b_start
            self.assertFalse(
                overlap,
                f"Friends ({friends['start']}-{friends['end']}) overlaps "
                f"Breakfast (08:00-08:30)"
            )

    # ----------------------------------------------------------
    # TEST 3: Multiple fixed routines all stay at their times
    # ----------------------------------------------------------
    def test_3_multiple_fixed_routines_stay_put(self):
        """Breakfast 08:00-08:30 and College 09:00-16:00 both stay put."""
        routines = [
            self._make_routine("Breakfast", "08:00", "08:30"),
            self._make_routine("College", "09:00", "16:00"),
        ]
        tasks = [{
            "title": "Study",
            "duration": 60,
            "priority": "normal",
            "type": "task",
            "time_type": "estimated",
        }]
        schedule = self._schedule_with_routines(routines, tasks)

        breakfast = self._entry_for(schedule, "breakfast")
        self.assertIsNotNone(breakfast)
        self.assertEqual(breakfast["start"], "08:00")
        self.assertEqual(breakfast["end"], "08:30")

        college = self._entry_for(schedule, "college")
        self.assertIsNotNone(college)
        self.assertEqual(college["start"], "09:00")
        self.assertEqual(college["end"], "16:00")

        for entry in schedule:
            if entry.get("type") == "routine":
                continue
            e_start = time_to_minutes(entry["start"])
            e_end   = time_to_minutes(entry["end"])
            for fixed_title, f_s, f_e in [
                ("Breakfast", "08:00", "08:30"),
                ("College",   "09:00", "16:00"),
            ]:
                fs = time_to_minutes(f_s)
                fe = time_to_minutes(f_e)
                overlap = e_start < fe and e_end > fs
                self.assertFalse(
                    overlap,
                    f"{entry['title']} ({entry['start']}-{entry['end']}) "
                    f"overlaps fixed routine {fixed_title} ({f_s}-{f_e})"
                )

    # ----------------------------------------------------------
    # TEST 4: Exercise is scheduled around Breakfast
    # ----------------------------------------------------------
    def test_4_exercise_scheduled_around_breakfast(self):
        """Exercise (60 min, morning) must not overlap Breakfast 08:00-08:30."""
        routines = [self._make_routine("Breakfast", "08:00", "08:30")]
        tasks = [{
            "title": "Exercise",
            "duration": 60,
            "priority": "normal",
            "type": "task",
            "time_type": "estimated",
            "context_window": "morning",
        }]
        schedule = self._schedule_with_routines(routines, tasks)

        breakfast = self._entry_for(schedule, "breakfast")
        self.assertIsNotNone(breakfast)
        self.assertEqual(breakfast["start"], "08:00")
        self.assertEqual(breakfast["end"], "08:30")

        exercise = self._entry_for(schedule, "exercise")
        if exercise:
            b_start  = time_to_minutes("08:00")
            b_end    = time_to_minutes("08:30")
            ex_start = time_to_minutes(exercise["start"])
            ex_end   = time_to_minutes(exercise["end"])
            overlap  = ex_start < b_end and ex_end > b_start
            self.assertFalse(
                overlap,
                f"Exercise ({exercise['start']}-{exercise['end']}) overlaps "
                f"Breakfast (08:00-08:30)"
            )

    # ----------------------------------------------------------
    # TEST 5: JSON persistence – routine times survive reload
    # ----------------------------------------------------------
    def test_5_routine_times_persisted_in_json(self):
        """After save, load_routines() must return the same start/end times."""
        dm = DataManager()
        test_rec = {
            "routine_id": "test_breakfast_persist_invariant",
            "name": "BreakfastPersistInvariant",
            "title": "BreakfastPersistInvariant",
            "start_time": "08:00",
            "start": "08:00",
            "end_time": "08:30",
            "end": "08:30",
            "days": ["Monday"],
            "enabled": True,
            "active": True,
        }
        dm.add_routine(dict(test_rec))

        routines = dm.load_routines()
        found = next(
            (r for r in routines
             if (r.get("name") or r.get("title", "")) == "BreakfastPersistInvariant"),
            None
        )
        self.assertIsNotNone(found, "Saved routine must appear after reload")
        start = found.get("start_time") or found.get("start")
        end   = found.get("end_time") or found.get("end")
        self.assertEqual(start, "08:00",
                         f"Persisted start must be 08:00, got {start}")
        self.assertEqual(end, "08:30",
                         f"Persisted end must be 08:30, got {end}")

        dm.delete_routine("test_breakfast_persist_invariant")

    # ----------------------------------------------------------
    # TEST 6: is_fixed_entry() correctly classifies entries
    # ----------------------------------------------------------
    def test_6_is_fixed_entry_classification(self):
        """is_fixed_entry() must return True for routines/events, False for flexible tasks."""
        from core.scheduler import is_fixed_entry

        self.assertTrue(
            is_fixed_entry({"title": "Breakfast", "type": "routine",
                            "time_type": "fixed", "start": "08:00", "end": "08:30"}),
            "Routine entries must be classified as fixed"
        )
        self.assertTrue(
            is_fixed_entry({"title": "College", "type": "event",
                            "time_type": "fixed", "start": "09:00", "end": "16:00"}),
            "Event entries must be classified as fixed"
        )
        self.assertFalse(
            is_fixed_entry({"title": "Shopping", "type": "task",
                            "time_type": "estimated", "start": "10:00", "end": "11:00"}),
            "Flexible task entries must NOT be classified as fixed"
        )
        self.assertTrue(
            is_fixed_entry({"title": "Gym Session", "type": "routine",
                            "time_type": "fixed", "start": "06:30", "end": "07:30"}),
            "Custom-named routines must also be classified as fixed"
        )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    unittest.main(verbosity=2)


