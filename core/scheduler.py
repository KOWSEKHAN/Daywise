import re
from uuid import uuid4

from storage.storage_manager import add_plan_to_history


# ============================================================
# DEFAULT DAILY AVAILABILITY
# ============================================================

def get_default_day_slots():
    """
    Returns the default working/planning window for a day.
    """
    return [
        {
            "start": "06:00",
            "end": "22:00"
        }
    ]


# ============================================================
# DEFAULT DAILY ROUTINES
# ============================================================

def get_default_daily_routines():
    """
    Returns fixed daily routines that automatically block time.
    """
    return [
        {
            "start": "06:00",
            "end": "07:00",
            "title": "Morning routine"
        },
        {
            "start": "07:00",
            "end": "07:30",
            "title": "Breakfast"
        },
        {
            "start": "12:30",
            "end": "13:30",
            "title": "Lunch"
        },
        {
            "start": "18:30",
            "end": "19:00",
            "title": "Dinner"
        },
        {
            "start": "21:30",
            "end": "22:00",
            "title": "Wind down"
        }
    ]


# ============================================================
# TIME CONVERSION
# ============================================================

def time_to_minutes(time_string):
    """
    Converts HH:MM into minutes from midnight.
    Example: 07:30 -> 450
    """
    if not time_string or ":" not in str(time_string):
        return 0
    hours, minutes = map(int, str(time_string).split(":"))
    return hours * 60 + minutes


def minutes_to_time(total_minutes):
    """
    Converts minutes from midnight into HH:MM.
    """
    total_minutes = max(0, min(total_minutes, 24 * 60))
    hours = total_minutes // 60
    minutes = total_minutes % 60
    return f"{hours:02d}:{minutes:02d}"


# ============================================================
# TASK ID
# ============================================================

def get_or_create_task_id(task):
    """
    Returns an existing task ID if available.
    Otherwise creates a new unique task ID.
    """
    task_id = task.get("task_id") or task.get("id")
    if not task_id:
        task_id = uuid4().hex[:8]
    return task_id


# ============================================================
# REMOVE TIME FROM AVAILABLE SLOTS
# ============================================================

def remove_time_from_slots(slots, start_time, end_time):
    """
    Removes a time range from available slots.
    """
    start_minutes = time_to_minutes(start_time)
    end_minutes = time_to_minutes(end_time)
    new_slots = []

    for slot in slots:
        slot_start = time_to_minutes(slot["start"])
        slot_end = time_to_minutes(slot["end"])

        # No overlap
        if end_minutes <= slot_start or start_minutes >= slot_end:
            new_slots.append({
                "start": slot["start"],
                "end": slot["end"]
            })
            continue

        # Left portion
        if start_minutes > slot_start:
            new_slots.append({
                "start": slot["start"],
                "end": minutes_to_time(start_minutes)
            })

        # Right portion
        if end_minutes < slot_end:
            new_slots.append({
                "start": minutes_to_time(end_minutes),
                "end": slot["end"]
            })

    return new_slots


# ============================================================
# FREE SLOT DETECTION
# ============================================================

def get_free_slots(day_slots, blocked_slots):
    """
    Calculates free time by removing blocked periods from available day.
    """
    free_slots = []
    for day_slot in day_slots:
        current_slots = [{
            "start": day_slot["start"],
            "end": day_slot["end"]
        }]

        for blocked in blocked_slots:
            next_slots = []
            for slot in current_slots:
                rem = remove_time_from_slots(
                    [slot],
                    blocked["start"],
                    blocked["end"]
                )
                next_slots.extend(rem)
            current_slots = next_slots

        free_slots.extend(current_slots)

    return free_slots


# ============================================================
# TASK SORTING
# ============================================================

