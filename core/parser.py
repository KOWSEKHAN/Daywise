import re
from datetime import datetime, date, timedelta


# =============================================================
# FIXED EVENT KEYWORDS — events that REQUIRE time clarification
# =============================================================

FIXED_EVENT_KEYWORDS = {
    "college": {
        "title": "College",
        "q_start": "What time do you go to college?",
        "q_end":   "What time do you return from college?",
    },
    "college class": {
        "title": "College Class",
        "q_start": "What time does your college class start?",
        "q_end":   "What time does your college class end?",
    },
    "class": {
        "title": "Class",
        "q_start": "What time does your class start?",
        "q_end":   "What time does your class end?",
    },
    "meeting": {
        "title": "Meeting",
        "q_start": "What time is your meeting?",
        "q_end":   "What time does the meeting end?",
    },
    "appointment": {
        "title": "Appointment",
        "q_start": "What time is your appointment?",
        "q_end":   "What time does the appointment end?",
    },
    "doctor appointment": {
        "title": "Doctor Appointment",
        "q_start": "What time is your doctor appointment?",
        "q_end":   "What time does your appointment end?",
    },
    "doctor": {
        "title": "Doctor Appointment",
        "q_start": "What time is your doctor appointment?",
        "q_end":   "What time does your appointment end?",
    },
    "travel": {
        "title": "Travel",
        "q_start": "What time do you start travelling?",
        "q_end":   "What time do you arrive?",
    },
    "interview": {
        "title": "Interview",
        "q_start": "What time is your interview?",
        "q_end":   "What time does the interview end?",
    },
}

# Phrases that reference an event ONLY as a relation anchor (not a new task)
RELATION_ONLY_PHRASES = [
    r"\bbefore college\b",
    r"\bafter college\b",
    r"\bbefore class\b",
    r"\bafter class\b",
    r"\bbefore meeting\b",
    r"\bafter meeting\b",
    r"\bbefore the interview\b",
    r"\bafter the interview\b",
    r"\bbefore my interview\b",
    r"\bafter my interview\b",
    r"\bbefore college class\b",
    r"\bafter college class\b",
    r"\bexercise before\b",
    r"\bbreakfast before\b",
    r"\bprepare after\b",
]


def _is_relation_only(text):
    """Returns True if 'text' is just a relational phrase that anchors to
    a fixed event, NOT a declaration of that event itself."""
    tl = text.lower().strip()
    for pat in RELATION_ONLY_PHRASES:
        if re.search(pat, tl):
            return True
    return False


