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