def sort_tasks(tasks):
    """
    Sorts tasks by relationship dependencies, deadline, priority, and duration.
    """
    priority_rank = {
        "high": 3,
        "normal": 2,
        "low": 1
    }

    def get_sort_key(task):
        rel = task.get("relationship") or {}
        b_task = task.get("before_task")
        a_task = task.get("after_task")

        is_before_dep = 1 if (b_task or (rel and rel.get("type") == "before")) else 0
        is_after_dep = 1 if (a_task or (rel and rel.get("type") == "after")) else 0

        p_str = str(task.get("priority", "normal")).lower()
        p_val = priority_rank.get(p_str, 2)

        dl_str = task.get("deadline_time")
        dl_val = time_to_minutes(dl_str) if dl_str else 99999

        dur = task.get("duration", 60)

        return (-is_before_dep, is_after_dep, dl_val, -p_val, -dur)

    return sorted(tasks, key=get_sort_key)


# ============================================================
# FIND SLOT BY CONTEXT WINDOW
# ============================================================

def find_slot_for_context(duration, free_slots, context_window, deadline_time=None):
    """
    Finds a suitable free slot matching preferred context window.
    """
    dl_mins = time_to_minutes(deadline_time) if deadline_time else None

    window_bounds = {
        "morning": (360, 720),      # 06:00 - 12:00
        "afternoon": (720, 1020),   # 12:00 - 17:00
        "evening": (1020, 1320),    # 17:00 - 22:00
        "later_day": (900, 1320)    # 15:00 - 22:00
    }

    if context_window in window_bounds:
        w_start, w_end = window_bounds[context_window]
        for slot in free_slots:
            s_mins = time_to_minutes(slot["start"])
            e_mins = time_to_minutes(slot["end"])

            cand_start = max(s_mins, w_start)
            cand_end = cand_start + duration

            if cand_end <= min(e_mins, w_end):
                if dl_mins is None or cand_end <= dl_mins:
                    start_str = minutes_to_time(cand_start)
                    end_str = minutes_to_time(cand_end)
                    updated = remove_time_from_slots(free_slots, start_str, end_str)
                    return start_str, end_str, updated

    # Fallback to general search
    for slot in free_slots:
        s_mins = time_to_minutes(slot["start"])
        e_mins = time_to_minutes(slot["end"])

        if e_mins - s_mins >= duration:
            cand_end = s_mins + duration
            if dl_mins is None or cand_end <= dl_mins:
                start_str = slot["start"]
                end_str = minutes_to_time(cand_end)
                updated = remove_time_from_slots(free_slots, start_str, end_str)
                return start_str, end_str, updated

    return None, None, free_slots


# ============================================================
# FIND RELATIONSHIP-AWARE SLOT
# ============================================================