class Parser:

    # =========================================================
    # 1. DETECT DATE
    # =========================================================

    def detect_date(self, text):
        text_lower = text.lower()
        today = date.today()

        if "day after tomorrow" in text_lower:
            return str(today + timedelta(days=2))

        if "tomorrow" in text_lower:
            return str(today + timedelta(days=1))

        if "today" in text_lower:
            return str(today)

        date_match = re.search(
            r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b",
            text
        )

        if date_match:
            day = int(date_match.group(1))
            month = int(date_match.group(2))
            year = int(date_match.group(3))
            try:
                detected_date = date(year, month, day)
                return str(detected_date)
            except ValueError:
                return None

        month_pattern = (
            r"\b("
            r"january|february|march|april|may|june|"
            r"july|august|september|october|november|december"
            r")"
            r"\s+"
            r"(\d{1,2})"
            r"(?:,\s*|\s+)"
            r"(\d{4})?"
            r"\b"
        )

        month_match = re.search(month_pattern, text_lower)

        if month_match:
            month_name = month_match.group(1)
            day = int(month_match.group(2))
            year_text = month_match.group(3)

            month_number = datetime.strptime(month_name, "%B").month

            if year_text:
                year = int(year_text)
            else:
                year = today.year
                try:
                    possible_date = date(year, month_number, day)
                    if possible_date < today:
                        year += 1
                except ValueError:
                    return None

            try:
                detected_date = date(year, month_number, day)
                return str(detected_date)
            except ValueError:
                return None

        return None

    # =========================================================
    # 2. DETECT SINGLE TIME
    # =========================================================

    def detect_time(self, text):
        text_lower = text.lower()
        if re.search(r"\b(?:by|before|until|due\s+by)\s+(?:\d{1,2}(?::\d{2})?\s*(?:am|pm)?|\d{1,2}:\d{2})\b", text_lower):
            return None

        pattern_12 = (
            r"\b"
            r"(\d{1,2})"
            r"(?::(\d{2}))?"
            r"\s*"
            r"(AM|PM|am|pm)"
            r"\b"
        )

        match = re.search(pattern_12, text)

        if match:
            hour = int(match.group(1))
            minute = int(match.group(2) or 0)
            period = match.group(3).lower()

            if hour < 1 or hour > 12:
                return None

            if period == "pm" and hour != 12:
                hour += 12
            elif period == "am" and hour == 12:
                hour = 0

            return f"{hour:02d}:{minute:02d}"

        pattern_24 = (
            r"\b"
            r"([01]?\d|2[0-3])"
            r":"
            r"([0-5]\d)"
            r"\b"
        )

        match = re.search(pattern_24, text)

        if match:
            hour = int(match.group(1))
            minute = int(match.group(2))
            return f"{hour:02d}:{minute:02d}"

        return None

    # =========================================================
    # 2b. PARSE TIME FROM CLARIFICATION ANSWER
    # =========================================================

    def parse_time_answer(self, text):
        """Flexible time parser for user clarification answers.
        Accepts: '9 AM', '9:00 AM', '09:00', '4 PM', '4:00 PM', '16:00'
        Returns HH:MM or None.
        """
        t = text.strip()
        # Try patterns from detect_time (strips "by/before/until" guard)
        p12 = r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b"
        m = re.search(p12, t, flags=re.IGNORECASE)
        if m:
            h = int(m.group(1))
            mn = int(m.group(2) or 0)
            period = m.group(3).lower()
            if 1 <= h <= 12:
                if period == "pm" and h != 12:
                    h += 12
                elif period == "am" and h == 12:
                    h = 0
                return f"{h:02d}:{mn:02d}"
        p24 = r"\b([01]?\d|2[0-3]):([0-5]\d)\b"
        m = re.search(p24, t)
        if m:
            return f"{int(m.group(1)):02d}:{int(m.group(2)):02d}"
        # plain hour digits only: "9", "16"
        pm_match = re.match(r"^\s*(\d{1,2})\s*$", t)
        if pm_match:
            h = int(pm_match.group(1))
            if 0 <= h <= 23:
                return f"{h:02d}:00"
        return None

    # =========================================================
    # 3. DETECT TIME RANGE
    # =========================================================

    def detect_time_range(self, text):
        pattern_12 = (
            r"(?:from|between)?\s*\b"
            r"(\d{1,2})"
            r"(?::(\d{2}))?"
            r"\s*(AM|PM|am|pm)?"
            r"\s*(?:to|until|and|-|till)\s*"
            r"(\d{1,2})"
            r"(?::(\d{2}))?"
            r"\s*(AM|PM|am|pm)"
            r"\b"
        )

        match = re.search(pattern_12, text, flags=re.IGNORECASE)

        if match:
            start_hour = int(match.group(1))
            start_minute = int(match.group(2) or 0)
            start_period = (match.group(3) or "").lower()

            end_hour = int(match.group(4))
            end_minute = int(match.group(5) or 0)
            end_period = (match.group(6) or "").lower()

            if 1 <= start_hour <= 12 and 1 <= end_hour <= 12:
                if not start_period:
                    if end_period == "pm":
                        if start_hour < end_hour:
                            start_period = "pm"
                        else:
                            start_period = "am"
                    else:
                        start_period = "am"

                if start_period == "pm" and start_hour != 12:
                    start_hour += 12
                elif start_period == "am" and start_hour == 12:
                    start_hour = 0

                if end_period == "pm" and end_hour != 12:
                    end_hour += 12
                elif end_period == "am" and end_hour == 12:
                    end_hour = 0

                return {
                    "start": f"{start_hour:02d}:{start_minute:02d}",
                    "end": f"{end_hour:02d}:{end_minute:02d}"
                }

        pattern_24 = (
            r"(?:from|between)?\s*\b"
            r"([01]?\d|2[0-3])"
            r":"
            r"([0-5]\d)"
            r"\s*(?:to|until|and|-|till)\s*"
            r"([01]?\d|2[0-3])"
            r":"
            r"([0-5]\d)"
            r"\b"
        )

        match = re.search(pattern_24, text, flags=re.IGNORECASE)

        if match:
            start_hour = int(match.group(1))
            start_minute = int(match.group(2))
            end_hour = int(match.group(3))
            end_minute = int(match.group(4))

            return {
                "start": f"{start_hour:02d}:{start_minute:02d}",
                "end": f"{end_hour:02d}:{end_minute:02d}"
            }

        return None

    # =========================================================
    # 4. DETECT EXPLICIT DURATION
    # =========================================================

    def detect_duration(self, text):
        text_lower = text.lower()
        hours_match = re.search(r"(\d+(?:\.\d+)?)\s*hours?", text_lower)
        minutes_match = re.search(r"(\d+)\s*minutes?", text_lower)

        if hours_match or minutes_match:
            total_minutes = 0
            if hours_match:
                hours = float(hours_match.group(1))
                total_minutes += int(hours * 60)
            if minutes_match:
                total_minutes += int(minutes_match.group(1))
            return total_minutes

        return None

    # =========================================================
    # 5. ESTIMATE DURATION
    # =========================================================

    def estimate_duration(self, text):
        text_lower = text.lower()

        interview_keywords = [
            "interview preparation", "prepare for interview",
            "prepare for my interview", "prepare interview",
            "prepare my interview", "interview prep"
        ]
        for keyword in interview_keywords:
            if keyword in text_lower:
                return 120

        study_keywords = [
            "study", "learn", "exam preparation", "exam prep",
            "revision", "revise", "python", "sql", "course"
        ]
        for keyword in study_keywords:
            if keyword in text_lower:
                return 120

        work_keywords = [
            "work", "project", "report", "presentation", "meeting", "office"
        ]
        for keyword in work_keywords:
            if keyword in text_lower:
                return 120

        shopping_keywords = [
            "shopping", "supermarket", "groceries", "grocery", "buy", "purchase"
        ]
        for keyword in shopping_keywords:
            if keyword in text_lower:
                return 90

        health_keywords = ["exercise", "gym", "workout", "walk"]
        for keyword in health_keywords:
            if keyword in text_lower:
                return 60

        personal_keywords = ["temple", "pray", "prayer"]
        for keyword in personal_keywords:
            if keyword in text_lower:
                return 60

        social_keywords = ["meet friends", "meet friend", "friends", "friend", "party", "family"]
        for keyword in social_keywords:
            if keyword in text_lower:
                return 120

        rest_keywords = ["rest", "relax", "relaxation", "break"]
        for keyword in rest_keywords:
            if keyword in text_lower:
                return 60

        return 60

    # =========================================================
    # 6. DETECT PRIORITY
    # =========================================================

    def detect_priority(self, text):
        text_lower = text.lower()
        very_high_keywords = ["urgent", "very important", "must", "critical", "as soon as possible"]
        for keyword in very_high_keywords:
            if keyword in text_lower:
                return "very_high"

        high_keywords = ["important", "high priority", "should"]
        for keyword in high_keywords:
            if keyword in text_lower:
                return "high"

        low_keywords = ["low priority", "not important"]
        for keyword in low_keywords:
            if keyword in text_lower:
                return "low"

        return "normal"

    # =========================================================
    # 7. DETECT CONTEXT
    # =========================================================

    def detect_context(self, text):
        text_lower = text.lower()
        study_keywords = ["study", "learn", "exam", "interview", "python", "sql", "course", "revision"]
        for keyword in study_keywords:
            if keyword in text_lower:
                return "study"

        work_keywords = ["work", "meeting", "project", "office", "report", "presentation"]
        for keyword in work_keywords:
            if keyword in text_lower:
                return "work"

        shopping_keywords = ["shopping", "supermarket", "buy", "purchase", "groceries", "grocery"]
        for keyword in shopping_keywords:
            if keyword in text_lower:
                return "shopping"

        health_keywords = ["exercise", "gym", "doctor", "hospital", "medicine", "walk", "workout"]
        for keyword in health_keywords:
            if keyword in text_lower:
                return "health"

        social_keywords = ["friend", "friends", "family", "party", "meet"]
        for keyword in social_keywords:
            if keyword in text_lower:
                return "social"

        personal_keywords = ["temple", "pray", "relax", "rest", "personal"]
        for keyword in personal_keywords:
            if keyword in text_lower:
                return "personal"

        return "general"

    # =========================================================
    # 8. DETECT FREQUENCY
    # =========================================================

    def detect_frequency(self, text):
        text_lower = text.lower()
        if "every day" in text_lower or "daily" in text_lower:
            return "daily"
        if "every morning" in text_lower:
            return "every morning"
        if "every evening" in text_lower:
            return "every evening"
        if "every night" in text_lower:
            return "every night"
        if "every weekday" in text_lower:
            return "every weekday"
        return None

    # =========================================================
    # 9. DETECT DEADLINE TIME
    # =========================================================

    def detect_deadline_time(self, text):
        text_lower = text.lower()
        if "by evening" in text_lower or "before evening" in text_lower or "until evening" in text_lower:
            return "18:00"
        if "by morning" in text_lower or "before morning" in text_lower:
            return "12:00"
        if "by afternoon" in text_lower or "before afternoon" in text_lower:
            return "16:00"
        if "by night" in text_lower or "before night" in text_lower:
            return "21:00"

        pattern_12 = (
            r"\b(?:by|before|until)\s+"
            r"(\d{1,2})"
            r"(?::(\d{2}))?"
            r"\s*"
            r"(am|pm)"
            r"\b"
        )
        match = re.search(pattern_12, text_lower)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2) or 0)
            period = match.group(3)
            if hour < 1 or hour > 12:
                return None
            if period == "pm" and hour != 12:
                hour += 12
            elif period == "am" and hour == 12:
                hour = 0
            return f"{hour:02d}:{minute:02d}"

        pattern_24 = (
            r"\b(?:by|before|until)\s+"
            r"([01]?\d|2[0-3])"
            r":"
            r"([0-5]\d)"
            r"\b"
        )
        match = re.search(pattern_24, text_lower)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2))
            return f"{hour:02d}:{minute:02d}"

        return None

    # =========================================================
    # 9B. DETECT CONTEXT WINDOW & RELATIONSHIPS
    # =========================================================

    def detect_context_window(self, text):
        text_lower = text.lower()
        if "later in the day" in text_lower or "later day" in text_lower or "later" in text_lower:
            return "later_day"
        if "evening" in text_lower or "night" in text_lower:
            return "evening"
        if "morning" in text_lower:
            return "morning"
        if "afternoon" in text_lower:
            return "afternoon"
        return None

    def detect_relationships(self, text):
        text_lower = text.lower()
        before_task = None
        after_task = None

        if "before class" in text_lower or "before college" in text_lower or "before college class" in text_lower:
            before_task = "College Class" if "college class" in text_lower else "College"
        elif "before meeting" in text_lower or "before the meeting" in text_lower or "before my meeting" in text_lower:
            before_task = "Meeting"
        elif "before interview" in text_lower or "before my interview" in text_lower or "before the interview" in text_lower:
            before_task = "Interview Preparation"
        elif "before work" in text_lower:
            before_task = "Work"
        elif "before that" in text_lower or "before it" in text_lower or "prior to that" in text_lower:
            before_task = "PREVIOUS_TASK"
        else:
            m_before = re.search(r"\b(?:before|prior to|earlier than)\s+(?:the|my|a|an)?\s*([a-z0-9\s]+)", text_lower)
            if m_before:
                tgt = m_before.group(1).strip()
                if "class" in tgt or "college" in tgt:
                    before_task = "College Class" if "college" in tgt and "class" in tgt else "College"
                elif "interview" in tgt:
                    before_task = "Interview Preparation"
                elif "meeting" in tgt:
                    before_task = "Meeting"
                elif "work" in tgt:
                    before_task = "Work"
                elif tgt in ("that", "it"):
                    before_task = "PREVIOUS_TASK"

        if "after lunch" in text_lower:
            after_task = "Lunch"
        elif "after work" in text_lower:
            after_task = "Work"
        elif "after class" in text_lower or "after college" in text_lower or "after college class" in text_lower:
            after_task = "College Class" if "college class" in text_lower else "College"
        elif "after meeting" in text_lower or "after the meeting" in text_lower or "after my meeting" in text_lower:
            after_task = "Meeting"
        elif "after interview" in text_lower or "after my interview" in text_lower or "after the interview" in text_lower:
            after_task = "Interview Preparation"
        elif "after that" in text_lower or "after it" in text_lower or "following that" in text_lower:
            after_task = "PREVIOUS_TASK"
        elif re.search(r"^\s*then\b", text_lower) or re.search(r",\s*then\b", text_lower):
            after_task = "PREVIOUS_TASK"
        else:
            m_after = re.search(r"\b(?:after|following|later than)\s+(?:the|my|a|an)?\s*([a-z0-9\s]+)", text_lower)
            if m_after:
                tgt = m_after.group(1).strip()
                if "lunch" in tgt:
                    after_task = "Lunch"
                elif "work" in tgt:
                    after_task = "Work"
                elif "class" in tgt or "college" in tgt:
                    after_task = "College Class" if "college" in tgt and "class" in tgt else "College"
                elif "meeting" in tgt:
                    after_task = "Meeting"
                elif "interview" in tgt:
                    after_task = "Interview Preparation"
                elif tgt in ("that", "it"):
                    after_task = "PREVIOUS_TASK"

        return before_task, after_task

    # =========================================================
    # 10. EXTRACT TITLE
    # =========================================================

    def extract_title(self, text):
        title = text.strip()
        lower_raw = title.lower()

        if "breaks between activities" in lower_raw or "want some breaks" in lower_raw or lower_raw in ("some breaks", "breaks"):
            return None

        # Suppress "rest" / "enough time to rest" as a separate task title
        if re.match(r"^(i\s+also\s+want\s+)?(enough\s+time\s+to\s+)?rest(\s+time)?$", lower_raw):
            return None

        title = re.sub(r"\bday after tomorrow\b", "", title, flags=re.IGNORECASE)
        title = re.sub(r"\btomorrow\b", "", title, flags=re.IGNORECASE)
        title = re.sub(r"\btoday\b", "", title, flags=re.IGNORECASE)
        title = re.sub(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b", "", title)

        month_pattern = (
            r"\b(?:january|february|march|april|may|june|july|august|"
            r"september|october|november|december)\s+\d{1,2}(?:,\s*\d{4})?\b"
        )
        title = re.sub(month_pattern, "", title, flags=re.IGNORECASE)

        title = re.sub(r"(?:from|between)?\s*\b\d{1,2}(?::\d{2})?\s*(?:am|pm)?\s*(?:to|until|and|-|till)\s*\d{1,2}(?::\d{2})?\s*(?:am|pm)?\b", "", title, flags=re.IGNORECASE)
        title = re.sub(r"\bat\s+\d{1,2}(?::\d{2})?\s*(?:am|pm)?\b", "", title, flags=re.IGNORECASE)
        title = re.sub(r"\b(?:by|before|until)\s+\d{1,2}(?::\d{2})?\s*(?:am|pm)?\b", "", title, flags=re.IGNORECASE)
        title = re.sub(r"\b\d{1,2}:\d{2}\b", "", title)

        rel_patterns = [
            r"\bbefore that\b", r"\bafter that\b", r"\bbefore class\b", r"\bbefore college class\b", r"\bbefore college\b",
            r"\bafter lunch\b", r"\bafter work\b", r"\bbefore work\b", r"\bafter college class\b", r"\bafter college\b",
            r"\bbefore my interview\b", r"\bbefore the interview\b", r"\bafter the interview\b",
            r"\bbefore meeting\b", r"\bbefore the meeting\b", r"\bafter meeting\b", r"\bafter the meeting\b",
            r"\bby evening\b", r"\blater in the day\b", r"\bin the evening\b", r"\bin the morning\b", r"\bin the afternoon\b",
            r"\blater\b"
        ]
        for pattern in rel_patterns:
            title = re.sub(pattern, "", title, flags=re.IGNORECASE)

        title = re.sub(r"\b\d+(?:\.\d+)?\s*hours?\b", "", title, flags=re.IGNORECASE)
        title = re.sub(r"\b\d+\s*minutes?\b", "", title, flags=re.IGNORECASE)

        frequency_patterns = [
            r"\bevery day\b", r"\bdaily\b", r"\bevery morning\b",
            r"\bevery evening\b", r"\bevery night\b", r"\bevery weekday\b"
        ]
        for pattern in frequency_patterns:
            title = re.sub(pattern, "", title, flags=re.IGNORECASE)

        title = re.sub(r"\s+", " ", title).strip(" ,.-;:?")
        lower = title.lower()

        if not lower or lower in ("before", "after", "that", "it", "then", "later"):
            return None

        if "call" in lower and "friend" in lower:
            return "Call My Friend"

        if "college" in lower and "class" in lower:
            return "College Class"

        if "college" in lower:
            return "College"

        if "interview" in lower and (
            "prepare" in lower or "prep" in lower or "have an interview" in lower
            or "need to" in lower or "revision" in lower or "revise" in lower
        ):
            return "Interview Preparation"

        if "assignment" in lower and ("complete" in lower or "finish" in lower or "do" in lower or "submit" in lower):
            return "Complete My Assignment"

        if "friend" in lower or "friends" in lower:
            return "Spend Some Time With My Friends"

        if "supermarket" in lower and "groceries" in lower:
            return "Buy Groceries"

        if "temple" in lower:
            return "Go to Temple"

        if "python" in lower and ("study" in lower or "learn" in lower or "code" in lower or "revise" in lower):
            return "Study Python"

        if lower in ("have breakfast", "breakfast", "eat breakfast"):
            return "Breakfast"

        if lower in ("have lunch", "lunch", "eat lunch"):
            return "Lunch"

        if lower in ("exercise", "workout", "do exercise"):
            return "Exercise"

        if "gym" in lower:
            return "Gym"

        if "study" in lower:
            return "Study"

        filler_prefixes = [
            r"^i\s+have\s+an?\s+interview\s*(?:and|\.|,)?\s*(?:need\s+to\s+prepare\s+for\s+it)?",
            r"^i\s+want\s+to\s+go\s+to\s+the\s+",
            r"^i\s+want\s+to\s+go\s+to\s+",
            r"^i\s+want\s+to\s+",
            r"^i\s+need\s+to\s+prepare\s+for\s+",
            r"^i\s+need\s+to\s+",
            r"^i\s+also\s+need\s+to\s+",
            r"^i\s+have\s+to\s+",
            r"^i\s+have\s+an?\s+",
            r"^i\s+have\s+a\s+",
            r"^i\s+should\s+",
            r"^remember\s+to\s+",
            r"^don't\s+forget\s+to\s+",
            r"^please\s+"
        ]
        for prefix in filler_prefixes:
            title = re.sub(prefix, "", title, flags=re.IGNORECASE)

        title = re.sub(r"\s+\b(?:for|to|before|after)\b$", "", title, flags=re.IGNORECASE)
        title = re.sub(r"\s+", " ", title).strip(" ,.-;:?")

        if not title or title.lower() in ("before", "after", "that", "it", "then"):
            return None

        words = title.split()
        if words:
            lowercase_words = {"to", "for", "and", "a", "an", "the", "in", "on", "at", "of", "with", "by", "my"}
            c_words = []
            for idx, w in enumerate(words):
                if idx == 0 or w.lower() not in lowercase_words:
                    c_words.append(w.capitalize())
                else:
                    c_words.append(w.lower())
            title = " ".join(c_words)

        return title

    # =========================================================
    # 11. DETECT FIXED EVENT THAT NEEDS CLARIFICATION
    # =========================================================

    def detect_fixed_event(self, text):
        """
        Checks whether 'text' describes a fixed event that needs time
        clarification (college, class, meeting, appointment, etc.).

        Returns a dict like:
          {
              "title": "College",
              "requires_time": True,  # False if time range already given
              "start_time": "09:00" or None,
              "end_time":   "16:00" or None,
              "q_start": "What time do you go to college?",
              "q_end":   "What time do you return from college?",
          }
        or None if no fixed event is detected.

        Rules:
        - The text must declare the event (not merely reference it as a
          relational anchor such as "before college" or "after class").
        - If both start and end time are supplied → requires_time = False.
        - If only start is supplied → requires_time = True (ask for end).
        - If neither is supplied → requires_time = True (ask for start first).
        """
        tl = text.lower().strip()

        # Phrases that only reference the event as a relation anchor
        if _is_relation_only(tl):
            return None

        # Check whether the text really DECLARES a fixed event
        declared_key = None
        declared_meta = None

        # Order matters: check longer phrases first
        for keyword in sorted(FIXED_EVENT_KEYWORDS.keys(), key=len, reverse=True):
            if keyword in tl:
                # Make sure it's a declaration, not just a relational mention.
                # Declarations contain patterns like:
                #   "I have college", "going to college", "attend college",
                #   "I have a class", "I have college tomorrow", etc.
                # We match declaration patterns; if none match, skip.
                decl_patterns = [
                    rf"\bI\s+have\s+(?:a\s+|an\s+)?(?:the\s+)?{re.escape(keyword)}\b",
                    rf"\bI\s+(?:am\s+)?going\s+to\s+{re.escape(keyword)}\b",
                    rf"\bI\s+(?:have\s+to|need\s+to|want\s+to)\s+go\s+to\s+{re.escape(keyword)}\b",
                    rf"\battend\s+{re.escape(keyword)}\b",
                    rf"\bgo\s+to\s+{re.escape(keyword)}\b",
                    rf"\bgo\s+{re.escape(keyword)}\b",
                    # Simple bare declaration: "College tomorrow", "College from 9 AM"
                    rf"^\s*{re.escape(keyword)}(\s|,|$)",
                ]
                for dpat in decl_patterns:
                    if re.search(dpat, text, flags=re.IGNORECASE):
                        declared_key = keyword
                        declared_meta = FIXED_EVENT_KEYWORDS[keyword]
                        break
                if declared_key:
                    break

        if not declared_key:
            return None

        # Now check whether time information is already supplied
        time_range = self.detect_time_range(text)
        single_time = self.detect_time(text)

        start_time = None
        end_time = None

        if time_range:
            start_time = time_range["start"]
            end_time = time_range["end"]
        elif single_time:
            start_time = single_time
            end_time = None  # still need end time

        has_start = start_time is not None
        has_end = end_time is not None
        requires_time = not (has_start and has_end)

        return {
            "title": declared_meta["title"],
            "requires_time": requires_time,
            "start_time": start_time,
            "end_time": end_time,
            "q_start": declared_meta["q_start"],
            "q_end":   declared_meta["q_end"],
        }

    # =========================================================
    # 12. BUILD CLARIFICATION REQUEST
    # =========================================================

    def build_clarification(self, fixed_event_info):
        """
        Given the output of detect_fixed_event(), returns the next
        clarification question dict that the planner should send to the GUI.

        Returns:
          {
              "needs_clarification": True,
              "question": "What time do you go to college?",
              "field": "start_time",        # or "end_time"
              "task_title": "College",
          }
        or None if no clarification is needed.
        """
        if not fixed_event_info or not fixed_event_info.get("requires_time"):
            return None

        has_start = fixed_event_info.get("start_time") is not None
        task_title = fixed_event_info["title"]

        if not has_start:
            return {
                "needs_clarification": True,
                "question": fixed_event_info["q_start"],
                "field": "start_time",
                "task_title": task_title,
            }
        else:
            return {
                "needs_clarification": True,
                "question": fixed_event_info["q_end"],
                "field": "end_time",
                "task_title": task_title,
            }

    # =========================================================
    # 13. MAIN PARSE METHOD
    # =========================================================

    def parse(self, text):
        result = {
            "original_text": text,
            "type": None,
            "title": None,
            "duration": None,
            "date": None,
            "time": None,
            "start_time": None,
            "end_time": None,
            "priority": None,
            "context": None,
            "context_window": None,
            "before_task": None,
            "after_task": None,
            "frequency": None,
            "time_range": None,
            "deadline_time": None,
            "time_type": "estimated",
            "requires_time": False,
        }

        result["date"] = self.detect_date(text)
        result["time_range"] = self.detect_time_range(text)

        if result["time_range"] is not None:
            result["time"] = result["time_range"]["start"]
            result["start_time"] = result["time_range"]["start"]
            result["end_time"] = result["time_range"]["end"]
            result["time_type"] = "fixed"

            sh, sm = map(int, result["start_time"].split(":"))
            eh, em = map(int, result["end_time"].split(":"))
            calc_dur = (eh * 60 + em) - (sh * 60 + sm)
            if calc_dur > 0:
                result["duration"] = calc_dur
        else:
            result["time"] = self.detect_time(text)
            if result["time"] is not None:
                result["start_time"] = result["time"]
                result["end_time"] = None
                result["time_type"] = "fixed"
            else:
                result["start_time"] = None
                result["end_time"] = None
                result["time_type"] = "estimated"

        # Explicit duration always wins
        explicit_dur = self.detect_duration(text)
        if explicit_dur is not None:
            result["duration"] = explicit_dur
        elif result["duration"] is None:
            result["duration"] = self.estimate_duration(text)

        result["priority"] = self.detect_priority(text)
        result["context"] = self.detect_context(text)
        result["frequency"] = self.detect_frequency(text)
        result["deadline_time"] = self.detect_deadline_time(text)
        result["context_window"] = self.detect_context_window(text)

        b_task, a_task = self.detect_relationships(text)
        result["before_task"] = b_task
        result["after_task"] = a_task

        result["title"] = self.extract_title(text)

        if result["frequency"]:
            result["type"] = "routine"
        elif result["time_type"] == "fixed":
            result["type"] = "event"
        else:
            result["type"] = "task"

        # Mark if this parsed task still needs time clarification
        fixed_info = self.detect_fixed_event(text)
        if fixed_info and fixed_info["requires_time"]:
            result["requires_time"] = True
            result["type"] = "event"

        return result