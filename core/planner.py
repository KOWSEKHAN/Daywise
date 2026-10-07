"""
core/planner.py

STEP 17 – Full Pipeline Orchestration

The Planner coordinates the complete DayWise pipeline:

  User input
    ↓
  Parser          (detect tasks, dates, durations, …)
    ↓
  Fixed-event check (requires clarification?)
    ↓  YES → return needs_clarification dict (NO saving, NO scheduling)
    ↓  NO  →
  Memory          (extract & store long-term facts)
    ↓
  Task storage    (persist parsed tasks to tasks.json)
    ↓
  Scheduler       (generate intelligent daily schedule)
    ↓
  History storage (save generated plan to history.json)
    ↓
  Return result   (schedule + plan record)

The Planner does NOT contain UI logic.
"""

import re
from datetime import date, datetime

from core.parser import Parser
from core.scheduler import schedule_tasks
from core.memory import MemoryManager
from storage.data_manager import DataManager
from storage import storage_manager as sm


# ============================================================
# MULTI-TASK INPUT SPLITTER
# ============================================================

def split_compound_input(text):
    """
    Splits a compound user sentence into individual task phrases,
    preserving relationship context for EACH sub-task.

    Key improvements:
    - "exercise and breakfast before college" → BOTH get "before college"
    - "after college I need to prepare..." → AFTER relationship kept
    - Sequential "then" clauses preserve PREVIOUS_TASK reference
    """
    if not text or not text.strip():
        return []

    sentences = re.split(r"[.;!?]+", text)
    clauses = []

    # Intro-level relationship prefix patterns (whole-sentence level)
    intro_patterns = [
        (r"^(?:before\s+that|before\s+it|before\s+class|before\s+college\s+class),?\s*",
         "before college class"),
        (r"^(?:before\s+college)\b,?\s*", "before college"),
        (r"^(?:after\s+lunch),?\s*", "after lunch"),
        (r"^(?:after\s+work),?\s*", "after work"),
        (r"^(?:after\s+college\s+class),?\s*", "after college class"),
        (r"^(?:after\s+college)\b,?\s*", "after college"),
        (r"^(?:after\s+class),?\s*", "after class"),
        (r"^(?:after\s+that|after\s+it),?\s*", "after that"),
        (r"^(?:in\s+the\s+morning),?\s*", "in the morning"),
        (r"^(?:in\s+the\s+afternoon),?\s*", "in the afternoon"),
        (r"^(?:in\s+the\s+evening),?\s*", "in the evening"),
        (r"^(?:later\s+in\s+the\s+day|later\s+day),?\s*", "later in the day"),
    ]

    # Inline trailing relationship suffix patterns (appended to each sub-task)
    trailing_patterns = [
        r"\bbefore\s+(?:that|it|class|college\s+class|college|the\s+meeting|my\s+meeting|meeting|the\s+interview|my\s+interview|interview|work)\b",
        r"\bafter\s+(?:that|it|lunch|class|college\s+class|college|the\s+meeting|my\s+meeting|meeting|the\s+interview|my\s+interview|interview|work)\b",
        r"\blater\s+in\s+the\s+day\b",
        r"\bin\s+the\s+evening\b",
        r"\bin\s+the\s+morning\b",
        r"\bin\s+the\s+afternoon\b",
        r"\bby\s+evening\b",
    ]

    def extract_trailing_suffix(phrase):
        """Extract trailing relationship / time-of-day suffix from phrase."""
        phrase_lower = phrase.lower()
        for pat in trailing_patterns:
            m = re.search(pat, phrase_lower)
            if m:
                return " " + phrase[m.start():m.end()]
        return ""

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        # Extract intro relationship prefix
        prefix = ""
        matched_text = sentence
        for pat, _label in intro_patterns:
            m = re.match(pat, sentence, flags=re.IGNORECASE)
            if m:
                prefix = m.group(0).strip()
                matched_text = sentence[m.end():].strip()
                break

        # Extract trailing suffix from the whole clause (applied to all sub-items)
        trailing_suffix = extract_trailing_suffix(matched_text)

        # Remove trailing suffix from matched_text before splitting
        if trailing_suffix:
            ts_stripped = trailing_suffix.strip()
            idx = matched_text.lower().rfind(ts_stripped.lower())
            if idx != -1:
                matched_text = matched_text[:idx].strip(" ,")

        # Split on commas and "and" (but NOT "and then" which we handle below)
        # We do NOT split on "then" here — that is handled as a sequential connector
        parts = re.split(r",\s*(?:and\s+)?|\band\b", matched_text, flags=re.IGNORECASE)
        valid_parts = [p.strip() for p in parts if p.strip()]

        for p in valid_parts:
            combined = ""
            if prefix:
                combined = f"{prefix} {p}{trailing_suffix}"
            else:
                combined = f"{p}{trailing_suffix}"

            combined = combined.strip()
            if combined:
                clauses.append(combined)

    return clauses if clauses else [text.strip()]