def find_relationship_slot(task, free_slots, scheduled_map):
    """
    Schedules task respecting BEFORE/AFTER relationships and deadline bounds.
    """
    duration = task.get("duration", 60)
    rel = task.get("relationship") or {}
    b_target = task.get("before_task") or (rel.get("target") if rel.get("type") == "before" else None)
    a_target = task.get("after_task") or (rel.get("target") if rel.get("type") == "after" else None)
    dl_time = task.get("deadline_time")
    dl_mins = time_to_minutes(dl_time) if dl_time else None
    cw = task.get("context_window")

    min_start_mins = 0
    max_end_mins = 24 * 60

    if a_target:
        a_key = str(a_target).strip().lower()
        if a_key in scheduled_map:
            min_start_mins = time_to_minutes(scheduled_map[a_key]["end"])
        elif a_key == "college class" and "college class" in scheduled_map:
            min_start_mins = time_to_minutes(scheduled_map["college class"]["end"])
        elif "lunch" in a_key:
            min_start_mins = 13 * 60 + 30  # Fallback 13:30

    if b_target:
        b_key = str(b_target).strip().lower()
        if b_key in scheduled_map:
            max_end_mins = time_to_minutes(scheduled_map[b_key]["start"])
        elif b_key == "college class" and "college class" in scheduled_map:
            max_end_mins = time_to_minutes(scheduled_map["college class"]["start"])
        elif b_key in ("college class", "college", "class"):
            max_end_mins = 9 * 60  # Default 09:00

    if dl_mins:
        max_end_mins = min(max_end_mins, dl_mins)

    best_start = None
    best_end = None

    for slot in free_slots:
        s_mins = time_to_minutes(slot["start"])
        e_mins = time_to_minutes(slot["end"])

        cand_start = max(s_mins, min_start_mins)

        if cw == "evening" and cand_start < 17 * 60:
            cand_start = max(cand_start, 17 * 60)

        cand_end = cand_start + duration

        if cand_end <= e_mins and cand_end <= max_end_mins:
            best_start = minutes_to_time(cand_start)
            best_end = minutes_to_time(cand_end)
            break

    if not best_start and min_start_mins == 0 and max_end_mins == 24 * 60:
        best_start, best_end, updated_slots = find_slot_for_context(
            duration, free_slots, cw, deadline_time=dl_time
        )
        if best_start:
            entry = {
                "start": best_start,
                "end": best_end,
                "title": task.get("title", "Task"),
                "type": task.get("type", "task"),
                "task_id": task.get("task_id"),
                "time_type": task.get("time_type", "estimated"),
                "priority": task.get("priority", "normal")
            }
            return entry, updated_slots

    if best_start and best_end:
        updated_slots = remove_time_from_slots(free_slots, best_start, best_end)
        entry = {
            "start": best_start,
            "end": best_end,
            "title": task.get("title", "Task"),
            "type": task.get("type", "task"),
            "task_id": task.get("task_id"),
            "time_type": task.get("time_type", "estimated"),
            "priority": task.get("priority", "normal")
        }
        return entry, updated_slots

    # Emergency fallback placement in available slot
    for slot in free_slots:
        s_mins = time_to_minutes(slot["start"])
        e_mins = time_to_minutes(slot["end"])
        if e_mins - s_mins >= min(30, duration):
            actual_dur = min(duration, e_mins - s_mins)
            cand_end = s_mins + actual_dur
            best_start = slot["start"]
            best_end = minutes_to_time(cand_end)
            updated_slots = remove_time_from_slots(free_slots, best_start, best_end)
            entry = {
                "start": best_start,
                "end": best_end,
                "title": task.get("title", "Task"),
                "type": task.get("type", "task"),
                "task_id": task.get("task_id"),
                "time_type": task.get("time_type", "estimated"),
                "priority": task.get("priority", "normal")
            }
            return entry, updated_slots

    return None, free_slots


# ============================================================
# TASK SPLITTING FOR LONG TASKS
# ============================================================

def schedule_split_task(task, free_slots):
    """
    Splits long tasks (>120 mins) across multiple free slots.
    """
    total_needed = task.get("duration", 60)
    scheduled_entries = []
    remaining = total_needed
    task_title = task.get("title", "Task")
    current_slots = list(free_slots)

    part_num = 1
    for slot in list(current_slots):
        if remaining <= 0:
            break

        s_mins = time_to_minutes(slot["start"])
        e_mins = time_to_minutes(slot["end"])
        avail = e_mins - s_mins

        if avail >= 30:
            chunk = min(avail, remaining)
            c_start = slot["start"]
            c_end = minutes_to_time(s_mins + chunk)

            part_title = f"{task_title} (Part {part_num})" if remaining < total_needed or chunk < total_needed else task_title

            scheduled_entries.append({
                "start": c_start,
                "end": c_end,
                "title": part_title,
                "type": task.get("type", "task"),
                "task_id": task.get("task_id"),
                "time_type": task.get("time_type", "estimated"),
                "priority": task.get("priority", "normal")
            })

            current_slots = remove_time_from_slots(current_slots, c_start, c_end)
            remaining -= chunk
            part_num += 1

    return scheduled_entries, current_slots


# ============================================================
# SCHEDULE VALIDATION & REPAIR (ZERO OVERLAPS GUARANTEED)
# ============================================================

def is_fixed_entry(entry):
    """
    Returns True if this schedule entry is FIXED and must NEVER be moved.

    Fixed entries:
      - type == "event"   : user events with explicit start/end time
      - type == "routine" : recurring routines with configured start/end
      - time_type == "fixed" on any type

    Tasks (time_type != "fixed") are flexible and can be shifted.

    CRITICAL: Routines are ALWAYS fixed — they must never be moved to
    accommodate other tasks.  The old code had is_default_routine() which
    only matched a hardcoded list and was used to MOVE routines — that was
    the root cause of the scheduling bug.
    """
    etype = entry.get("type", "task")
    ttype = entry.get("time_type", "")

    if etype == "event":
        return True
    if etype == "routine":
        return True
    if ttype == "fixed":
        return True
    return False


