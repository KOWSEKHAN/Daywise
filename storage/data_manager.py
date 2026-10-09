"""
storage/data_manager.py

Central data management layer for DayWise.

Coordinates:
  - Persistent task storage (tasks.json)
  - History retrieval (history.json)
  - Memory storage (memory.json)
  - Routines storage (routines.json)

Steps 14.2 – 14.6 are implemented here.
"""

import uuid
from datetime import date, datetime

from storage import storage_manager as sm


# ============================================================
# DATA MANAGER CLASS
# ============================================================

class DataManager:
    """
    Central data-management layer.

    All application logic that touches JSON files
    should go through this class.
    """

    def __init__(self, storage=None):
        # 'storage' parameter kept for backward compatibility
        # with existing main.py which passes a StorageManager.
        # Actual file operations are done through storage_manager
        # module functions.
        pass

    # ========================================================
    # STEP 14.2 – LOAD PREVIOUS PLANS
    # ========================================================

    def load_all_history(self):
        """
        Returns every saved schedule record.
        Never crashes if history.json is missing.
        """
        return sm.load_history()

    def get_latest_plans(self, limit=10):
        """
        Returns the latest `limit` plan records
        (most-recent last / chronological within the list).

        Does NOT delete older records.
        """
        history = sm.load_history()
        return history[-limit:] if history else []

    def get_plan_by_date(self, plan_date):
        """
        Returns all schedule records saved for `plan_date`
        (YYYY-MM-DD string).

        Returns an empty list when nothing is found.
        """
        return sm.get_history_by_date(plan_date)

    def get_plan_for_today(self):
        """
        Returns schedule records for today.
        """
        today = date.today().isoformat()
        return self.get_plan_by_date(today)

    def search_plans(self, query):
        """
        Full-text search across history.

        Matches the query against:
          - date fields
          - task titles
          - any text in the serialised schedule

        Returns a list of matching history records.
        """
        return sm.search_history(query)

    # ========================================================
    # STEP 14.1 / 14.6 – SAVE PLAN
    # ========================================================

    def save_plan(self, plan_date, input_text, schedule, tasks):
        """
        Saves a generated schedule to history.json and
        returns the created plan record.

        Parameters
        ----------
        plan_date  : str  – YYYY-MM-DD
        input_text : str  – original user input
        schedule   : list – generated schedule entries
        tasks      : list – parsed task dicts
        """
        record = sm.add_plan_to_history(schedule, plan_date)
        # Attach extra info to the returned record for display
        record["input_text"] = input_text
        record["tasks"] = tasks
        return record

    # ========================================================
    # STEP 14.3 – PERSISTENT TASK STORAGE
    # ========================================================

    def load_tasks(self):
        """
        Loads all persistent tasks from tasks.json.
        Returns an empty list when the file is missing.
        """
        data = sm.load_json("tasks.json", [])
        if not isinstance(data, list):
            return []
        return data

    def save_tasks(self, tasks):
        """
        Saves the full tasks list to tasks.json.
        """
        sm.save_json("tasks.json", tasks)

    def add_task(self, task_dict):
        """
        Adds a single task to persistent storage.

        If the task already has a task_id that matches
        an existing record, the existing record is updated
        instead of creating a duplicate.

        Returns the stored task dict (with task_id).
        """
        tasks = self.load_tasks()

        # Ensure task has an ID
        if not task_dict.get("task_id"):
            task_dict["task_id"] = uuid.uuid4().hex[:8]

        # Ensure task has a status
        if not task_dict.get("status"):
            task_dict["status"] = "pending"

        # Check for existing record with same task_id
        existing_ids = {t.get("task_id") for t in tasks}
        if task_dict["task_id"] in existing_ids:
            # Update existing record
            for i, t in enumerate(tasks):
                if t.get("task_id") == task_dict["task_id"]:
                    tasks[i] = task_dict
                    break
        else:
            tasks.append(task_dict)

        self.save_tasks(tasks)
        return task_dict

    def add_tasks_bulk(self, task_list):
        """
        Adds or updates multiple tasks at once.
        Avoids creating unnecessary duplicates.
        """
        for task in task_list:
            self.add_task(task)

    # ========================================================
    # STEP 14.4 – TASK COMPLETION STATUS
    # ========================================================

    def update_task_status(self, task_id, new_status):
        """
        Updates the status of a persistent task.

        Valid statuses:
          pending | scheduled | completed | cancelled

        Does NOT touch history records.
        Returns True when the task was found and updated.
        """
        valid_statuses = {
            "pending",
            "scheduled",
            "completed",
            "cancelled",
        }

        if new_status not in valid_statuses:
            raise ValueError(
                f"Invalid status '{new_status}'. "
                f"Choose from: {valid_statuses}"
            )

        tasks = self.load_tasks()
        updated = False

        for task in tasks:
            if task.get("task_id") == task_id:
                task["status"] = new_status
                task["updated_at"] = (
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )
                updated = True
                break

        if updated:
            self.save_tasks(tasks)

        return updated

    def get_task_by_id(self, task_id):
        """
        Returns a single task dict by its task_id,
        or None if not found.
        """
        for task in self.load_tasks():
            if task.get("task_id") == task_id:
                return task
        return None

    # ========================================================
    # MEMORY HELPERS
    # ========================================================

    def load_memory(self):
        """
        Loads long-term memory from memory.json.
        Always returns a dict (never crashes).
        """
        data = sm.load_json("memory.json", {})
        if not isinstance(data, dict):
            return {}
        return data

    def save_memory(self, memory_dict):
        """
        Saves the memory dict to memory.json.
        """
        sm.save_json("memory.json", memory_dict)

    # ========================================================
    # ROUTINES HELPERS
    # ========================================================

    def get_initial_default_routines(self):
        """
        Returns the initial default routine records.
        """
        return [
            {
                "routine_id": "r_morning",
                "name": "Morning routine",
                "title": "Morning routine",
                "start_time": "06:00",
                "end_time": "07:00",
                "start": "06:00",
                "end": "07:00",
                "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
                "enabled": True,
                "active": True,
            },
            {
                "routine_id": "r_breakfast",
                "name": "Breakfast",
                "title": "Breakfast",
                "start_time": "07:00",
                "end_time": "07:30",
                "start": "07:00",
                "end": "07:30",
                "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
                "enabled": True,
                "active": True,
            },
            {
                "routine_id": "r_lunch",
                "name": "Lunch",
                "title": "Lunch",
                "start_time": "12:30",
                "end_time": "13:30",
                "start": "12:30",
                "end": "13:30",
                "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
                "enabled": True,
                "active": True,
            },
            {
                "routine_id": "r_dinner",
                "name": "Dinner",
                "title": "Dinner",
                "start_time": "18:30",
                "end_time": "19:00",
                "start": "18:30",
                "end": "19:00",
                "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
                "enabled": True,
                "active": True,
            },
            {
                "routine_id": "r_wind_down",
                "name": "Wind down",
                "title": "Wind down",
                "start_time": "21:30",
                "end_time": "22:00",
                "start": "21:30",
                "end": "22:00",
                "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
                "enabled": True,
                "active": True,
            },
        ]

    def load_routines(self):
        """
        Loads user-defined routines from routines.json.
        If routines.json does not exist or is empty on initial run,
        it seeds the default routines and saves them.
        Deduplicates routines with identical title, start, end times.
        """
        import os
        file_path = sm.get_data_file("routines.json")
        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            defaults = self.get_initial_default_routines()
            self.save_routines(defaults)
            return defaults

        data = sm.load_json("routines.json", None)
        if data is None:
            defaults = self.get_initial_default_routines()
            self.save_routines(defaults)
            return defaults

        if not isinstance(data, list):
            return []

        # Safe deduplication of duplicate routine definitions
        unique_routines = []
        seen_keys = set()
        duplicates_found = False

        for r in data:
            name = (r.get("name") or r.get("title") or "").strip().lower()
            start = r.get("start_time") or r.get("start") or ""
            end = r.get("end_time") or r.get("end") or ""
            key = (name, start, end)

            if key in seen_keys:
                duplicates_found = True
                continue
            seen_keys.add(key)
            unique_routines.append(r)

        if duplicates_found:
            self.save_routines(unique_routines)

        return unique_routines

    def save_routines(self, routines):
        """
        Saves routines list to routines.json.
        """
        sm.save_json("routines.json", routines)

    def add_routine(self, routine_dict):
        """
        Adds or updates a routine in routines.json.
        Matches existing routines by routine_id OR (name, start_time, end_time).
        Returns the stored routine dict.
        """
        routines = self.load_routines()

        name = routine_dict.get("name") or routine_dict.get("title") or "Routine"
        routine_dict["name"] = name
        routine_dict["title"] = name

        start = routine_dict.get("start") or routine_dict.get("start_time") or "08:00"
        end = routine_dict.get("end") or routine_dict.get("end_time") or "09:00"
        routine_dict["start"] = start
        routine_dict["start_time"] = start
        routine_dict["end"] = end
        routine_dict["end_time"] = end

        if "enabled" not in routine_dict:
            routine_dict["enabled"] = routine_dict.get("active", True)
        routine_dict["active"] = routine_dict["enabled"]

        if "days" not in routine_dict or not routine_dict["days"]:
            routine_dict["days"] = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

        # Check for existing record by routine_id or (name, start, end)
        existing_idx = -1
        target_id = routine_dict.get("routine_id")
        target_key = (name.strip().lower(), start, end)

        for i, r in enumerate(routines):
            r_id = r.get("routine_id")
            r_name = (r.get("name") or r.get("title") or "").strip().lower()
            r_start = r.get("start_time") or r.get("start") or ""
            r_end = r.get("end_time") or r.get("end") or ""
            r_key = (r_name, r_start, r_end)

            if (target_id and r_id == target_id) or (r_key == target_key):
                existing_idx = i
                # Preserve existing routine_id if target_id wasn't set
                if not target_id and r_id:
                    routine_dict["routine_id"] = r_id
                break

        if not routine_dict.get("routine_id"):
            routine_dict["routine_id"] = uuid.uuid4().hex[:8]

        if existing_idx >= 0:
            routines[existing_idx] = routine_dict
        else:
            routines.append(routine_dict)

        self.save_routines(routines)
        return routine_dict

    def delete_routine(self, routine_id):
        """
        Deletes a routine by routine_id or name/title.
        Does NOT touch history or tasks.
        Returns True if found and deleted.
        """
        routines = self.load_routines()
        initial_len = len(routines)
        updated = [
            r for r in routines
            if r.get("routine_id") != routine_id
            and r.get("name") != routine_id
            and r.get("title") != routine_id
        ]
        if len(updated) < initial_len:
            self.save_routines(updated)
            return True
        return False

    def update_routine(self, routine_id, updates):
        """
        Updates fields of an existing routine by routine_id or name/title.
        Returns True if updated.
        """
        routines = self.load_routines()
        found = False
        for r in routines:
            if r.get("routine_id") == routine_id or r.get("name") == routine_id or r.get("title") == routine_id:
                r.update(updates)
                found = True
                break
        if found:
            self.save_routines(routines)
        return found

    def toggle_routine_status(self, routine_id):
        """
        Toggles enabled/active status of a routine.
        """
        routines = self.load_routines()
        for r in routines:
            if r.get("routine_id") == routine_id or r.get("name") == routine_id or r.get("title") == routine_id:
                curr = r.get("enabled", r.get("active", True))
                r["enabled"] = not curr
                r["active"] = not curr
                self.save_routines(routines)
                return True
        return False

    # ========================================================
    # LIFECYCLE: ROUTINE PERIODS
    # ========================================================

    def load_routine_periods(self):
        """
        Loads all defined routine periods from routine_periods.json.
        """
        data = sm.load_json("routine_periods.json", [])
        if not isinstance(data, list):
            return []
        return data

    def save_routine_periods(self, periods):
        """
        Saves the list of routine periods to routine_periods.json.
        """
        sm.save_json("routine_periods.json", periods)

    def save_routine_period(self, period_dict):
        """
        Adds or updates a routine period.
        Validates date range and verifies no conflicting overlapping periods.
        """
        from utils.date_utils import validate_date_range, date_ranges_overlap
        s_date = period_dict.get("start_date")
        e_date = period_dict.get("end_date")

        valid, err = validate_date_range(s_date, e_date)
        if not valid:
            raise ValueError(err)

        if not period_dict.get("period_id"):
            period_dict["period_id"] = uuid.uuid4().hex[:8]

        periods = self.load_routine_periods()

        # Check for overlapping periods with different period_id
        for p in periods:
            if p.get("period_id") != period_dict["period_id"] and p.get("enabled", True):
                if date_ranges_overlap(s_date, e_date, p.get("start_date"), p.get("end_date")):
                    raise ValueError(
                        f"Routine period overlaps with existing active period '{p.get('name')}' "
                        f"({p.get('start_date')} to {p.get('end_date')})."
                    )

        existing_idx = -1
        for i, p in enumerate(periods):
            if p.get("period_id") == period_dict["period_id"]:
                existing_idx = i
                break

        if existing_idx >= 0:
            periods[existing_idx] = period_dict
        else:
            periods.append(period_dict)

        self.save_routine_periods(periods)
        return period_dict

    def delete_routine_period(self, period_id):
        """
        Deletes a routine period by period_id.
        """
        periods = self.load_routine_periods()
        initial_len = len(periods)
        updated = [p for p in periods if p.get("period_id") != period_id]
        if len(updated) < initial_len:
            self.save_routine_periods(updated)
            return True
        return False

    def get_active_routine_period_for_date(self, date_str):
        """
        Returns the active routine period covering date_str (YYYY-MM-DD), or None.
        """
        for p in self.load_routine_periods():
            if p.get("enabled", True):
                if p.get("start_date") <= str(date_str) <= p.get("end_date"):
                    return p
        return None

    def get_routines_for_date(self, date_str):
        """
        Loads the applicable daily routines for date_str.
        1. If date_str falls within an active Routine Period, loads the weekday config
           for that day with any day-specific overrides.
        2. Otherwise falls back to legacy routines in routines.json.
        """
        from utils.date_utils import get_weekday_name
        from core.scheduler import time_to_minutes, minutes_to_time

        weekday = get_weekday_name(date_str)
        period = self.get_active_routine_period_for_date(date_str)

        if period:
            days_config = period.get("days_config") or period.get("days") or {}
            day_items = days_config.get(weekday, [])
            routines = []
            for item in day_items:
                if item.get("enabled", True):
                    start = item.get("start_time") or item.get("start") or item.get("time") or "08:00"
                    if item.get("end_time") or item.get("end"):
                        end = item.get("end_time") or item.get("end")
                        dur = max(1, time_to_minutes(end) - time_to_minutes(start))
                    else:
                        dur = int(item.get("duration", 60))
                        end = minutes_to_time(time_to_minutes(start) + dur)
                    routines.append({
                        "name": item.get("name", "Routine"),
                        "title": item.get("name", "Routine"),
                        "start_time": start,
                        "start": start,
                        "end_time": end,
                        "end": end,
                        "duration": dur,
                        "days": [weekday],
                        "enabled": True,
                        "active": True,
                        "type": "routine",
                        "time_type": "fixed",
                        "routine_id": item.get("task_id"),
                        "is_override": item.get("is_override", False),
                        "category": item.get("category", "General"),
                        "period_id": period.get("period_id"),
                        "period_name": period.get("name"),
                    })
            return routines

        # Fallback to legacy routines
        legacy = self.load_routines()
        matched = []
        for r in legacy:
            is_enabled = r.get("enabled", r.get("active", True))
            days = r.get("days", [])
            day_matches = (not days) or (weekday in days)
            if is_enabled and day_matches:
                matched.append(dict(r))
        return matched

    # ========================================================
    # LIFECYCLE: FUTURE CONFIRMED PLANS
    # ========================================================

    def load_future_plans(self):
        """
        Loads all confirmed future plans from future_plans.json.
        Returns a dict: { "YYYY-MM-DD": plan_dict, ... }
        """
        data = sm.load_json("future_plans.json", {})
        if not isinstance(data, dict):
            return {}
        return data

    def save_future_plans(self, future_plans_dict):
        """
        Saves future plans dict to future_plans.json.
        """
        sm.save_json("future_plans.json", future_plans_dict)

    def get_future_plan(self, date_str):
        """
        Returns the confirmed future plan for date_str, or None.
        """
        plans = self.load_future_plans()
        return plans.get(str(date_str).strip())

    def save_future_plan(self, date_str, plan_dict):
        """
        Saves or updates a confirmed future plan for a specific date.
        """
        plans = self.load_future_plans()
        date_key = str(date_str).strip()
        plan_dict["date"] = date_key
        plan_dict["status"] = "future_confirmed"
        if not plan_dict.get("confirmed_at"):
            plan_dict["confirmed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        plans[date_key] = plan_dict
        self.save_future_plans(plans)
        return plan_dict

    def delete_future_plan(self, date_str):
        """
        Deletes a confirmed future plan for date_str.
        """
        plans = self.load_future_plans()
        date_key = str(date_str).strip()
        if date_key in plans:
            del plans[date_key]
            self.save_future_plans(plans)
            return True
        return False

    # ========================================================
    # LIFECYCLE: ACTIVE PLAN (TODAY)
    # ========================================================

    def load_active_plan(self):
        """
        Loads the currently active execution plan from active_plan.json.
        Returns plan dict or None if no plan is active today.
        """
        data = sm.load_json("active_plan.json", None)
        if not isinstance(data, dict):
            return None
        return data

    def save_active_plan(self, plan_dict):
        """
        Saves the active execution plan.
        """
        if plan_dict:
            plan_dict["status"] = "active"
            if not plan_dict.get("confirmed_at"):
                plan_dict["confirmed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sm.save_json("active_plan.json", plan_dict)
        return plan_dict

    def clear_active_plan(self):
        """
        Clears the active execution plan.
        """
        sm.save_json("active_plan.json", None)

    def update_active_plan_task(self, task_id, updates):
        """
        Updates a specific task or scheduled item in the active plan.
        """
        active = self.load_active_plan()
        if not active:
            return False

        found = False
        # Update schedule item
        for item in active.get("schedule", []):
            if item.get("task_id") == task_id or item.get("title") == task_id:
                item.update(updates)
                found = True

        # Update tasks item
        for t in active.get("tasks", []):
            if t.get("task_id") == task_id or t.get("title") == task_id:
                t.update(updates)
                found = True

        if found:
            self.save_active_plan(active)
        return found

    # ========================================================
    # LIFECYCLE: HISTORY FINALIZATION & AUDITED EDITS
    # ========================================================

    def finalize_plan_to_history(self, plan_dict):
        """
        Finalizes an active plan into the permanent history record.
        Preserves complete schedule, tasks, notes, and final statuses.
        """
        if not plan_dict:
            return None

        plan_date = plan_dict.get("date", date.today().isoformat())
        schedule = plan_dict.get("schedule", [])
        tasks = plan_dict.get("tasks", [])
        input_text = plan_dict.get("input_text", "")

        history = sm.load_history()

        # Enforce invariant: ONE COMPLETED DAY = ONE HISTORY RECORD
        # Collect any existing audit trail entries across all records for this date
        existing_audits = []
        for rec in history:
            if rec.get("date") == plan_date:
                for a in rec.get("audit_trail", []):
                    if a not in existing_audits:
                        existing_audits.append(a)

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        record = {
            "record_id": plan_dict.get("plan_id") or uuid.uuid4().hex[:8],
            "date": plan_date,
            "created_at": plan_dict.get("created_at") or now_str,
            "finalized_at": now_str,
            "schedule": schedule,
            "tasks": tasks,
            "input_text": input_text,
            "status": "finalized",
            "audit_trail": plan_dict.get("audit_trail", []),
            "is_edited": plan_dict.get("is_edited", False),
        }

        if "audit_trail" in plan_dict:
            record["audit_trail"] = list(plan_dict["audit_trail"])
            record["is_edited"] = plan_dict.get("is_edited", bool(plan_dict["audit_trail"]))
        else:
            record["audit_trail"] = existing_audits
            record["is_edited"] = bool(existing_audits)

        # Remove ALL records matching this date (consolidates duplicates)
        new_history = [rec for rec in history if rec.get("date") != plan_date]
        new_history.append(record)

        sm.save_history(new_history)

        # If this plan was the active plan, clear it
        curr_active = self.load_active_plan()
        if curr_active and curr_active.get("date") == plan_date:
            self.clear_active_plan()

        return record

    def consolidate_history(self):
        """
        Consolidates duplicate historical records per date:
        - Exactly one record per date.
        - Preserves most complete finalized record.
        - Preserves all audit trail entries, notes, and task statuses.
        """
        history = sm.load_history()
        if not history:
            return []

        by_date = {}
        for rec in history:
            d = rec.get("date")
            if not d:
                continue
            if d not in by_date:
                by_date[d] = []
            by_date[d].append(rec)

        consolidated = []
        for d, recs in by_date.items():
            if len(recs) == 1:
                consolidated.append(recs[0])
                continue

            def _score(r):
                is_fin = 1 if r.get("status") == "finalized" else 0
                ts = r.get("finalized_at") or r.get("created_at") or ""
                task_cnt = len(r.get("schedule", []) or r.get("tasks", []))
                return (is_fin, task_cnt, ts)

            best = dict(max(recs, key=_score))

            all_audits = []
            for r in recs:
                for a in r.get("audit_trail", []):
                    if a not in all_audits:
                        all_audits.append(a)
            best["audit_trail"] = all_audits
            best["is_edited"] = bool(all_audits) or best.get("is_edited", False)

            consolidated.append(best)

        consolidated.sort(key=lambda r: r.get("date", ""))
        sm.save_history(consolidated)
        return consolidated

    def edit_historical_task(self, plan_date, task_id, changes, mandatory_note):
        """
        Controlled historical edit workflow.
        A non-empty mandatory_note is required.
        Preserves original state, updates record, and appends an audit trail entry.
        """
        if not mandatory_note or not str(mandatory_note).strip():
            raise ValueError("A non-empty note is mandatory for historical edits.")

        history = sm.load_history()
        target_record = None
        record_idx = -1

        for i, rec in enumerate(history):
            if rec.get("date") == plan_date:
                target_record = rec
                record_idx = i
                break

        if not target_record:
            raise ValueError(f"No historical record found for date '{plan_date}'.")

        # Find task in schedule or tasks
        found_task = None
        original_state = None

        for item in target_record.get("schedule", []):
            if item.get("task_id") == task_id or item.get("title") == task_id:
                found_task = item
                original_state = dict(item)
                break

        if not found_task:
            for item in target_record.get("tasks", []):
                if item.get("task_id") == task_id or item.get("title") == task_id:
                    found_task = item
                    original_state = dict(item)
                    break

        if not found_task:
            raise ValueError(f"Task '{task_id}' not found in historical record for '{plan_date}'.")

        # Apply changes
        for k, v in changes.items():
            found_task[k] = v

        found_task["is_edited"] = True
        found_task["edit_note"] = mandatory_note.strip()

        # Audit trail entry
        if "audit_trail" not in target_record or not isinstance(target_record["audit_trail"], list):
            target_record["audit_trail"] = []

        audit_entry = {
            "edit_id": uuid.uuid4().hex[:8],
            "edited_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "task_id": task_id,
            "task_title": found_task.get("title", ""),
            "original_state": original_state,
            "new_state": dict(found_task),
            "edit_reason": mandatory_note.strip(),
        }
        target_record["audit_trail"].append(audit_entry)
        target_record["is_edited"] = True

        history[record_idx] = target_record
        sm.save_history(history)
        return True, target_record

    # ========================================================
    # LIFECYCLE: DAY ROLLOVER & AUTO-FINALIZATION
    # ========================================================

    def check_and_process_rollover(self, current_date=None):
        """
        Determines the current date, finalizes any past active plan into history,
        and promotes any confirmed future plan scheduled for today into the active plan.
        Safe to call on application boot or date checks.
        """
        from utils.date_utils import today_str, is_past_date
        current_today = current_date or today_str()
        results = {
            "finalized_past_plans": [],
            "promoted_future_plan": None,
        }

        # 1. Finalize past active plan
        active = self.load_active_plan()
        if active:
            active_date = active.get("date")
            if active_date and is_past_date(active_date, reference_date=current_today):
                self.finalize_plan_to_history(active)
                results["finalized_past_plans"].append(active_date)
                active = None

        # 2. Check if a confirmed future plan exists for today
        today_future_plan = self.get_future_plan(current_today)
        if today_future_plan and not active:
            # Promote to today's active plan
            today_future_plan["status"] = "active"
            self.save_active_plan(today_future_plan)
            self.delete_future_plan(current_today)
            results["promoted_future_plan"] = current_today

        return results