# ============================================================
# CLARIFICATION STATE HELPERS
# ============================================================

def check_needs_clarification(parsed_tasks):
    """
    Iterates parsed tasks and returns the FIRST clarification needed.
    Inspects the already-stored start_time/end_time on the task dict
    (which may have been updated by a prior clarification round) rather
    than re-parsing the original text.
    Returns a dict with needs_clarification=True, or None.
    """
    parser = Parser()
    for task in parsed_tasks:
        if task.get("requires_time") or task.get("time_type") == "missing":
            title = task.get("title", "")
            has_start = bool(task.get("start_time"))
            has_end   = bool(task.get("end_time"))

            # Look up question strings from the parser's FIXED_EVENT_KEYWORDS table
            from core.parser import FIXED_EVENT_KEYWORDS
            meta = None
            for kw, info in sorted(FIXED_EVENT_KEYWORDS.items(), key=lambda x: -len(x[0])):
                if title.lower().startswith(info["title"].lower()) or info["title"].lower() == title.lower():
                    meta = info
                    break

            q_start = (meta["q_start"] if meta else f"What time does '{title}' start?")
            q_end   = (meta["q_end"]   if meta else f"What time does '{title}' end?")

            if not has_start:
                return {
                    "needs_clarification": True,
                    "question":   q_start,
                    "field":      "start_time",
                    "task_title": title,
                }
            elif not has_end:
                return {
                    "needs_clarification": True,
                    "question":   q_end,
                    "field":      "end_time",
                    "task_title": title,
                }
    return None


def apply_clarification_answer(parsed_tasks, field, value, task_title):
    """
    Updates parsed tasks with the user's answer to a clarification question.
    Also updates time_type and requires_time flags accordingly.
    """
    from core.scheduler import time_to_minutes, minutes_to_time
    parser = Parser()
    parsed_time = parser.parse_time_answer(value)

    for task in parsed_tasks:
        title = task.get("title", "")
        if title.lower() == task_title.lower():
            if parsed_time:
                if field == "start_time":
                    task["start_time"] = parsed_time
                    task["time"] = parsed_time
                    # If we now have start but not end, still needs clarification
                    if not task.get("end_time"):
                        task["requires_time"] = True
                        task["time_type"] = "missing"
                    else:
                        task["requires_time"] = False
                        task["time_type"] = "fixed"
                        task["type"] = "event"
                        sh, sm = map(int, task["start_time"].split(":"))
                        eh, em = map(int, task["end_time"].split(":"))
                        task["duration"] = (eh * 60 + em) - (sh * 60 + sm)

                elif field == "end_time":
                    task["end_time"] = parsed_time
                    if task.get("start_time"):
                        task["requires_time"] = False
                        task["time_type"] = "fixed"
                        task["type"] = "event"
                        sh, sm2 = map(int, task["start_time"].split(":"))
                        eh, em = map(int, task["end_time"].split(":"))
                        task["duration"] = (eh * 60 + em) - (sh * 60 + sm2)

    return parsed_tasks


# ============================================================
# DEDUPLICATION HELPERS
# ============================================================

# Title pairs that represent the same activity when both appear
_DUPLICATE_TITLE_GROUPS = [
    {"breakfast", "have breakfast", "eat breakfast"},
    {"lunch", "have lunch", "eat lunch"},
    {"dinner", "have dinner", "eat dinner"},
    {"exercise", "workout", "gym", "do exercise"},
]

def _canonical_title(title):
    t = title.lower().strip()
    for group in _DUPLICATE_TITLE_GROUPS:
        if t in group:
            return min(group)  # consistent canonical representative
    return t


