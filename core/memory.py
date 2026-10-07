"""
core/memory.py

STEP 15 – Long-term Memory

DayWise remembers useful user information across sessions.

Categories stored:
  preferences       – e.g. "I prefer studying at night"
  routines          – e.g. "I exercise every morning"
  future_events     – e.g. "interview on October 15"
  constraints       – e.g. "college from 9 AM to 4 PM"
  sleep_schedule    – e.g. "I sleep at 10:30 PM"

Memory influences future scheduling:
  - preferred study time  → scheduler adjusts context window
  - college hours         → scheduler blocks that window
  - morning exercise      → scheduler reserves morning slot
"""

import re
from datetime import datetime

from storage import storage_manager as sm


# ============================================================
# MEMORY CATEGORIES
# ============================================================

MEMORY_CATEGORIES = [
    "preferences",
    "routines",
    "future_events",
    "constraints",
    "sleep_schedule",
]


# ============================================================
# MEMORY MANAGER CLASS
# ============================================================

class MemoryManager:
    """
    Manages DayWise long-term memory.

    All memory is stored in data/memory.json as a dict:

    {
        "preferences": [...],
        "routines": [...],
        "future_events": [...],
        "constraints": [...],
        "sleep_schedule": [...],
        "_raw": [...]         ← full text entries
    }
    """

    # --------------------------------------------------------
    # INTERNAL HELPERS
    # --------------------------------------------------------

    def _load(self):
        data = sm.load_json("memory.json", {})
        if not isinstance(data, dict):
            data = {}
        # Migrate old format (flat dict like {"name": "User"})
        # into structured memory if needed
        for cat in MEMORY_CATEGORIES:
            if cat not in data:
                data[cat] = []
        if "_raw" not in data:
            data["_raw"] = []
        return data

    def _save(self, data):
        sm.save_json("memory.json", data)

    # --------------------------------------------------------
    # PUBLIC API
    # --------------------------------------------------------

    def load_memory(self):
        """Returns the full structured memory dict."""
        return self._load()

    def add_memory_entry(self, text, category, note=""):
        """
        Adds a memory entry under the given category.

        Parameters
        ----------
        text     : str – the factual statement to remember
        category : str – one of MEMORY_CATEGORIES
        note     : str – optional extra annotation
        """
        if category not in MEMORY_CATEGORIES:
            category = "preferences"

        data = self._load()

        entry = {
            "text": text,
            "note": note,
            "added_at": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        }

        # Avoid storing the exact same text twice
        existing_texts = [
            e.get("text", "").lower()
            for e in data.get(category, [])
        ]
        if text.lower() not in existing_texts:
            data[category].append(entry)
            data["_raw"].append(
                {"category": category, **entry}
            )

        self._save(data)
        return entry

    def get_preferences(self):
        """Returns stored study/work preferences."""
        return self._load().get("preferences", [])

    def get_constraints(self):
        """Returns schedule constraints (e.g. college hours)."""
        return self._load().get("constraints", [])

    def get_future_events(self):
        """Returns upcoming events stored in memory."""
        return self._load().get("future_events", [])

    def get_routines(self):
        """Returns remembered recurring activities."""
        return self._load().get("routines", [])

    def get_all_entries(self):
        """Returns every memory entry as a flat list."""
        return self._load().get("_raw", [])

    # --------------------------------------------------------
    # RULE-BASED EXTRACTION FROM USER INPUT
    # --------------------------------------------------------

    def extract_and_store(self, text):
        """
        Analyses user input and stores any useful
        long-term facts using simple rule-based matching.

        Returns a list of (category, stored_text) tuples
        for entries that were stored.
        """
        stored = []
        text_lower = text.lower()

        # ---- SLEEP SCHEDULE --------------------------------
        sleep_patterns = [
            r"i (?:usually |normally |always )?sleep at (.+)",
            r"i go to (?:bed|sleep) at (.+)",
            r"bedtime (?:is )?at (.+)",
        ]
        for pat in sleep_patterns:
            m = re.search(pat, text_lower)
            if m:
                fact = f"Sleep at {m.group(1).strip()}"
                self.add_memory_entry(
                    fact, "sleep_schedule"
                )
                stored.append(("sleep_schedule", fact))
                break

        # ---- PREFERENCES -----------------------------------
        preference_patterns = [
            r"i prefer (?:studying|study|working|work|reading|read) (?:at |in the |during the )?(.+)",
            r"i like (?:to )?(?:study|work|exercise|read) (?:at |in the |during the )?(.+)",
            r"i (?:usually|normally|always) (?:study|work|exercise) (?:at |in the |during the )?(.+)",
        ]
        for pat in preference_patterns:
            m = re.search(pat, text_lower)
            if m:
                fact = text.strip()
                self.add_memory_entry(
                    fact, "preferences"
                )
                stored.append(("preferences", fact))
                break

        # ---- CONSTRAINTS (college / work schedule) ---------
        constraint_patterns = [
            r"i have college from (.+) to (.+)",
            r"i have (?:work|office|school|class) from (.+) to (.+)",
            r"college (?:is |hours are )?from (.+) to (.+)",
        ]
        for pat in constraint_patterns:
            m = re.search(pat, text_lower)
            if m:
                fact = f"Schedule constraint: {text.strip()}"
                self.add_memory_entry(
                    fact, "constraints"
                )
                stored.append(("constraints", fact))
                break

        # ---- RECURRING ACTIVITIES --------------------------
        recurring_patterns = [
            r"(?:i )?(?:exercise|gym|workout|jog|run|walk) every (.+)",
            r"(?:i )?(?:study|learn|practice) (?:python|sql|java|programming|coding) every (.+)",
            r"(?:i )?(?:meditate|pray|temple) every (.+)",
        ]
        for pat in recurring_patterns:
            m = re.search(pat, text_lower)
            if m:
                fact = text.strip()
                self.add_memory_entry(
                    fact, "routines"
                )
                stored.append(("routines", fact))
                break

        # ---- FUTURE EVENTS ---------------------------------
        future_patterns = [
            r"i have (?:an? )?(.+?) on (.+)",
            r"(?:my )?(.+?) is on (.+)",
        ]
        # Only store if contains a date-like reference
        date_hints = [
            "january", "february", "march", "april",
            "may", "june", "july", "august",
            "september", "october", "november", "december",
            "monday", "tuesday", "wednesday",
            "thursday", "friday", "saturday", "sunday",
            "tomorrow", "next week", "next month",
        ]
        has_date = any(h in text_lower for h in date_hints)
        if has_date and not stored:
            for pat in future_patterns:
                m = re.search(pat, text_lower)
                if m:
                    fact = text.strip()
                    self.add_memory_entry(
                        fact, "future_events"
                    )
                    stored.append(("future_events", fact))
                    break

        return stored

    # --------------------------------------------------------
    # INFLUENCE ON SCHEDULING
    # --------------------------------------------------------

    def get_study_preference_time(self):
        """
        Reads preferences and returns the preferred
        study time window as (start_str, end_str) or None.

        Examples detected:
          "I prefer studying at night"  → ("20:00", "22:00")
          "I prefer studying in the morning" → ("07:30", "10:00")
          "I prefer studying in the evening" → ("17:00", "20:00")
        """
        prefs = self.get_preferences()
        for entry in prefs:
            text = entry.get("text", "").lower()
            if "stud" in text or "learn" in text:
                if "night" in text or "midnight" in text:
                    return ("20:00", "22:00")
                if "morning" in text:
                    return ("07:30", "10:00")
                if "evening" in text or "afternoon" in text:
                    return ("17:00", "20:00")
        return None
