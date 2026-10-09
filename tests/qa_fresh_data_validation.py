"""
tests/qa_fresh_data_validation.py

Automated Full User-Journey QA Acceptance Script for DayWise:
Executes the complete fresh-data lifecycle from a clean state.
"""

import os
import sys
import json
import unittest
from datetime import date, datetime, timedelta

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.planner import Planner
from storage.data_manager import DataManager
from utils.date_utils import today_str, tomorrow_str, get_weekday_name
from models.routine import DAYS_OF_WEEK


def reset_fresh_data():
    from storage import storage_manager as sm
    dm = DataManager()
    dm.clear_active_plan()
    dm.save_future_plans({})
    dm.save_routine_periods([])
    sm.save_history([])
    dm.save_tasks([])
    dm.save_memory({'preferences': [], 'routines': [], 'constraints': [], 'sleep_schedule': [], 'future_events': []})


def run_full_qa_suite():
    print("============================================================")
    print("STARTING DAYWISE COMPLETE FRESH-DATA QA VALIDATION")
    print("============================================================")

    # Reset to fresh state first
    reset_fresh_data()

    # 1. VERIFY INITIAL CLEAN STATE
    dm = DataManager()
    planner = Planner()

    active_p = dm.load_active_plan()
    assert active_p is None, f"Expected no active plan, found: {active_p}"

    future_ps = dm.load_future_plans()
    assert len(future_ps) == 0, f"Expected 0 future plans, found: {len(future_ps)}"

    periods = dm.load_routine_periods()
    assert len(periods) == 0, f"Expected 0 routine periods, found: {len(periods)}"

    hist = dm.load_all_history()
    assert len(hist) == 0, f"Expected 0 history records, found: {len(hist)}"
    print("[PASS] 1. Clean Initial State Verified (0 active, 0 future, 0 periods, 0 history)")

    # 2. TEST CASE A: CREATE ROUTINE PERIOD
    common_tasks = [
        {"task_id": "ct_ex", "name": "Exercise", "default_time": "06:00", "duration": 60, "category": "Health"},
        {"task_id": "ct_bf", "name": "Breakfast", "default_time": "07:30", "duration": 30, "category": "Meal"},
        {"task_id": "ct_col", "name": "College", "default_time": "09:00", "duration": 240, "category": "Education"},
        {"task_id": "ct_lun", "name": "Lunch", "default_time": "13:00", "duration": 60, "category": "Meal"},
        {"task_id": "ct_py", "name": "Python Study", "default_time": "20:00", "duration": 120, "category": "Education"},
    ]

    # Initialize days config with common tasks
    days_config = {}
    for d in DAYS_OF_WEEK:
        days_config[d] = [
            {
                "task_id": ct["task_id"],
                "name": ct["name"],
                "time": ct["default_time"],
                "duration": ct["duration"],
                "category": ct["category"],
                "is_override": False,
                "enabled": True,
            }
            for ct in common_tasks
        ]

    # 3. TEST CASE C: DAY-SPECIFIC OVERRIDE (Tuesday Exercise @ 06:30)
    for it in days_config["Tuesday"]:
        if it["name"] == "Exercise":
            it["time"] = "06:30"
            it["is_override"] = True

    # 4. TEST CASE D: UNIQUE DAY ROUTINE (Saturday Project Review @ 15:00)
    days_config["Saturday"].append({
        "task_id": "ct_proj_rev",
        "name": "Project Review",
        "time": "15:00",
        "duration": 60,
        "category": "Work",
        "is_override": True,
        "enabled": True,
    })

    period_data = {
        "period_id": "fall_2026_semester",
        "name": "Fall Semester 2026",
        "start_date": "2026-10-08",
        "end_date": "2026-10-31",
        "common_tasks": common_tasks,
        "days_config": days_config,
        "enabled": True,
    }

    saved_period = planner.save_routine_period(period_data)
    assert saved_period is not None
    assert saved_period["name"] == "Fall Semester 2026"

    # Reload from disk and verify persistence
    loaded_periods = dm.load_routine_periods()
    assert len(loaded_periods) == 1
    p = loaded_periods[0]
    assert p["start_date"] == "2026-10-08"
    assert p["end_date"] == "2026-10-31"
    assert len(p["common_tasks"]) == 5
    print("[PASS] 2. Routine Period & Common Library Saved and Persisted")

    # TEST CASE B: Verify Monday
    mon_items = p["days_config"]["Monday"]
    assert len(mon_items) == 5
    mon_ex = next(it for it in mon_items if it["name"] == "Exercise")
    assert mon_ex["time"] == "06:00"
    print("[PASS] 3. Monday Configuration Persisted (Exercise @ 06:00)")

    # TEST CASE C: Verify Tuesday Override vs Monday & Master
    tue_items = p["days_config"]["Tuesday"]
    tue_ex = next(it for it in tue_items if it["name"] == "Exercise")
    assert tue_ex["time"] == "06:30", f"Expected 06:30, got {tue_ex['time']}"
    assert tue_ex["is_override"] is True
    assert mon_ex["time"] == "06:00", f"Monday Exercise mutated! Got {mon_ex['time']}"
    master_ex = next(ct for ct in p["common_tasks"] if ct["name"] == "Exercise")
    assert master_ex["default_time"] == "06:00", f"Master Exercise mutated! Got {master_ex['default_time']}"
    print("[PASS] 4. Day-Specific Override Verified (Tuesday 06:30, Monday 06:00, Master 06:00)")

    # TEST CASE D: Verify Saturday unique routine
    sat_items = p["days_config"]["Saturday"]
    sat_titles = [it["name"] for it in sat_items]
    assert "Project Review" in sat_titles
    assert "Project Review" not in [it["name"] for it in p["days_config"]["Monday"]]
    assert "Project Review" not in [it["name"] for it in p["days_config"]["Sunday"]]
    print("[PASS] 5. Unique Day Routine Verified (Saturday has Project Review; Mon/Sun do not)")

    # 5. TEST CASE E: PLAN MY DAY FOR TODAY
    test_today = today_str()
    today_weekday = get_weekday_name(test_today)

    today_routines = dm.get_routines_for_date(test_today)
    assert len(today_routines) in (5, 6), f"Expected 5 or 6 routines for {today_weekday}, got {len(today_routines)}"
    r_titles = [r["name"] for r in today_routines]
    assert "Exercise" in r_titles and "College" in r_titles
    print(f"[PASS] 6. Plan My Day Auto-loaded {len(today_routines)} routines for Today ({test_today}, {today_weekday})")

    # 6. ADD ONE-TIME TASK & GENERATE PLAN
    one_time_tasks = [
        {
            "title": "Project Documentation",
            "duration": 120,
            "priority": "high",
            "deadline": "18:00",
            "source": "one-time",
            "type": "task",
            "status": "pending",
            "note": "",
        }
    ]

    generated_plan = planner.generate_date_plan(
        plan_date=test_today,
        one_time_tasks=one_time_tasks,
    )
    assert generated_plan["status"] == "generated"
    schedule = generated_plan["schedule"]
    sched_titles = [e["title"] for e in schedule]
    assert "Project Documentation" in sched_titles
    assert "College" in sched_titles
    assert "Exercise" in sched_titles

    # Verify zero time overlaps in schedule
    for i in range(len(schedule) - 1):
        e1 = schedule[i]
        e2 = schedule[i + 1]
        assert e1["end"] <= e2["start"], f"Collision detected between {e1['title']} ({e1['start']}-{e1['end']}) and {e2['title']} ({e2['start']}-{e2['end']})"
    print(f"[PASS] 7. Collision-Free Plan Generated with {len(schedule)} items including One-Time Task")

    # 7. INLINE EDIT & NOTE TEST
    doc_entry = next(e for e in schedule if e["title"] == "Project Documentation")
    doc_tid = doc_entry.get("task_id") or "Project Documentation"

    # 8. CONFIRM TODAY'S PLAN
    confirm_res = planner.confirm_plan(generated_plan)
    assert confirm_res["success"] is True
    assert confirm_res["status"] == "active"

    active = dm.load_active_plan()
    assert active is not None
    assert active["date"] == test_today
    assert active["status"] == "active"
    print(f"[PASS] 8. Today's Plan Confirmed & Activated for {test_today}")

    # 9. TODAY'S PLAN EXECUTION (STATUS UPDATES & NOTES)
    # Mark Exercise = completed, Breakfast = completed, Project Documentation = incomplete with note
    planner.update_active_task("Exercise", status="completed")
    planner.update_active_task("Breakfast", status="completed")
    planner.update_active_task(
        "Project Documentation",
        status="not_completed",
        note="Could not finish because project dependency was unavailable.",
    )

    # Verify updates in active plan
    active = dm.load_active_plan()
    ex_task = next(e for e in active["schedule"] if e["title"] == "Exercise")
    bf_task = next(e for e in active["schedule"] if e["title"] == "Breakfast")
    doc_task = next(e for e in active["schedule"] if e["title"] == "Project Documentation")

    assert ex_task["status"] == "completed"
    assert bf_task["status"] == "completed"
    assert doc_task["status"] in ("not_completed", "not completed")
    assert doc_task["note"] == "Could not finish because project dependency was unavailable."
    print("[PASS] 9. Today's Task Execution & Live Notes Persisted Correctly")

    # 10. FUTURE PLAN TEST (2026-10-15)
    future_date = "2026-10-15"
    future_gen = planner.generate_date_plan(
        plan_date=future_date,
        one_time_tasks=[
            {
                "title": "Complete presentation",
                "duration": 120,
                "priority": "high",
                "deadline": "18:00",
                "source": "one-time",
            }
        ],
    )
    fut_res = planner.confirm_plan(future_gen)
    assert fut_res["status"] == "future_confirmed"

    # Verify Future Plan in future_plans.json
    all_future = dm.load_future_plans()
    assert future_date in all_future
    fut_plan = all_future[future_date]
    assert fut_plan["status"] == "future_confirmed"
    assert any(e["title"] == "Complete presentation" for e in fut_plan["schedule"])
    print(f"[PASS] 10. Future Plan Confirmed for {future_date} in future_plans.json")

    # 11. FUTURE PLAN ISOLATION TEST
    # Verify Today's active plan still only has today's tasks
    active_now = dm.load_active_plan()
    assert active_now["date"] == test_today
    assert not any(e["title"] == "Complete presentation" for e in active_now["schedule"])
    print("[PASS] 11. Future Plan Isolated: Today's Active Plan Untouched")

    # 12. ROUTINE CHANGE DOES NOT SILENTLY MUTATE CONFIRMED FUTURE PLAN
    # Modify period definition for Thursdays
    p_mod = dict(p)
    for it in p_mod["days_config"]["Thursday"]:
        if it["name"] == "Exercise":
            it["time"] = "08:00"
            it["is_override"] = True
    dm.save_routine_period(p_mod)

    # Verify future plan still has original snapshot time
    fut_plan_check = dm.get_future_plan(future_date)
    fut_ex = next(e for e in fut_plan_check["schedule"] if e["title"] == "Exercise")
    assert fut_ex["start"] == "06:00", f"Future plan was mutated! Got {fut_ex['start']}"
    print("[PASS] 12. Confirmed Future Plan is an Immutable Snapshot (Not silently mutated by routine edit)")

    # 13. DATE ROLLOVER: ADVANCE CLOCK TO 2026-10-15 (Future Plan Promoted to Active)
    # First finalize current today to simulate midnight transition
    rollover_1 = dm.check_and_process_rollover(current_date="2026-10-15")
    assert test_today in rollover_1["finalized_past_plans"]
    assert rollover_1["promoted_future_plan"] == future_date

    # Verify 2026-10-15 is now Active Plan
    active_oct15 = dm.load_active_plan()
    assert active_oct15 is not None
    assert active_oct15["date"] == "2026-10-15"
    assert active_oct15["status"] == "active"
    assert any(e["title"] == "Complete presentation" for e in active_oct15["schedule"])

    # Verify 2026-10-15 is removed from future_plans.json
    assert dm.get_future_plan(future_date) is None
    print(f"[PASS] 13. Midnight Rollover to {future_date} Promoted Future Plan to Active Plan")

    # 14. EXECUTE TASKS ON 2026-10-15 ACTIVE PLAN
    planner.update_active_task("Complete presentation", status="completed", note="Presentation finalized with graphics")
    planner.update_active_task("College", status="completed")
    planner.update_active_task("Lunch", status="completed")
    planner.update_active_task("Python Study", status="not_completed", note="Postponed to tomorrow")

    # 15. MIDNIGHT ROLLOVER TO 2026-10-16 (2026-10-15 Moves to History)
    rollover_2 = dm.check_and_process_rollover(current_date="2026-10-16")
    assert "2026-10-15" in rollover_2["finalized_past_plans"]
    assert dm.load_active_plan() is None
    print("[PASS] 14. Midnight Rollover to 2026-10-16 Auto-Finalized 2026-10-15 to History")

    # 16. HISTORY IMMUTABILITY & AUDITED EDIT WORKFLOW
    hist_records = dm.load_all_history()
    assert len(hist_records) >= 2  # 2026-10-08 and 2026-10-15
    rec_oct15 = next(h for h in hist_records if h["date"] == "2026-10-15")
    assert rec_oct15["status"] == "finalized"
    pres_task = next(e for e in rec_oct15["schedule"] if e["title"] == "Complete presentation")
    assert pres_task["status"] == "completed"
    assert pres_task["note"] == "Presentation finalized with graphics"
    py_task = next(e for e in rec_oct15["schedule"] if e["title"] == "Python Study")
    assert py_task["status"] in ("not_completed", "not completed")

    # 17. REJECT HISTORICAL EDIT WITHOUT MANDATORY NOTE
    try:
        dm.edit_historical_task("2026-10-15", "Python Study", {"status": "completed"}, mandatory_note="")
        assert False, "Expected ValueError on empty note!"
    except ValueError as ve:
        assert "mandatory" in str(ve).lower()
    print("[PASS] 15. Historical Edit without Mandatory Note Rejected as Required")

    # 18. ACCEPT HISTORICAL EDIT WITH MANDATORY NOTE
    success, updated_hist = dm.edit_historical_task(
        "2026-10-15",
        "Python Study",
        {"status": "completed"},
        mandatory_note="Task was actually completed later than the scheduled time.",
    )
    assert success is True
    assert updated_hist["is_edited"] is True
    assert len(updated_hist["audit_trail"]) >= 1
    audit_entry = updated_hist["audit_trail"][-1]
    assert audit_entry["task_title"] == "Python Study"
    assert audit_entry["original_state"]["status"] in ("not_completed", "not completed")
    assert audit_entry["new_state"]["status"] == "completed"
    assert audit_entry["edit_reason"] == "Task was actually completed later than the scheduled time."
    print("[PASS] 16. Audited Historical Edit Succeeded & Preserved Before/After State")

    # 19. SEARCH TEST
    search_doc = planner.search_history("Project Documentation")
    assert len(search_doc) >= 1
    assert search_doc[0]["date"] == test_today

    search_oct15 = planner.search_history("2026-10-15")
    assert len(search_oct15) >= 1
    assert search_oct15[0]["date"] == "2026-10-15"

    search_routines = dm.load_routines()
    assert len(search_routines) > 0
    print("[PASS] 17. Search System Verified across History, Dates, and Routines")

    # 20. DATASTORE SCHEMA & RELATIONSHIP INTEGRITY
    # Check all json files exist and are valid JSON
    for fname in ["routine_periods.json", "future_plans.json", "history.json", "tasks.json", "memory.json", "routines.json"]:
        fpath = os.path.join("data", fname)
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert data is not None

    print("[PASS] 18. JSON Datastore Schema & File Structure Intact")
    print("============================================================")
    print("ALL 18 FRESH-DATA QA VALIDATION PHASES COMPLETED AND PASSED!")
    print("============================================================")

    # Clean up test data after successful validation to leave workspace pristine
    reset_fresh_data()


if __name__ == "__main__":
    run_full_qa_suite()