def deduplicate_parsed_tasks(parsed_tasks, routine_titles):
    """
    Removes tasks from parsed_tasks whose title is already covered
    by a default routine, to prevent double-scheduling.
    Routine titles win over user task declarations of the same activity.
    """
    # Normalise routine titles to canonical forms
    routine_canonical = {_canonical_title(rt) for rt in routine_titles}

    deduped = []
    seen_canonical = set()

    for task in parsed_tasks:
        title = task.get("title", "")
        if not title:
            deduped.append(task)
            continue
        canon = _canonical_title(title)
        # If same activity already in routines AND NOT explicitly needed as
        # a before/after relationship anchor, suppress the duplicate task.
        if canon in routine_canonical and not task.get("before_task") and not task.get("after_task"):
            continue
        if canon in seen_canonical:
            continue
        seen_canonical.add(canon)
        deduped.append(task)

    return deduped


# ============================================================
# PLANNER CLASS
# ============================================================

class Planner:
    """
    Central orchestration layer for DayWise.
    """

    def __init__(self):
        self.parser = Parser()
        self.memory = MemoryManager()
        self.data_manager = DataManager()

    # --------------------------------------------------------
    # MAIN PLAN METHOD
    # --------------------------------------------------------

    def plan(self, user_input, plan_date=None, _pending_tasks=None):
        """
        Processes user input through the full pipeline.

        Returns one of:

        A) Clarification needed (no saving, no scheduling):
          {
            "needs_clarification": True,
            "question":  "...",
            "field":     "start_time" | "end_time",
            "task_title": "...",
            "pending_tasks": [...],   ← preserved for follow-up calls
            "original_input": "...",
            "plan_date": "...",
          }

        B) Successful plan:
          {
            "schedule": [...],
            "tasks":    [...],
            "plan_record": {...},
            "memory_stored": [...],
            "error": None,
          }
        """
        if not user_input or not user_input.strip():
            return {
                "schedule": [],
                "tasks": [],
                "plan_record": None,
                "memory_stored": [],
                "error": "No input provided.",
            }

        # ------------------------------------------------
        # Determine plan date
        # ------------------------------------------------
        overall_date = self.parser.detect_date(user_input)
        if overall_date:
            plan_date = overall_date
        elif plan_date is None:
            plan_date = date.today().isoformat()

        # ------------------------------------------------
        # 1. Extract and store long-term memory facts
        #    (do this even during clarification loop)
        # ------------------------------------------------
        memory_stored = self.memory.extract_and_store(user_input)

        # ------------------------------------------------
        # 2. Split compound input into individual clauses
        # ------------------------------------------------
        phrases = split_compound_input(user_input)

        # ------------------------------------------------
        # 3. Parse each phrase & link relationships
        # ------------------------------------------------
        parsed_tasks = [] if _pending_tasks is None else list(_pending_tasks)

        last_independent_title = None

        # When re-entering with pending tasks, use those titles as context
        if parsed_tasks:
            for pt in parsed_tasks:
                t = pt.get("title")
                if t and not pt.get("before_task"):
                    last_independent_title = t

        # Parse new phrases (only when NOT continuing from pending)
        if _pending_tasks is None:
            for phrase in phrases:
                try:
                    result = self.parser.parse(phrase)
                    clean_title = result.get("title")

                    if not clean_title:
                        continue

                    # Deduplicate identical titles in same pipeline call
                    if parsed_tasks and parsed_tasks[-1].get("title") == clean_title:
                        continue

                    # Link relative before/after targets
                    b_task = result.get("before_task")
                    a_task = result.get("after_task")

                    if b_task == "PREVIOUS_TASK":
                        b_task = last_independent_title
                        result["before_task"] = b_task

                    if a_task == "PREVIOUS_TASK":
                        a_task = last_independent_title
                        result["after_task"] = a_task

                    rel = None
                    if b_task:
                        rel = {"type": "before", "target": b_task}
                    elif a_task:
                        rel = {"type": "after", "target": a_task}

                    result["relationship"] = rel

                    if not result.get("date") or overall_date:
                        result["date"] = plan_date

                    parsed_tasks.append(result)

                    if not result.get("before_task") and clean_title not in ("Exercise", "Breakfast"):
                        last_independent_title = clean_title

                except Exception:
                    pass

        if not parsed_tasks:
            return {
                "schedule": [],
                "tasks": [],
                "plan_record": None,
                "memory_stored": memory_stored,
                "error": "Could not parse any tasks from input.",
            }

        # ------------------------------------------------
        # 4. CHECK FOR CLARIFICATION BEFORE ANYTHING ELSE
        #    Do NOT save, do NOT schedule, do NOT save history
        # ------------------------------------------------
        clarification = check_needs_clarification(parsed_tasks)
        if clarification:
            return {
                "needs_clarification": True,
                "question":   clarification["question"],
                "field":      clarification["field"],
                "task_title": clarification["task_title"],
                "pending_tasks":   parsed_tasks,
                "original_input":  user_input,
                "plan_date":       plan_date,
                "memory_stored":   memory_stored,
            }

        # ------------------------------------------------
        # 5. Apply memory preferences
        # ------------------------------------------------
        study_pref = self.memory.get_study_preference_time()

        # ------------------------------------------------
        # 6. Deduplicate tasks against routines
        # ------------------------------------------------
        try:
            routines = self.data_manager.load_routines()
            routine_titles = {
                (r.get("title") or r.get("name", "")).strip()
                for r in routines
                if r.get("enabled", r.get("active", True))
            }
        except Exception:
            routine_titles = set()

        parsed_tasks = deduplicate_parsed_tasks(parsed_tasks, routine_titles)

        # ------------------------------------------------
        # 7. Persist tasks to tasks.json
        # ------------------------------------------------
        stored_tasks = []
        for task in parsed_tasks:
            stored = self.data_manager.add_task(dict(task))
            stored_tasks.append(stored)

        # ------------------------------------------------
        # 8. Generate schedule (also saves to history)
        # ------------------------------------------------
        schedule = schedule_tasks(parsed_tasks, plan_date=plan_date)

        # ------------------------------------------------
        # 9. Save plan record with full context
        # ------------------------------------------------
        plan_record = self.data_manager.save_plan(
            plan_date,
            user_input,
            schedule,
            stored_tasks,
        )

        # ------------------------------------------------
        # 10. Update task statuses to "scheduled"
        # ------------------------------------------------
        for task in stored_tasks:
            tid = task.get("task_id")
            if tid:
                self.data_manager.update_task_status(tid, "scheduled")

        return {
            "schedule": schedule,
            "tasks": stored_tasks,
            "plan_record": plan_record,
            "memory_stored": memory_stored,
            "error": None,
        }

    # --------------------------------------------------------
    # CONTINUE PLAN AFTER CLARIFICATION ANSWER
    # --------------------------------------------------------

    def continue_plan(self, original_input, pending_tasks, plan_date, field, value, task_title):
        """
        Called by the GUI after the user answers a clarification question.

        1. Updates pending_tasks with the new field value.
        2. Calls plan() again – if still needs clarification, returns
           another clarification dict; otherwise returns the final schedule.
        """
        updated_tasks = apply_clarification_answer(
            pending_tasks, field, value, task_title
        )

        return self.plan(
            original_input,
            plan_date=plan_date,
            _pending_tasks=updated_tasks,
        )

    # --------------------------------------------------------
    # QUICK HELPERS (used by GUI)
    # --------------------------------------------------------

    def get_today_plan(self):
        """Returns the most-recent schedule for today."""
        records = self.data_manager.get_plan_for_today()
        if records:
            return records[-1].get("schedule", [])
        return []

    def get_latest_plans(self, limit=10):
        """Returns the latest N history records."""
        return self.data_manager.get_latest_plans(limit)

    def get_plan_for_date(self, plan_date):
        """Returns all schedule records for a specific date."""
        return self.data_manager.get_plan_by_date(plan_date)

    def search_history(self, query):
        """Full-text search across history."""
        return self.data_manager.search_plans(query)

    def load_tasks(self):
        """Loads persistent task list."""
        return self.data_manager.load_tasks()

    def load_routines(self):
        """Loads persistent routines."""
        return self.data_manager.load_routines()

    def load_memory(self):
        """Loads long-term memory."""
        return self.memory.load_memory()

    def update_task_status(self, task_id, new_status):
        """Delegates status update to data manager."""
        return self.data_manager.update_task_status(task_id, new_status)