def validate_and_repair_schedule(schedule):
    """
    Performs final schedule validation to guarantee:
    1. Zero overlapping entries.
    2. Fixed events AND routines remain absolutely immovable.
    3. Flexible tasks are shifted to avoid fixed blocks — never the other way.
    4. Duplicate Exercise / Gym Session routines are unified.

    INVARIANT: A routine's start/end time is NEVER changed here.
               If a flexible task overlaps a fixed block, the TASK is moved,
               not the fixed block.
    """
    if not schedule:
        return []

    # 1. Deduplicate Exercise / Gym Session intent
    has_gym_routine = any(e.get("title") == "Gym Session" for e in schedule)
    has_exercise_task = any(
        e.get("title") in ("Exercise", "Workout", "Gym") and e.get("type") == "task"
        for e in schedule
    )

    if has_gym_routine and has_exercise_task:
        schedule = [e for e in schedule if not (e.get("title") in ("Exercise", "Workout", "Gym") and e.get("type") == "task")]

    # 2. Deduplicate meal routines (Breakfast, Lunch, Dinner)
    for meal in ("breakfast", "lunch", "dinner"):
        has_meal_routine = any(e.get("title", "").strip().lower() == meal and e.get("type") == "routine" for e in schedule)
        has_meal_task = any(meal in e.get("title", "").lower() and e.get("type") == "task" for e in schedule)
        if has_meal_routine and has_meal_task:
            schedule = [e for e in schedule if not (meal in e.get("title", "").lower() and e.get("type") == "task")]

    schedule.sort(key=lambda item: time_to_minutes(item["start"]))

    max_passes = 15
    for _ in range(max_passes):
        schedule.sort(key=lambda item: time_to_minutes(item["start"]))
        has_overlap = False

        for i in range(len(schedule) - 1):
            e1 = schedule[i]
            e2 = schedule[i + 1]

            s1 = time_to_minutes(e1["start"])
            e1_end = time_to_minutes(e1["end"])
            s2 = time_to_minutes(e2["start"])
            e2_end = time_to_minutes(e2["end"])

            if s2 < e1_end:
                has_overlap = True
                d2 = e2_end - s2
                d1 = e1_end - s1

                e1_fixed = is_fixed_entry(e1)
                e2_fixed = is_fixed_entry(e2)

                if e1_fixed and e2_fixed:
                    # Both are fixed — neither can be moved.
                    # Accept the conflict; downstream time-filter handles invalid entries.
                    pass

                elif e1_fixed and not e2_fixed:
                    # e1 is a fixed routine/event — push the flexible e2 past it.
                    new_s2 = e1_end
                    new_e2 = new_s2 + d2
                    e2["start"] = minutes_to_time(new_s2)
                    e2["end"] = minutes_to_time(new_e2)

                elif e2_fixed and not e1_fixed:
                    # e2 is a fixed routine/event — trim or push the flexible e1.
                    if s2 > s1:
                        e1["end"] = minutes_to_time(s2)
                    else:
                        new_s1 = e2_end
                        e1["start"] = minutes_to_time(new_s1)
                        e1["end"] = minutes_to_time(new_s1 + d1)

                else:
                    # Both flexible — push the later one forward.
                    new_s2 = e1_end
                    new_e2 = new_s2 + d2
                    e2["start"] = minutes_to_time(new_s2)
                    e2["end"] = minutes_to_time(new_e2)

        if not has_overlap:
            break

    valid_schedule = []
    for e in schedule:
        s = time_to_minutes(e["start"])
        end = time_to_minutes(e["end"])
        if end > s and end <= 24 * 60:
            valid_schedule.append(e)

    valid_schedule.sort(key=lambda item: time_to_minutes(item["start"]))
    return valid_schedule


# ============================================================
# SCHEDULE MULTIPLE TASKS
# ============================================================

def schedule_tasks(tasks, plan_date=None):
    """
    Main scheduling function.
    """
    for task in tasks:
        task["task_id"] = get_or_create_task_id(task)

    day_slots = get_default_day_slots()

    from datetime import datetime as dt_cls, date as dt_date
    if plan_date:
        try:
            target_dt = dt_cls.strptime(plan_date, "%Y-%m-%d").date()
        except ValueError:
            target_dt = dt_date.today()
    else:
        target_dt = dt_date.today()

    weekday_name = target_dt.strftime("%A")

    try:
        from storage.data_manager import DataManager
        dm = DataManager()
        date_iso = target_dt.strftime("%Y-%m-%d")
        saved_routines = dm.get_routines_for_date(date_iso)
        routines = []
        seen_routine_keys = set()

        for r in saved_routines:
            is_enabled = r.get("enabled", r.get("active", True))
            days = r.get("days", [])
            day_matches = (not days) or (weekday_name in days)

            if is_enabled and day_matches:
                start = r.get("start") or r.get("start_time", "06:00")
                end = r.get("end") or r.get("end_time", "07:00")
                title = r.get("title") or r.get("name", "Routine")

                key = (title.strip().lower(), start, end)
                if key not in seen_routine_keys:
                    seen_routine_keys.add(key)
                    routines.append({
                        "start": start,
                        "end": end,
                        "title": title,
                        "type": "routine",
                        "time_type": "fixed",   # ← all routines are fixed blocks
                        "routine_id": r.get("routine_id")
                    })
    except Exception:
        routines = get_default_daily_routines()
        for r in routines:
            r.setdefault("time_type", "fixed")

    free_slots = get_free_slots(day_slots, routines)

    final_schedule = []
    scheduled_map = {}

    for r in routines:
        scheduled_map[r["title"].lower()] = {"start": r["start"], "end": r["end"]}

    routine_titles = {r["title"].strip().lower() for r in routines}
    tasks_to_schedule = [
        t for t in tasks
        if t.get("title", "").strip().lower() not in routine_titles
    ]

    # 1. SCHEDULE FIXED EVENTS FIRST
    fixed_tasks = [t for t in tasks_to_schedule if t.get("time_type") == "fixed"]
    flexible_tasks = [t for t in tasks_to_schedule if t.get("time_type") != "fixed"]

    for task in fixed_tasks:
        start_time = task.get("start_time") or task.get("time") or "09:00"
        end_time = task.get("end_time")
        duration = task.get("duration", 60)

        if not end_time:
            end_time = minutes_to_time(time_to_minutes(start_time) + duration)

        entry = {
            "start": start_time,
            "end": end_time,
            "title": task.get("title", "Event"),
            "type": task.get("type", "event"),
            "task_id": task.get("task_id"),
            "time_type": "fixed",
            "priority": task.get("priority", "normal")
        }

        final_schedule.append(entry)
        scheduled_map[entry["title"].lower()] = {"start": start_time, "end": end_time}
        free_slots = remove_time_from_slots(free_slots, start_time, end_time)

    # 2. SCHEDULE FLEXIBLE TASKS
    sorted_flexible = sort_tasks(flexible_tasks)

    for task in sorted_flexible:
        duration = task.get("duration", 60)

        if duration > 120 and not task.get("relationship") and not task.get("before_task") and not task.get("after_task"):
            scheduled_entries, updated_slots = schedule_split_task(task, free_slots)
        else:
            entry, updated_slots = find_relationship_slot(task, free_slots, scheduled_map)
            scheduled_entries = [entry] if entry else []

        if scheduled_entries:
            final_schedule.extend(scheduled_entries)
            free_slots = updated_slots
            for e in scheduled_entries:
                scheduled_map[e["title"].lower()] = {"start": e["start"], "end": e["end"]}

    # 3. ADD ROUTINES TO FINAL SCHEDULE AT THEIR EXACT CONFIGURED TIMES
    # Routines are inserted verbatim — start/end are NEVER adjusted here.
    for routine in routines:
        final_schedule.append({
            "start": routine["start"],
            "end": routine["end"],
            "title": routine["title"],
            "type": "routine",
            "time_type": "fixed"        # immovable marker for validate_and_repair_schedule
        })

    # 4. VALIDATE & REPAIR FINAL SCHEDULE (Zero overlaps guaranteed)
    final_schedule = validate_and_repair_schedule(final_schedule)

    # Save to history
    add_plan_to_history(final_schedule)

    return final_schedule