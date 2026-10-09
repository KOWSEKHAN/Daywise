"""
ui/gui.py

DayWise Tkinter Desktop GUI – Rich Lifecycle Dashboard Theme
Zero third-party dependencies – pure Python + Tkinter standard library.

Full Personal Planning Lifecycle:
  Routines (Periods + Mon-Sun Overrides + Common Library)
    ↓
  Plan My Day (Date Selection + Applicable Routines + One-Time Tasks + NLP)
    ↓
  Generate Plan & Review/Inline Edit
    ↓
  Confirm Plan (Today → Active Plan | Future → Future Confirmed Plan)
    ↓
  Today's Plan (Live Execution, Inline Status Tracking, Inline Notes, Inline Editing)
    ↓
  Day Closure / Rollover (Automatic or Manual Finalization)
    ↓
  History (Immutable by Default, Audited Historical Edits with Mandatory Note)
"""

import re
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, datetime, timedelta

from core.planner import Planner
from core.scheduler import time_to_minutes, minutes_to_time
from utils.date_utils import (
    format_date_display,
    today_str,
    tomorrow_str,
    parse_date_str,
    get_weekday_name,
    is_today,
    is_future_date,
    is_past_date,
    validate_date_range,
)
from utils.text_utils import truncate
from models.routine import DAYS_OF_WEEK, RoutineTaskTemplate, DayRoutineItem, RoutinePeriod
from models.plan import PlanStatus


# ============================================================
# LIGHT DASHBOARD COLOR PALETTE & TYPOGRAPHY
# ============================================================

BG_MAIN        = "#f8fafc"   # Slate-50 – main background
BG_PANEL       = "#f1f5f9"   # Slate-100 – panel background
BG_CARD        = "#ffffff"   # Pure white – card background
BG_SIDEBAR     = "#0f172a"   # Deep slate / dark navy – left sidebar

BORDER_COLOR   = "#e2e8f0"   # Light border slate-200
BORDER_DARK    = "#cbd5e1"   # Medium border slate-300

FG_MAIN        = "#0f172a"   # Dark navy primary text
FG_MUTED       = "#64748b"   # Muted blue-gray secondary text
FG_SIDEBAR     = "#94a3b8"   # Light gray text for sidebar

PRIMARY_BLUE   = "#2563eb"   # Vivid blue accent
PRIMARY_HOVER  = "#1d4ed8"   # Darker blue hover
PRIMARY_LIGHT  = "#eff6ff"   # Soft blue background tint

BTN_BG         = "#2563eb"   # Primary button bg
BTN_FG         = "#ffffff"
BTN_HOVER      = "#1d4ed8"

BTN_SUCCESS_BG = "#16a34a"   # Green confirm bg
BTN_SUCCESS_HOVER = "#15803d"

BTN_SEC_BG     = "#e2e8f0"   # Secondary button bg
BTN_SEC_FG     = "#0f172a"
BTN_SEC_HOVER  = "#cbd5e1"

BTN_DANGER_BG  = "#fee2e2"   # Soft red delete bg
BTN_DANGER_FG  = "#dc2626"   # Soft red text
BTN_DANGER_HOVER = "#fca5a5"

ENTRY_BG       = "#ffffff"
ENTRY_FG       = "#0f172a"
ENTRY_BORDER   = "#cbd5e1"

FONT_TITLE     = ("Segoe UI", 18, "bold")
FONT_HEADING   = ("Segoe UI", 13, "bold")
FONT_SUBHEAD   = ("Segoe UI", 11, "bold")
FONT_BODY      = ("Segoe UI", 10)
FONT_SMALL     = ("Segoe UI", 9)
FONT_MONO      = ("Consolas", 10, "bold")

# Soft Pastel Badge Styling: (Background, Text Color)
BADGE_STYLES = {
    # Sources / Types
    "routine":        ("#e0f2fe", "#0369a1"),  # soft cyan
    "one-time":       ("#fae8ff", "#86198f"),  # soft purple
    "override":       ("#fef3c7", "#92400e"),  # soft amber
    "fixed":          ("#dbeafe", "#1e40af"),  # soft blue
    "break":          ("#f1f5f9", "#475569"),  # soft gray
    "task":           ("#e0e7ff", "#3730a3"),  # soft indigo

    # Priorities
    "very high":      ("#fee2e2", "#991b1b"),  # soft red
    "high":           ("#ffedd5", "#9a3412"),  # soft orange
    "normal":         ("#fef9c3", "#854d0e"),  # soft yellow
    "low":            ("#dcfce7", "#166534"),  # soft green

    # Statuses
    "pending":        ("#ffedd5", "#9a3412"),  # soft orange
    "not_completed":  ("#fee2e2", "#991b1b"),  # soft red
    "not completed":  ("#fee2e2", "#991b1b"),  # soft red
    "scheduled":      ("#dbeafe", "#1e40af"),  # soft blue
    "completed":      ("#dcfce7", "#166534"),  # soft green
    "active":         ("#dcfce7", "#166534"),  # soft green
    "future_confirmed": ("#e0f2fe", "#0369a1"), # soft cyan
    "finalized":      ("#f1f5f9", "#475569"),  # soft gray
    "edited":         ("#fef3c7", "#92400e"),  # soft amber
}

TIMELINE_DOTS = ["🟢", "🔵", "🟣", "🟠", "🔴", "🟤", "⚪"]


# ============================================================
# CONTEXTUAL ICONS & DESCRIPTIONS
# ============================================================

def get_icon_for_title(title, context="", etype=""):
    """Returns a contextual unicode icon based on title, context, or type."""
    text = (str(title) + " " + str(context)).lower()

    if "gym" in text or "workout" in text or "fitness" in text:
        return "🏋"
    if "exercise" in text or "run" in text or "walk" in text or "jog" in text or "yoga" in text:
        return "🏃"
    if "breakfast" in text or "coffee" in text or "tea" in text:
        return "☕"
    if "lunch" in text or "dinner" in text or "food" in text or "eat" in text or "meal" in text:
        return "🍴"
    if "python" in text or "study" in text or "code" in text or "learn" in text or "read" in text or "book" in text:
        return "📚"
    if "shopping" in text or "groceries" in text or "supermarket" in text or "buy" in text:
        return "🛒"
    if "college" in text or "class" in text or "university" in text or "exam" in text or "lecture" in text:
        return "🎓"
    if "interview" in text or "work" in text or "office" in text or "job" in text or "meeting" in text:
        return "💼"
    if "friend" in text or "social" in text or "hangout" in text or "party" in text:
        return "👥"
    if "call" in text or "phone" in text or "talk" in text:
        return "📞"
    if "movie" in text or "watch" in text or "show" in text or "cinema" in text:
        return "🎬"
    if "sleep" in text or "bed" in text or "nap" in text or "wind down" in text:
        return "🛏"
    if "rest" in text or "relax" in text or "meditat" in text:
        return "🧘"
    if "assignment" in text or "report" in text or "write" in text or "notes" in text:
        return "📝"
    if "temple" in text or "church" in text or "pray" in text or "worship" in text:
        return "⛪"
    if "doctor" in text or "hospital" in text or "health" in text or "medicine" in text:
        return "🏥"
    if etype == "routine":
        return "🔄"
    if etype == "break":
        return "☕"
    return "📝"


def get_description_for_title(title, etype=""):
    """Returns a clean secondary description for visual task cards."""
    text = str(title).lower()
    if "gym" in text or "exercise" in text or "workout" in text:
        return "Stay healthy and active"
    if "breakfast" in text:
        return "Start your day with energy"
    if "lunch" in text or "dinner" in text:
        return "Nutritious meal break"
    if "python" in text or "study" in text or "code" in text:
        return "Skill building & focus time"
    if "groceries" in text or "shopping" in text:
        return "Pick up daily essentials"
    if "interview" in text or "prepare" in text:
        return "Career milestone preparation"
    if "temple" in text or "pray" in text:
        return "Peaceful spiritual time"
    if "wind down" in text or "sleep" in text:
        return "Rest and recharge"
    if etype == "routine":
        return "Daily recurring habit"
    if etype == "break":
        return "Short refresh break"
    return "Scheduled daily activity"


def format_12h(time_str):
    """Formats HH:MM string to HH:MM AM/PM string if valid."""
    try:
        dt = datetime.strptime(str(time_str).strip(), "%H:%M")
        return dt.strftime("%I:%M %p").lstrip("0")
    except Exception:
        return str(time_str)


# ============================================================
# HELPER – PURE-TKINTER CALENDAR DATE PICKER
# ============================================================

class CalendarPicker(tk.Toplevel):
    """
    A lightweight, pure-Tkinter calendar popup.
    No third-party dependencies — uses only tkinter + datetime.

    Usage:
        CalendarPicker(parent, date_var, callback=None)
        - date_var  : tk.StringVar that receives the selected YYYY-MM-DD date.
        - callback  : optional callable invoked after date selection.
    """

    _DAYS_SHORT = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]

    _HDR_BG     = PRIMARY_BLUE
    _HDR_FG     = "#ffffff"
    _CELL_BG    = BG_CARD
    _CELL_FG    = FG_MAIN
    _SEL_BG     = PRIMARY_BLUE
    _SEL_FG     = "#ffffff"
    _TODAY_BG   = "#eff6ff"
    _TODAY_FG   = PRIMARY_BLUE
    _OTHER_FG   = "#94a3b8"   # days from adjacent month

    def __init__(self, parent, date_var, callback=None):
        super().__init__(parent)
        self._date_var = date_var
        self._callback  = callback

        # Determine initial display month
        try:
            initial = datetime.strptime(date_var.get().strip(), "%Y-%m-%d").date()
        except Exception:
            initial = date.today()

        self._view_year  = initial.year
        self._view_month = initial.month
        self._selected   = initial

        self.title("Pick a Date")
        self.resizable(False, False)
        self.configure(bg=BG_CARD)
        self.transient(parent)
        self.grab_set()

        # Position near parent
        px, py = parent.winfo_rootx(), parent.winfo_rooty()
        self.geometry(f"270x240+{px + 60}+{py + 120}")

        self._build()
        self.wait_window(self)

    # ----------------------------------------------------------

    def _build(self):
        """Build / re-build the calendar grid."""
        for w in self.winfo_children():
            w.destroy()

        # ── Header (month navigation) ──────────────────────────
        hdr = tk.Frame(self, bg=self._HDR_BG, padx=4, pady=4)
        hdr.pack(fill="x")

        tk.Button(
            hdr, text="◀", font=("Segoe UI", 9, "bold"),
            bg=self._HDR_BG, fg=self._HDR_FG,
            relief="flat", bd=0, padx=6, cursor="hand2",
            activebackground=PRIMARY_HOVER, activeforeground="#fff",
            command=self._prev_month,
        ).pack(side="left")

        import calendar as cal_mod
        month_name = cal_mod.month_name[self._view_month]
        tk.Label(
            hdr, text=f"{month_name} {self._view_year}",
            font=("Segoe UI", 10, "bold"),
            bg=self._HDR_BG, fg=self._HDR_FG,
        ).pack(side="left", expand=True)

        tk.Button(
            hdr, text="▶", font=("Segoe UI", 9, "bold"),
            bg=self._HDR_BG, fg=self._HDR_FG,
            relief="flat", bd=0, padx=6, cursor="hand2",
            activebackground=PRIMARY_HOVER, activeforeground="#fff",
            command=self._next_month,
        ).pack(side="right")

        # ── Day-of-week header row ─────────────────────────────
        dow_row = tk.Frame(self, bg=BG_PANEL)
        dow_row.pack(fill="x")
        for d in self._DAYS_SHORT:
            tk.Label(
                dow_row, text=d, width=3,
                font=("Segoe UI", 8, "bold"),
                fg=FG_MUTED, bg=BG_PANEL, anchor="center",
            ).pack(side="left", padx=1, pady=2)

        # ── Calendar grid ──────────────────────────────────────
        import calendar as cal_mod
        today = date.today()
        cal = cal_mod.monthcalendar(self._view_year, self._view_month)

        grid_frame = tk.Frame(self, bg=BG_CARD)
        grid_frame.pack(fill="both", expand=True, padx=2, pady=2)

        for week in cal:
            row = tk.Frame(grid_frame, bg=BG_CARD)
            row.pack(fill="x", pady=0)
            for day_num in week:
                if day_num == 0:
                    tk.Label(row, text="", width=3, bg=BG_CARD).pack(side="left", padx=1, pady=1)
                    continue

                cell_date = date(self._view_year, self._view_month, day_num)
                is_today    = (cell_date == today)
                is_selected = (cell_date == self._selected)

                if is_selected:
                    bg, fg = self._SEL_BG, self._SEL_FG
                    font = ("Segoe UI", 9, "bold")
                elif is_today:
                    bg, fg = self._TODAY_BG, self._TODAY_FG
                    font = ("Segoe UI", 9, "bold")
                else:
                    bg, fg = self._CELL_BG, self._CELL_FG
                    font = ("Segoe UI", 9)

                btn = tk.Button(
                    row, text=str(day_num), width=3,
                    font=font, bg=bg, fg=fg,
                    relief="flat", bd=0, padx=1, pady=3,
                    cursor="hand2",
                    activebackground=self._SEL_BG,
                    activeforeground=self._SEL_FG,
                    command=lambda d=cell_date: self._select(d),
                )
                btn.pack(side="left", padx=1, pady=1)

        # ── Footer: Today shortcut ─────────────────────────────
        foot = tk.Frame(self, bg=BG_PANEL)
        foot.pack(fill="x", pady=(4, 0))
        tk.Button(
            foot, text="Today", font=("Segoe UI", 8),
            bg=BTN_SEC_BG, fg=FG_MUTED,
            relief="flat", cursor="hand2",
            padx=8, pady=2,
            command=lambda: self._select(date.today()),
        ).pack(side="right", padx=6, pady=2)

    def _select(self, selected_date):
        self._date_var.set(selected_date.strftime("%Y-%m-%d"))
        if self._callback:
            self._callback(selected_date.strftime("%Y-%m-%d"))
        self.destroy()

    def _prev_month(self):
        if self._view_month == 1:
            self._view_month, self._view_year = 12, self._view_year - 1
        else:
            self._view_month -= 1
        self._build()

    def _next_month(self):
        if self._view_month == 12:
            self._view_month, self._view_year = 1, self._view_year + 1
        else:
            self._view_month += 1
        self._build()


# ============================================================
# HELPER – HOVER BUTTON
# ============================================================

class HoverButton(tk.Button):
    """A Button that smoothly changes background on mouse hover."""

    def __init__(self, master, hover_bg=PRIMARY_HOVER, **kwargs):
        super().__init__(master, **kwargs)
        self._default_bg = kwargs.get("bg", BTN_BG)
        self._hover_bg   = hover_bg
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _on_enter(self, _event):
        try:
            self.config(bg=self._hover_bg)
        except Exception:
            pass

    def _on_leave(self, _event):
        try:
            self.config(bg=self._default_bg)
        except Exception:
            pass


# ============================================================
# HELPER – RESPONSIVE SCROLLABLE FRAME
# ============================================================

class ScrollableFrame(tk.Frame):
    """A Frame with a vertical scrollbar that dynamically resizes to canvas width."""

    def __init__(self, parent, bg=BG_MAIN, **kwargs):
        super().__init__(parent, bg=bg, **kwargs)

        canvas = tk.Canvas(self, bg=bg, highlightthickness=0)
        scrollbar = ttk.Scrollbar(
            self, orient="vertical", command=canvas.yview
        )
        self.inner = tk.Frame(canvas, bg=bg)

        self._window_id = canvas.create_window((0, 0), window=self.inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        def _on_inner_configure(_event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def _on_canvas_configure(event):
            canvas.itemconfig(self._window_id, width=event.width)

        self.inner.bind("<Configure>", _on_inner_configure)
        canvas.bind("<Configure>", _on_canvas_configure)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Mouse-wheel scrolling across platforms
        def _on_mousewheel(event):
            if hasattr(event, "delta") and event.delta:
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            elif hasattr(event, "num"):
                if event.num == 4:
                    canvas.yview_scroll(-1, "units")
                elif event.num == 5:
                    canvas.yview_scroll(1, "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)


# ============================================================
# BADGE RENDERING (SINGLE SOURCE OF TRUTH, ZERO DUPLICATES)
# ============================================================

def render_task_badges(parent, entry):
    """
    Renders standardized, non-duplicated semantic badges for a task or schedule entry.
    Ensures that redundant badge combinations like [ROUTINE] [ROUTINE] are never created.
    """
    etype = str(entry.get("type", "task")).lower()
    priority = str(entry.get("priority", "")).lower()
    status = str(entry.get("status", "pending")).lower()
    source = str(entry.get("source", "")).lower()
    is_edited = entry.get("is_edited", False)

    # 1. Audit Badge
    if is_edited:
        tk.Label(
            parent, text=" EDITED ",
            font=("Segoe UI", 8, "bold"), fg="#92400e",
            bg="#fef3c7", padx=6, pady=2,
        ).pack(side="right", padx=(4, 0))

    # 2. Status Badge (for meaningful, non-pending statuses)
    if status in BADGE_STYLES and status != "pending":
        s_bg, s_fg = BADGE_STYLES[status]
        tk.Label(
            parent, text=f" {status.replace('_', ' ').upper()} ",
            font=("Segoe UI", 8, "bold"), fg=s_fg,
            bg=s_bg, padx=6, pady=2,
        ).pack(side="right", padx=(4, 0))

    # 3. Priority Badge (only if high or very high)
    if priority in ("high", "very high") and priority in BADGE_STYLES:
        p_bg, p_fg = BADGE_STYLES[priority]
        tk.Label(
            parent, text=f" {priority.upper()} ",
            font=("Segoe UI", 8, "bold"), fg=p_fg,
            bg=p_bg, padx=6, pady=2,
        ).pack(side="right", padx=(4, 0))

    # 4. Source / Type Badge (Single Meaningful Badge)
    single_badge = None
    if source == "override" or entry.get("is_override"):
        single_badge = "override"
    elif source == "routine" or etype == "routine":
        single_badge = "routine"
    elif source == "one-time":
        single_badge = "one-time"
    elif etype == "break":
        single_badge = "break"
    elif etype == "event" or entry.get("time_type") == "fixed":
        single_badge = "fixed"
    elif etype == "task":
        single_badge = "task"

    if single_badge and single_badge in BADGE_STYLES:
        b_bg, b_fg = BADGE_STYLES[single_badge]
        tk.Label(
            parent, text=f" {single_badge.upper()} ",
            font=("Segoe UI", 8, "bold"), fg=b_fg,
            bg=b_bg, padx=6, pady=2,
        ).pack(side="right")


# ============================================================
# SCHEDULE TIMELINE CARD RENDERING (INLINE EDITING SYSTEM)
# ============================================================

def render_schedule(parent, schedule, bg=BG_MAIN, compact=False, allow_actions=False, on_action=None):
    """
    Renders a schedule list into `parent` as an interactive visual timeline.
    Supports complete INLINE EDITING and INLINE NOTES without any popup modals.
    """
    for widget in parent.winfo_children():
        widget.destroy()

    if not schedule:
        empty_card = tk.Frame(
            parent, bg=BG_CARD,
            highlightbackground=BORDER_COLOR, highlightthickness=1,
            bd=0, pady=30, padx=20,
        )
        empty_card.pack(fill="x", expand=True, padx=4, pady=10)

        tk.Label(
            empty_card,
            text="No schedule entries available.",
            font=FONT_BODY,
            bg=BG_CARD,
            fg=FG_MUTED,
        ).pack()
        return

    unique_schedule = []
    seen_entries = set()
    for entry in schedule:
        title = entry.get("title") or entry.get("name") or ""
        start = entry.get("start", "")
        end = entry.get("end", "")
        key = (title.strip().lower(), start, end)
        if key not in seen_entries:
            seen_entries.add(key)
            unique_schedule.append(entry)

    timeline_container = tk.Frame(parent, bg=bg)
    timeline_container.pack(fill="both", expand=True, padx=4, pady=4)

    for idx, entry in enumerate(unique_schedule):
        row_frame = tk.Frame(timeline_container, bg=bg)
        row_frame.pack(fill="x", expand=True, pady=6)

        # Timeline Left Pillar: Dot + Time
        pillar = tk.Frame(row_frame, bg=bg, width=140)
        pillar.pack(side="left", fill="y", padx=(0, 8))

        dot = TIMELINE_DOTS[idx % len(TIMELINE_DOTS)]
        start_12 = format_12h(entry.get("start", "00:00"))
        end_12 = format_12h(entry.get("end", "00:00"))

        dot_label = tk.Label(
            pillar, text=f"{dot} {start_12}",
            font=FONT_MONO, fg=PRIMARY_BLUE, bg=bg, anchor="w"
        )
        dot_label.pack(anchor="w")

        time_sub_label = tk.Label(
            pillar, text=f"   – {end_12}",
            font=FONT_SMALL, fg=FG_MUTED, bg=bg, anchor="w"
        )
        time_sub_label.pack(anchor="w")

        # Timeline Card Container
        card = tk.Frame(
            row_frame, bg=BG_CARD,
            highlightbackground=BORDER_COLOR, highlightthickness=1,
            bd=0, pady=10, padx=14,
        )
        card.pack(side="left", fill="x", expand=True)

        # Draw card in normal mode with closure over current entry state
        _draw_card_content(card, entry, pillar, dot_label, time_sub_label, compact, allow_actions, on_action)


def _draw_card_content(card, entry, pillar, dot_label, time_sub_label, compact, allow_actions, on_action, mode="normal"):
    """
    Renders card content in 'normal', 'edit', or 'note' mode.
    All edits happen inline inside `card` with ZERO popups.
    """
    for w in card.winfo_children():
        w.destroy()

    title_text = entry.get("title", "Task")
    start_time = entry.get("start", "00:00")
    end_time = entry.get("end", "00:00")
    etype = str(entry.get("type", "task")).lower()
    task_id = entry.get("task_id") or title_text
    icon = get_icon_for_title(title_text, etype=etype)
    desc_text = get_description_for_title(title_text, etype=etype)
    note_text = entry.get("note", "")

    # Update pillar time labels
    dot_label.config(text=f"{dot_label.cget('text').split()[0]} {format_12h(start_time)}")
    time_sub_label.config(text=f"   – {format_12h(end_time)}")

    # ========================================================
    # MODE: NORMAL DISPLAY
    # ========================================================
    if mode == "normal":
        # Top Row: Icon + Title + Badges
        top_line = tk.Frame(card, bg=BG_CARD)
        top_line.pack(fill="x")

        tk.Label(
            top_line, text=f"{icon} ",
            font=("Segoe UI", 12), bg=BG_CARD
        ).pack(side="left")

        title_lbl = tk.Label(
            top_line, text=title_text,
            font=FONT_SUBHEAD, fg=FG_MAIN, bg=BG_CARD,
            anchor="w"
        )
        title_lbl.pack(side="left")

        # Segment indicator
        if etype == "task":
            seg = entry.get("segment_number")
            tot = entry.get("total_segments")
            if seg and tot and tot > 1:
                tk.Label(
                    top_line, text=f" (Part {seg}/{tot})",
                    font=FONT_SMALL, fg=FG_MUTED, bg=BG_CARD,
                ).pack(side="left")

        # Badges (Deduplicated Single-Source Engine)
        badges_box = tk.Frame(top_line, bg=BG_CARD)
        badges_box.pack(side="right")
        render_task_badges(badges_box, entry)

        # Middle Row: Description + Note
        desc_line = tk.Frame(card, bg=BG_CARD)
        desc_line.pack(fill="x", pady=(4, 0))

        if not compact:
            tk.Label(
                desc_line, text=desc_text,
                font=FONT_SMALL, fg=FG_MUTED, bg=BG_CARD,
                anchor="w"
            ).pack(side="left")

        if note_text:
            tk.Label(
                desc_line, text=f"  💬 Note: {note_text}",
                font=("Segoe UI", 9, "italic"), fg="#0369a1", bg=BG_CARD,
                anchor="w"
            ).pack(side="left", padx=(8, 0))

        # Bottom Row: Action Controls
        if allow_actions and on_action:
            action_line = tk.Frame(card, bg=BG_CARD)
            action_line.pack(fill="x", pady=(8, 0))

            HoverButton(
                action_line, hover_bg="#bbf7d0",
                text=" ✓ Complete ",
                font=FONT_SMALL, bg="#dcfce7", fg="#166534",
                relief="flat", padx=8, pady=3, cursor="hand2",
                command=lambda: on_action("complete", task_id),
            ).pack(side="left", padx=(0, 6))

            HoverButton(
                action_line, hover_bg="#fecaca",
                text=" ✗ Incomplete ",
                font=FONT_SMALL, bg="#fee2e2", fg="#991b1b",
                relief="flat", padx=8, pady=3, cursor="hand2",
                command=lambda: on_action("incomplete", task_id),
            ).pack(side="left", padx=(0, 6))

            HoverButton(
                action_line, hover_bg=BTN_SEC_HOVER,
                text=" 💬 Note ",
                font=FONT_SMALL, bg=BTN_SEC_BG, fg=BTN_SEC_FG,
                relief="flat", padx=8, pady=3, cursor="hand2",
                command=lambda: _draw_card_content(card, entry, pillar, dot_label, time_sub_label, compact, allow_actions, on_action, mode="note"),
            ).pack(side="left", padx=(0, 6))

            HoverButton(
                action_line, hover_bg=BTN_SEC_HOVER,
                text=" ✎ Edit ",
                font=FONT_SMALL, bg=BTN_SEC_BG, fg=BTN_SEC_FG,
                relief="flat", padx=8, pady=3, cursor="hand2",
                command=lambda: _draw_card_content(card, entry, pillar, dot_label, time_sub_label, compact, allow_actions, on_action, mode="edit"),
            ).pack(side="left")

    # ========================================================
    # MODE: INLINE TASK EDIT
    # ========================================================
    elif mode == "edit":
        edit_hdr = tk.Frame(card, bg=BG_CARD)
        edit_hdr.pack(fill="x", pady=(0, 6))
        tk.Label(
            edit_hdr, text=f"✏️ Editing Task: {title_text}",
            font=FONT_SUBHEAD, fg=PRIMARY_BLUE, bg=BG_CARD
        ).pack(side="left")

        form_grid = tk.Frame(card, bg=BG_CARD)
        form_grid.pack(fill="x", pady=4)

        tk.Label(form_grid, text="Task Name:", font=FONT_SMALL, fg=FG_MAIN, bg=BG_CARD).grid(row=0, column=0, sticky="w", padx=(0, 8))
        t_var = tk.StringVar(value=title_text)
        t_ent = tk.Entry(form_grid, textvariable=t_var, font=FONT_BODY, bg=ENTRY_BG, fg=ENTRY_FG, relief="flat", highlightbackground=ENTRY_BORDER, highlightthickness=1, width=28)
        t_ent.grid(row=0, column=1, sticky="w", pady=2, ipady=2)

        tk.Label(form_grid, text="Start Time (HH:MM):", font=FONT_SMALL, fg=FG_MAIN, bg=BG_CARD).grid(row=1, column=0, sticky="w", padx=(0, 8), pady=(4, 0))
        s_var = tk.StringVar(value=start_time)
        s_ent = tk.Entry(form_grid, textvariable=s_var, font=FONT_BODY, bg=ENTRY_BG, fg=ENTRY_FG, relief="flat", highlightbackground=ENTRY_BORDER, highlightthickness=1, width=14)
        s_ent.grid(row=1, column=1, sticky="w", pady=(4, 2), ipady=2)

        tk.Label(form_grid, text="End Time (HH:MM):", font=FONT_SMALL, fg=FG_MAIN, bg=BG_CARD).grid(row=2, column=0, sticky="w", padx=(0, 8), pady=(4, 0))
        e_var = tk.StringVar(value=end_time)
        e_ent = tk.Entry(form_grid, textvariable=e_var, font=FONT_BODY, bg=ENTRY_BG, fg=ENTRY_FG, relief="flat", highlightbackground=ENTRY_BORDER, highlightthickness=1, width=14)
        e_ent.grid(row=2, column=1, sticky="w", pady=(4, 2), ipady=2)

        btn_row = tk.Frame(card, bg=BG_CARD)
        btn_row.pack(fill="x", pady=(8, 0))

        def _do_save():
            new_title = t_var.get().strip()
            new_s = s_var.get().strip()
            new_e = e_var.get().strip()

            if not new_title:
                messagebox.showwarning("Validation Error", "Task title cannot be empty.", parent=card.winfo_toplevel())
                return

            # Basic time format validation
            time_regex = r"^([01]?[0-9]|2[0-3]):[0-5][0-9]$"
            if not re.match(time_regex, new_s) or not re.match(time_regex, new_e):
                messagebox.showwarning("Validation Error", "Times must be in 24-hour HH:MM format (e.g. 08:30).", parent=card.winfo_toplevel())
                return

            entry["title"] = new_title
            entry["start"] = new_s
            entry["start_time"] = new_s
            entry["end"] = new_e
            entry["end_time"] = new_e

            if on_action:
                on_action("save_edit", (task_id, new_title, new_s, new_e))
            _draw_card_content(card, entry, pillar, dot_label, time_sub_label, compact, allow_actions, on_action, mode="normal")

        def _do_cancel():
            _draw_card_content(card, entry, pillar, dot_label, time_sub_label, compact, allow_actions, on_action, mode="normal")

        HoverButton(
            btn_row, hover_bg=PRIMARY_HOVER,
            text=" 💾 Save Changes ",
            font=FONT_SMALL, bg=BTN_BG, fg=BTN_FG,
            relief="flat", padx=10, pady=3, cursor="hand2",
            command=_do_save,
        ).pack(side="left", padx=(0, 6))

        HoverButton(
            btn_row, hover_bg=BTN_SEC_HOVER,
            text=" ✕ Cancel ",
            font=FONT_SMALL, bg=BTN_SEC_BG, fg=BTN_SEC_FG,
            relief="flat", padx=10, pady=3, cursor="hand2",
            command=_do_cancel,
        ).pack(side="left")

    # ========================================================
    # MODE: INLINE NOTE EDIT
    # ========================================================
    elif mode == "note":
        note_hdr = tk.Frame(card, bg=BG_CARD)
        note_hdr.pack(fill="x", pady=(0, 6))
        tk.Label(
            note_hdr, text=f"💬 Task Note for: {title_text}",
            font=FONT_SUBHEAD, fg=PRIMARY_BLUE, bg=BG_CARD
        ).pack(side="left")

        n_var = tk.StringVar(value=note_text)
        n_ent = tk.Entry(card, textvariable=n_var, font=FONT_BODY, bg=ENTRY_BG, fg=ENTRY_FG, relief="flat", highlightbackground=ENTRY_BORDER, highlightthickness=1, width=44)
        n_ent.pack(fill="x", ipady=3, pady=(2, 8))
        n_ent.focus_set()

        btn_row = tk.Frame(card, bg=BG_CARD)
        btn_row.pack(fill="x")

        def _do_save_note():
            new_note = n_var.get().strip()
            entry["note"] = new_note
            if on_action:
                on_action("save_note", (task_id, new_note))
            _draw_card_content(card, entry, pillar, dot_label, time_sub_label, compact, allow_actions, on_action, mode="normal")

        def _do_cancel_note():
            _draw_card_content(card, entry, pillar, dot_label, time_sub_label, compact, allow_actions, on_action, mode="normal")

        HoverButton(
            btn_row, hover_bg=PRIMARY_HOVER,
            text=" 💾 Save Note ",
            font=FONT_SMALL, bg=BTN_BG, fg=BTN_FG,
            relief="flat", padx=10, pady=3, cursor="hand2",
            command=_do_save_note,
        ).pack(side="left", padx=(0, 6))

        HoverButton(
            btn_row, hover_bg=BTN_SEC_HOVER,
            text=" ✕ Cancel ",
            font=FONT_SMALL, bg=BTN_SEC_BG, fg=BTN_SEC_FG,
            relief="flat", padx=10, pady=3, cursor="hand2",
            command=_do_cancel_note,
        ).pack(side="left")


# ============================================================
# MAIN APPLICATION WINDOW
# ============================================================

class DayWiseApp(tk.Tk):

    def __init__(self):
        super().__init__()

        self.planner = Planner()

        self.title("DayWise – Intelligent Daily Planning Dashboard")
        self.geometry("1400x860")
        self.minsize(1000, 680)
        self.configure(bg=BG_MAIN)

        self._current_page = None

        # Plan My Day interactive state
        self._one_time_tasks = []          # list of one-time task dicts
        self._routine_overrides = []       # list of routine overrides for selected date
        self._current_generated_plan = None # PlanRecord currently being reviewed

        # Clarification state
        self._clarification_active    = False
        self._clarification_question  = ""
        self._clarification_field     = ""
        self._clarification_title     = ""
        self._clarification_pending   = []
        self._clarification_original  = ""
        self._clarification_date      = ""

        # Process rollover on boot
        self.planner.check_date_rollover()

        self._build_layout()
        self._show_page("home")

    # --------------------------------------------------------
    # LAYOUT & NAVIGATION
    # --------------------------------------------------------

    def _build_layout(self):
        """Build main dark navy sidebar + main content layout."""
        self.sidebar = tk.Frame(
            self, bg=BG_SIDEBAR, width=220
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self._build_sidebar()

        self.content = tk.Frame(self, bg=BG_MAIN)
        self.content.pack(
            side="left", fill="both", expand=True
        )

    def _build_sidebar(self):
        """Populate left dark navy navigation sidebar."""
        logo_frame = tk.Frame(self.sidebar, bg=BG_SIDEBAR)
        logo_frame.pack(fill="x", pady=(24, 12), padx=16)

        header_title = tk.Frame(logo_frame, bg=BG_SIDEBAR)
        header_title.pack(anchor="w")

        tk.Label(
            header_title, text="⚡ ",
            font=("Segoe UI", 16), fg=PRIMARY_BLUE, bg=BG_SIDEBAR,
        ).pack(side="left")

        tk.Label(
            header_title, text="DAYWISE",
            font=("Segoe UI", 16, "bold"),
            fg="#ffffff", bg=BG_SIDEBAR,
        ).pack(side="left")

        tk.Label(
            logo_frame,
            text="Plan Smarter, Live Better",
            font=FONT_SMALL, fg=FG_SIDEBAR, bg=BG_SIDEBAR,
        ).pack(anchor="w", pady=(2, 0))

        ttk.Separator(self.sidebar, orient="horizontal").pack(
            fill="x", padx=16, pady=14
        )

        nav_items = [
            ("🏠  Home",         "home"),
            ("📅  Plan My Day",  "plan"),
            ("📋  Today's Plan",  "today"),
            ("📜  History",      "history"),
            ("✅  Tasks",        "tasks"),
            ("🔄  Routines",     "routines"),
            ("🧠  Memory",       "memory"),
            ("🔍  Search",       "search"),
        ]

        self._nav_buttons = {}

        for label, page in nav_items:
            btn = tk.Button(
                self.sidebar,
                text=label,
                font=FONT_BODY,
                fg=FG_SIDEBAR, bg=BG_SIDEBAR,
                bd=0, padx=18, pady=9,
                anchor="w", cursor="hand2",
                activebackground=PRIMARY_BLUE,
                activeforeground="#ffffff",
                command=lambda p=page: self._show_page(p),
            )
            btn.pack(fill="x", padx=8, pady=2)
            self._nav_buttons[page] = btn

        footer = tk.Frame(self.sidebar, bg=BG_SIDEBAR)
        footer.pack(side="bottom", fill="x", pady=16, padx=16)

        tk.Label(
            footer, text="DayWise v2.0",
            font=FONT_SMALL, fg=FG_SIDEBAR, bg=BG_SIDEBAR,
        ).pack(anchor="w")

    def _clear_content_frame(self):
        """Destroys all mounted widgets in content area to eliminate duplicate views."""
        for widget in self.content.winfo_children():
            widget.destroy()

    def _show_page(self, page_name):
        """Clear content area and render requested page with single-mount guarantee."""
        if page_name != "plan":
            self._clarification_active = False

        for name, btn in self._nav_buttons.items():
            if name == page_name:
                btn.config(
                    bg=PRIMARY_BLUE, fg="#ffffff",
                    font=("Segoe UI", 10, "bold")
                )
            else:
                btn.config(
                    bg=BG_SIDEBAR, fg=FG_SIDEBAR,
                    font=FONT_BODY
                )

        self._clear_content_frame()
        self._current_page = page_name

        page_builders = {
            "home":     self._page_home,
            "plan":     self._page_plan,
            "today":    self._page_today,
            "history":  self._page_history,
            "tasks":    self._page_tasks,
            "routines": self._page_routines,
            "memory":   self._page_memory,
            "search":   self._page_search,
        }

        builder = page_builders.get(page_name)
        if builder:
            builder()

    # ========================================================
    # PAGE: HOME DASHBOARD
    # ========================================================

    def _page_home(self):
        self._clear_content_frame()
        self.planner.check_date_rollover()

        frame = tk.Frame(self.content, bg=BG_MAIN)
        frame.pack(fill="both", expand=True, padx=36, pady=28)

        tk.Label(
            frame,
            text=f"Welcome back! 👋",
            font=FONT_TITLE, fg=FG_MAIN, bg=BG_MAIN,
        ).pack(anchor="w")

        today_label = format_date_display(today_str())
        tk.Label(
            frame,
            text=f"Today is {today_label}. Here is your planning dashboard overview.",
            font=FONT_BODY, fg=FG_MUTED, bg=BG_MAIN,
        ).pack(anchor="w", pady=(2, 16))

        # Metrics Row
        stats_row = tk.Frame(frame, bg=BG_MAIN)
        stats_row.pack(fill="x", pady=(0, 16))

        active_plan = self.planner.get_active_today_plan()
        active_cnt = len(active_plan.get("schedule", [])) if active_plan else 0
        periods_cnt = len(self.planner.load_routine_periods())
        future_cnt = len(self.planner.get_all_future_plans())
        hist_cnt = len(self.planner.get_latest_plans(100))

        def _stat_box(parent, title, value, icon, color="#2563eb", bg_tint="#eff6ff"):
            box = tk.Frame(
                parent, bg=bg_tint, padx=16, pady=12,
                highlightbackground=BORDER_COLOR, highlightthickness=1, bd=0,
            )
            box.pack(side="left", fill="both", expand=True, padx=4)
            tk.Label(box, text=f"{icon} {title}", font=FONT_SMALL, fg=FG_MUTED, bg=bg_tint).pack(anchor="w")
            tk.Label(box, text=str(value), font=("Segoe UI", 20, "bold"), fg=color, bg=bg_tint).pack(anchor="w", pady=(2, 0))

        _stat_box(stats_row, "Today's Scheduled Tasks", active_cnt, "📋", color="#16a34a", bg_tint="#dcfce7")
        _stat_box(stats_row, "Active Routine Periods", periods_cnt, "🔄", color="#2563eb", bg_tint="#eff6ff")
        _stat_box(stats_row, "Future Confirmed Plans", future_cnt, "📅", color="#0369a1", bg_tint="#e0f2fe")
        _stat_box(stats_row, "Completed History Days", hist_cnt, "📜", color="#475569", bg_tint="#f1f5f9")

        # Quick Actions Card
        act_card = tk.Frame(
            frame, bg=BG_CARD,
            highlightbackground=BORDER_COLOR, highlightthickness=1,
            bd=0, padx=20, pady=18,
        )
        act_card.pack(fill="x", pady=(0, 16))

        tk.Label(act_card, text="⚡ Quick Actions", font=FONT_HEADING, fg=FG_MAIN, bg=BG_CARD).pack(anchor="w", pady=(0, 10))

        actions_box = tk.Frame(act_card, bg=BG_CARD)
        actions_box.pack(fill="x")

        HoverButton(
            actions_box, hover_bg=PRIMARY_HOVER,
            text="  📅  Plan Today / Future Day  ",
            font=FONT_SUBHEAD, bg=BTN_BG, fg=BTN_FG,
            relief="flat", padx=14, pady=8, cursor="hand2",
            command=lambda: self._show_page("plan"),
        ).pack(side="left", padx=(0, 10))

        HoverButton(
            actions_box, hover_bg=BTN_SEC_HOVER,
            text="  📋  View Today's Execution  ",
            font=FONT_SUBHEAD, bg=BTN_SEC_BG, fg=BTN_SEC_FG,
            relief="flat", padx=14, pady=8, cursor="hand2",
            command=lambda: self._show_page("today"),
        ).pack(side="left", padx=(0, 10))

        HoverButton(
            actions_box, hover_bg=BTN_SEC_HOVER,
            text="  🔄  Routine Periods & Habits  ",
            font=FONT_SUBHEAD, bg=BTN_SEC_BG, fg=BTN_SEC_FG,
            relief="flat", padx=14, pady=8, cursor="hand2",
            command=lambda: self._show_page("routines"),
        ).pack(side="left")

    # ========================================================
    # PAGE: PLAN MY DAY (DATE SELECTION + ROUTINES + ONE-TIME + NLP)
    # ========================================================

    def _page_plan(self):
        self._clear_content_frame()
        frame = tk.Frame(self.content, bg=BG_MAIN)
        frame.pack(fill="both", expand=True, padx=36, pady=28)

        # Header Row
        header_row = tk.Frame(frame, bg=BG_MAIN)
        header_row.pack(fill="x", pady=(0, 6))

        tk.Label(
            header_row, text="Plan My Day 📅",
            font=FONT_TITLE, fg=FG_MAIN, bg=BG_MAIN,
        ).pack(side="left")

        # Scrollable workspace
        scroll = ScrollableFrame(frame, bg=BG_MAIN)
        scroll.pack(fill="both", expand=True, pady=(6, 0))
        body = scroll.inner

        # --- Card 1: Date Selector (Calendar Picker) ---
        date_card = tk.Frame(
            body, bg=BG_CARD,
            highlightbackground=BORDER_COLOR, highlightthickness=1,
            bd=0, padx=16, pady=12,
        )
        date_card.pack(fill="x", pady=(0, 12))

        tk.Label(
            date_card, text="📅 Planning Date:",
            font=FONT_SUBHEAD, fg=FG_MAIN, bg=BG_CARD,
        ).pack(side="left", padx=(0, 10))

        if not hasattr(self, "_plan_date_var") or not self._plan_date_var.get():
            self._plan_date_var = tk.StringVar(value=today_str())

        # Display entry (read-only presentation; user can also type directly)
        date_entry = tk.Entry(
            date_card, textvariable=self._plan_date_var,
            font=("Segoe UI", 10, "bold"), bg=ENTRY_BG, fg=PRIMARY_BLUE,
            highlightbackground=ENTRY_BORDER, highlightthickness=1,
            relief="flat", width=13,
        )
        date_entry.pack(side="left", padx=(0, 4), ipady=3)

        def _set_date(d_str):
            self._plan_date_var.set(d_str)
            self._one_time_tasks.clear()
            self._routine_overrides.clear()
            self._current_generated_plan = None
            self._refresh_applicable_routines_display()

        def _open_calendar():
            """Opens the CalendarPicker popup; _set_date is called on selection."""
            CalendarPicker(self, self._plan_date_var, callback=_set_date)

        # Calendar icon button
        HoverButton(
            date_card, hover_bg=PRIMARY_HOVER,
            text="📆 Pick Date", font=FONT_SMALL,
            bg=BTN_BG, fg=BTN_FG,
            relief="flat", padx=8, pady=3, cursor="hand2",
            command=_open_calendar,
        ).pack(side="left", padx=(0, 6))

        # Quick shortcuts
        HoverButton(date_card, hover_bg=BTN_SEC_HOVER, text="Today", font=FONT_SMALL, bg=BTN_SEC_BG, fg=BTN_SEC_FG, relief="flat", padx=8, pady=3, cursor="hand2", command=lambda: _set_date(today_str())).pack(side="left", padx=2)
        HoverButton(date_card, hover_bg=BTN_SEC_HOVER, text="Tomorrow", font=FONT_SMALL, bg=BTN_SEC_BG, fg=BTN_SEC_FG, relief="flat", padx=8, pady=3, cursor="hand2", command=lambda: _set_date(tomorrow_str())).pack(side="left", padx=2)
        HoverButton(date_card, hover_bg=PRIMARY_HOVER, text="Load", font=FONT_SMALL, bg=BTN_BG, fg=BTN_FG, relief="flat", padx=8, pady=3, cursor="hand2", command=lambda: _set_date(self._plan_date_var.get().strip())).pack(side="left", padx=6)

        # --- Card 2: Applicable Routines for this Day ---
        self._routines_box = tk.Frame(
            body, bg=BG_CARD,
            highlightbackground=BORDER_COLOR, highlightthickness=1,
            bd=0, padx=16, pady=12,
        )
        self._routines_box.pack(fill="x", pady=(0, 12))

        # --- Card 3: Date-Specific One-Time Tasks ---
        onetime_card = tk.Frame(
            body, bg=BG_CARD,
            highlightbackground=BORDER_COLOR, highlightthickness=1,
            bd=0, padx=16, pady=12,
        )
        onetime_card.pack(fill="x", pady=(0, 12))

        tk.Label(
            onetime_card, text="➕ Add One-Time Tasks for this Date",
            font=FONT_SUBHEAD, fg=FG_MAIN, bg=BG_CARD,
        ).pack(anchor="w", pady=(0, 6))

        ot_form = tk.Frame(onetime_card, bg=BG_CARD)
        ot_form.pack(fill="x", pady=(0, 8))

        tk.Label(ot_form, text="Task Name:", font=FONT_SMALL, fg=FG_MUTED, bg=BG_CARD).grid(row=0, column=0, sticky="w")
        tk.Label(ot_form, text="Duration (min):", font=FONT_SMALL, fg=FG_MUTED, bg=BG_CARD).grid(row=0, column=1, sticky="w", padx=6)
        tk.Label(ot_form, text="Deadline (opt):", font=FONT_SMALL, fg=FG_MUTED, bg=BG_CARD).grid(row=0, column=2, sticky="w", padx=6)
        tk.Label(ot_form, text="Priority:", font=FONT_SMALL, fg=FG_MUTED, bg=BG_CARD).grid(row=0, column=3, sticky="w", padx=6)

        ot_title_var = tk.StringVar()
        ot_dur_var = tk.StringVar(value="60")
        ot_dl_var = tk.StringVar()
        ot_prio_var = tk.StringVar(value="normal")

        tk.Entry(ot_form, textvariable=ot_title_var, font=FONT_BODY, bg=ENTRY_BG, fg=ENTRY_FG, highlightbackground=ENTRY_BORDER, highlightthickness=1, relief="flat", width=30).grid(row=1, column=0, sticky="w", ipady=3)
        tk.Entry(ot_form, textvariable=ot_dur_var, font=FONT_BODY, bg=ENTRY_BG, fg=ENTRY_FG, highlightbackground=ENTRY_BORDER, highlightthickness=1, relief="flat", width=12).grid(row=1, column=1, sticky="w", padx=6, ipady=3)
        tk.Entry(ot_form, textvariable=ot_dl_var, font=FONT_BODY, bg=ENTRY_BG, fg=ENTRY_FG, highlightbackground=ENTRY_BORDER, highlightthickness=1, relief="flat", width=14).grid(row=1, column=2, sticky="w", padx=6, ipady=3)

        prio_cb = ttk.Combobox(ot_form, textvariable=ot_prio_var, values=["very high", "high", "normal", "low"], width=10, state="readonly")
        prio_cb.grid(row=1, column=3, sticky="w", padx=6, ipady=2)

        def _add_onetime():
            t = ot_title_var.get().strip()
            if not t:
                messagebox.showwarning("Missing Title", "Please enter a task title.", parent=self)
                return
            try:
                dur = int(ot_dur_var.get().strip() or "60")
            except ValueError:
                dur = 60
            dl = ot_dl_var.get().strip() or None
            prio = ot_prio_var.get()

            self._one_time_tasks.append({
                "title": t,
                "duration": dur,
                "deadline": dl,
                "priority": prio,
                "source": "one-time",
                "type": "task",
                "status": "pending",
                "note": "",
            })
            ot_title_var.set("")
            ot_dl_var.set("")
            self._refresh_onetime_display(onetime_card)

        HoverButton(ot_form, hover_bg=PRIMARY_HOVER, text=" + Add Task ", font=FONT_SMALL, bg=BTN_BG, fg=BTN_FG, relief="flat", padx=10, pady=3, cursor="hand2", command=_add_onetime).grid(row=1, column=4, sticky="w", padx=8)

        self._onetime_list_frame = tk.Frame(onetime_card, bg=BG_CARD)
        self._onetime_list_frame.pack(fill="x", pady=(4, 0))

        # --- Card 4: Natural Language Conversational Input ---
        nlp_card = tk.Frame(
            body, bg=BG_CARD,
            highlightbackground=BORDER_COLOR, highlightthickness=1,
            bd=0, padx=16, pady=12,
        )
        nlp_card.pack(fill="x", pady=(0, 12))

        tk.Label(
            nlp_card, text="💬 Natural Language Instructions (Optional):",
            font=FONT_SUBHEAD, fg=FG_MAIN, bg=BG_CARD,
        ).pack(anchor="w", pady=(0, 4))

        tk.Label(
            nlp_card, text='e.g. "I have a meeting at 3 PM and need to study Python for 2 hours before that"',
            font=FONT_SMALL, fg=FG_MUTED, bg=BG_CARD,
        ).pack(anchor="w", pady=(0, 6))

        self._input_text = tk.Text(
            nlp_card, height=3, width=80,
            font=FONT_BODY, bg=ENTRY_BG, fg=ENTRY_FG,
            highlightbackground=ENTRY_BORDER, highlightthickness=1,
            relief="flat", padx=10, pady=8, wrap="word",
        )
        self._input_text.pack(fill="x", pady=(0, 8))

        # Action row: Generate Plan
        gen_row = tk.Frame(body, bg=BG_MAIN)
        gen_row.pack(fill="x", pady=(4, 10))

        HoverButton(
            gen_row, hover_bg=PRIMARY_HOVER,
            text="  📅  Generate My Plan  ",
            font=FONT_SUBHEAD, bg=BTN_BG, fg=BTN_FG,
            relief="flat", padx=18, pady=10, cursor="hand2",
            command=self._execute_generate_plan,
        ).pack(side="left", padx=(0, 10))

        HoverButton(
            gen_row, hover_bg=BTN_SEC_HOVER,
            text="  ✕  Clear All  ",
            font=FONT_BODY, bg=BTN_SEC_BG, fg=BTN_SEC_FG,
            relief="flat", padx=12, pady=10, cursor="hand2",
            command=self._clear_plan_inputs,
        ).pack(side="left")

        self._plan_status = tk.Label(
            body, text="", font=FONT_BODY, fg="#166534", bg=BG_MAIN,
        )
        self._plan_status.pack(anchor="w", pady=(0, 8))

        # Clarification Panel
        self._clarif_panel = tk.Frame(
            body, bg="#fffbeb", highlightbackground="#fbbf24", highlightthickness=2, bd=0, padx=20, pady=16,
        )
        tk.Label(self._clarif_panel, text="🤔 DayWise needs clarification", font=FONT_SUBHEAD, fg="#92400e", bg="#fffbeb").pack(anchor="w", pady=(0, 4))
        self._clarif_question_label = tk.Label(self._clarif_panel, text="", font=FONT_BODY, fg=FG_MAIN, bg="#fffbeb", wraplength=700, justify="left")
        self._clarif_question_label.pack(anchor="w", pady=(0, 8))
        self._clarif_answer_var = tk.StringVar()
        self._clarif_entry_widget = tk.Entry(self._clarif_panel, textvariable=self._clarif_answer_var, font=("Segoe UI", 12), bg=ENTRY_BG, fg=ENTRY_FG, highlightbackground="#fbbf24", highlightthickness=1, relief="flat", width=28)
        self._clarif_entry_widget.pack(anchor="w", ipady=4, pady=(0, 8))
        self._clarif_entry_widget.bind("<Return>", lambda e: self._submit_clarification())

        c_btns = tk.Frame(self._clarif_panel, bg="#fffbeb")
        c_btns.pack(anchor="w")
        HoverButton(c_btns, hover_bg=PRIMARY_HOVER, text=" Continue ➜ ", font=FONT_SMALL, bg=BTN_BG, fg=BTN_FG, relief="flat", padx=12, pady=6, cursor="hand2", command=self._submit_clarification).pack(side="left", padx=(0, 6))
        HoverButton(c_btns, hover_bg=BTN_SEC_HOVER, text=" Cancel ", font=FONT_SMALL, bg=BTN_SEC_BG, fg=BTN_SEC_FG, relief="flat", padx=10, pady=6, cursor="hand2", command=self._cancel_clarification).pack(side="left")

        # Review & Confirmation Section
        self._review_section = tk.Frame(body, bg=BG_MAIN)
        self._review_section.pack(fill="both", expand=True, pady=(6, 0))

        # Initial render of routines
        self._refresh_applicable_routines_display()

    def _refresh_applicable_routines_display(self):
        """Refreshes applicable routines for the selected date with INLINE override editing."""
        for w in self._routines_box.winfo_children():
            w.destroy()

        sel_date = self._plan_date_var.get().strip() or today_str()
        weekday = get_weekday_name(sel_date)
        period = self.planner.data_manager.get_active_routine_period_for_date(sel_date)
        period_title = f" ({period.get('name')})" if period else " (Default Recurring)"

        tk.Label(
            self._routines_box,
            text=f"🔄 Applicable Routines for {weekday}, {sel_date}{period_title}",
            font=FONT_SUBHEAD, fg=FG_MAIN, bg=BG_CARD,
        ).pack(anchor="w", pady=(0, 6))

        routines = self.planner.get_routines_for_date(sel_date)

        if not routines:
            tk.Label(
                self._routines_box,
                text="No routines configured for this weekday. You can create routine periods in the Routines tab.",
                font=FONT_SMALL, fg=FG_MUTED, bg=BG_CARD,
            ).pack(anchor="w")
            return

        for r in routines:
            row = tk.Frame(self._routines_box, bg=PRIMARY_LIGHT, padx=10, pady=6, highlightbackground=BORDER_COLOR, highlightthickness=1, bd=0)
            row.pack(fill="x", pady=3)
            self._draw_applicable_routine_row(row, r, sel_date, mode="normal")

    def _draw_applicable_routine_row(self, row, r, sel_date, mode="normal"):
        for w in row.winfo_children():
            w.destroy()

        name = r.get("name") or r.get("title", "Routine")
        start = r.get("start") or r.get("start_time", "08:00")
        dur = r.get("duration", 60)
        is_overridden = any(ro.get("name") == name for ro in self._routine_overrides)

        if mode == "normal":
            tk.Label(row, text=f"🔄 {name}", font=FONT_SUBHEAD, fg=FG_MAIN, bg=PRIMARY_LIGHT).pack(side="left", padx=(0, 8))
            tk.Label(row, text=f"{format_12h(start)} ({dur} min)", font=FONT_BODY, fg=FG_MUTED, bg=PRIMARY_LIGHT).pack(side="left", padx=(0, 8))

            if is_overridden:
                tk.Label(row, text=" OVERRIDE ", font=("Segoe UI", 7, "bold"), fg="#92400e", bg="#fef3c7", padx=4, pady=1).pack(side="left")
            else:
                tk.Label(row, text=" ROUTINE ", font=("Segoe UI", 7, "bold"), fg="#0369a1", bg="#e0f2fe", padx=4, pady=1).pack(side="left")

            HoverButton(
                row, hover_bg=BTN_SEC_HOVER,
                text=" ✎ Override for this day ",
                font=FONT_SMALL, bg=BTN_SEC_BG, fg=BTN_SEC_FG,
                relief="flat", padx=8, pady=2, cursor="hand2",
                command=lambda: self._draw_applicable_routine_row(row, r, sel_date, mode="edit"),
            ).pack(side="right")

        elif mode == "edit":
            tk.Label(row, text=f"Override '{name}' for {sel_date}:", font=FONT_SMALL, fg=PRIMARY_BLUE, bg=PRIMARY_LIGHT).pack(side="left", padx=(0, 6))

            tk.Label(row, text="Start:", font=FONT_SMALL, fg=FG_MUTED, bg=PRIMARY_LIGHT).pack(side="left")
            st_var = tk.StringVar(value=start)
            st_ent = tk.Entry(row, textvariable=st_var, font=FONT_SMALL, width=8)
            st_ent.pack(side="left", padx=2)

            tk.Label(row, text="Duration (min):", font=FONT_SMALL, fg=FG_MUTED, bg=PRIMARY_LIGHT).pack(side="left", padx=(4, 0))
            dur_var = tk.StringVar(value=str(dur))
            dur_ent = tk.Entry(row, textvariable=dur_var, font=FONT_SMALL, width=5)
            dur_ent.pack(side="left", padx=2)

            def _apply():
                st = st_var.get().strip()
                try:
                    d = int(dur_var.get().strip())
                except ValueError:
                    d = 60
                self._routine_overrides = [ro for ro in self._routine_overrides if ro.get("name") != name]
                self._routine_overrides.append({
                    "routine_id": r.get("routine_id"),
                    "name": name,
                    "title": name,
                    "start_time": st,
                    "start": st,
                    "duration": d,
                    "enabled": True,
                })
                r["start"] = st
                r["start_time"] = st
                r["duration"] = d
                self._draw_applicable_routine_row(row, r, sel_date, mode="normal")

            def _cancel():
                self._draw_applicable_routine_row(row, r, sel_date, mode="normal")

            HoverButton(row, hover_bg=PRIMARY_HOVER, text=" Apply ", font=FONT_SMALL, bg=BTN_BG, fg=BTN_FG, relief="flat", padx=8, pady=2, cursor="hand2", command=_apply).pack(side="left", padx=4)
            HoverButton(row, hover_bg=BTN_SEC_HOVER, text=" Cancel ", font=FONT_SMALL, bg=BTN_SEC_BG, fg=BTN_SEC_FG, relief="flat", padx=6, pady=2, cursor="hand2", command=_cancel).pack(side="left")

    def _refresh_onetime_display(self, container):
        """Refreshes one-time task card rows with inline remove."""
        for w in self._onetime_list_frame.winfo_children():
            w.destroy()

        if not self._one_time_tasks:
            return

        for idx, ot in enumerate(self._one_time_tasks):
            r = tk.Frame(self._onetime_list_frame, bg="#faf5ff", padx=10, pady=5, highlightbackground="#f3e8ff", highlightthickness=1, bd=0)
            r.pack(fill="x", pady=2)

            tk.Label(r, text=f"📌 {ot['title']}", font=FONT_SUBHEAD, fg="#6b21a8", bg="#faf5ff").pack(side="left", padx=(0, 6))
            tk.Label(r, text=f"({ot['duration']} min | Priority: {ot['priority']})", font=FONT_SMALL, fg=FG_MUTED, bg="#faf5ff").pack(side="left")
            tk.Label(r, text=" ONE-TIME ", font=("Segoe UI", 7, "bold"), fg="#86198f", bg="#fae8ff", padx=4, pady=1).pack(side="left", padx=6)

            def _remove(i=idx):
                self._one_time_tasks.pop(i)
                self._refresh_onetime_display(container)

            HoverButton(r, hover_bg="#fecaca", text=" Remove ", font=FONT_SMALL, bg=BTN_DANGER_BG, fg=BTN_DANGER_FG, relief="flat", padx=6, pady=1, cursor="hand2", command=_remove).pack(side="right")

    def _clear_plan_inputs(self):
        self._input_text.delete("1.0", "end")
        self._one_time_tasks.clear()
        self._routine_overrides.clear()
        self._current_generated_plan = None
        self._cancel_clarification(silent=True)
        self._refresh_applicable_routines_display()
        for w in self._onetime_list_frame.winfo_children():
            w.destroy()
        for w in self._review_section.winfo_children():
            w.destroy()
        self._plan_status.config(text="")

    def _execute_generate_plan(self):
        """Generates the plan from routines, overrides, one-time tasks, and NLP input."""
        plan_date = self._plan_date_var.get().strip() or today_str()
        raw_text = self._input_text.get("1.0", "end").strip()

        self._plan_status.config(text="⏳ Generating schedule...", fg=FG_MUTED)
        self.update_idletasks()

        try:
            result = self.planner.generate_date_plan(
                plan_date=plan_date,
                one_time_tasks=self._one_time_tasks,
                routine_overrides=self._routine_overrides,
                raw_input=raw_text,
            )
        except Exception as exc:
            self._plan_status.config(text=f"❌ Error: {exc}", fg="#991b1b")
            return

        if result.get("needs_clarification"):
            self._handle_plan_result(result, raw_text, plan_date)
            return

        # Show NLP warning if natural language could not be fully parsed
        if result.get("nlp_warning"):
            messagebox.showwarning(
                "Natural Language Instruction",
                result["nlp_warning"] + "\n\nThe rest of your routines and manual tasks have been scheduled normally.",
                parent=self,
            )

        # Inform user about NLP tasks included
        nlp_count = result.get("nlp_tasks_count", 0)
        if nlp_count and raw_text:
            self._plan_status.config(
                text=f"💬 {nlp_count} NLP task(s) included from your instruction. Review and confirm below.",
                fg="#1d4ed8",
            )
            self.update_idletasks()

        self._current_generated_plan = result
        self._render_plan_review_and_confirm(result)

    def _render_plan_review_and_confirm(self, plan_data):
        """Renders generated plan in editable review state with prominent Confirm button."""
        for w in self._review_section.winfo_children():
            w.destroy()

        schedule = plan_data.get("schedule", [])
        plan_date = plan_data.get("date", today_str())

        rev_card = tk.Frame(
            self._review_section, bg=BG_CARD,
            highlightbackground=BORDER_COLOR, highlightthickness=1,
            bd=0, padx=18, pady=16,
        )
        rev_card.pack(fill="x", pady=(10, 0))

        # Top confirmation bar
        top_bar = tk.Frame(rev_card, bg=BG_CARD)
        top_bar.pack(fill="x", pady=(0, 12))

        title_box = tk.Frame(top_bar, bg=BG_CARD)
        title_box.pack(side="left")

        tk.Label(title_box, text=f"📋 Review Generated Schedule ({format_date_display(plan_date)})", font=FONT_HEADING, fg=FG_MAIN, bg=BG_CARD).pack(anchor="w")
        tk.Label(title_box, text="Review schedule below, then click Confirm Plan to activate.", font=FONT_SMALL, fg=FG_MUTED, bg=BG_CARD).pack(anchor="w")

        # Prominent CONFIRM PLAN Button
        def _on_confirm():
            try:
                res = self.planner.confirm_plan(self._current_generated_plan)
                if res.get("status") == "active":
                    messagebox.showinfo(
                        "Plan Confirmed",
                        f"Today's Plan for {plan_date} has been confirmed and is now ACTIVE!\n\n"
                        "You can now track execution and task completion in Today's Plan tab.",
                        parent=self,
                    )
                    self._show_page("today")
                elif res.get("status") == "future_confirmed":
                    messagebox.showinfo(
                        "Future Plan Confirmed",
                        f"Plan for {plan_date} has been confirmed and stored as a FUTURE CONFIRMED PLAN.\n\n"
                        f"It will automatically become Today's Active Plan when {plan_date} arrives.",
                        parent=self,
                    )
                    self._show_page("memory")
            except Exception as e:
                messagebox.showerror("Confirmation Error", str(e), parent=self)

        HoverButton(
            top_bar, hover_bg=BTN_SUCCESS_HOVER,
            text="  🚀  CONFIRM PLAN  ",
            font=("Segoe UI", 12, "bold"), bg=BTN_SUCCESS_BG, fg="#ffffff",
            relief="flat", padx=18, pady=8, cursor="hand2",
            command=_on_confirm,
        ).pack(side="right")

        # Render schedule timeline
        sched_box = tk.Frame(rev_card, bg=BG_CARD)
        sched_box.pack(fill="x", pady=6)
        render_schedule(sched_box, schedule, bg=BG_CARD, compact=False)

        self._plan_status.config(
            text=f"✅ Generated {len(schedule)} schedule items for {plan_date}. Review above and click Confirm Plan.",
            fg="#166534",
        )

    # --------------------------------------------------------
    # CLARIFICATION PANEL LOGIC
    # --------------------------------------------------------

    def _show_clarification_panel(self, question):
        if hasattr(self, "_clarif_panel"):
            self._clarif_question_label.config(text=question)
            self._clarif_answer_var.set("")
            self._clarif_panel.pack(fill="x", pady=(0, 12))
            self._clarif_entry_widget.focus_set()

    def _hide_clarification_panel(self):
        if hasattr(self, "_clarif_panel"):
            self._clarif_panel.pack_forget()

    def _cancel_clarification(self, silent=False):
        self._clarification_active   = False
        self._clarification_question = ""
        self._clarification_field    = ""
        self._clarification_title    = ""
        self._clarification_pending  = []
        self._clarification_original = ""
        self._clarification_date     = ""
        self._hide_clarification_panel()
        if not silent and hasattr(self, "_plan_status"):
            self._plan_status.config(text="", fg="#166534")

    def _submit_clarification(self):
        answer = self._clarif_answer_var.get().strip()
        if not answer:
            messagebox.showwarning("Clarification", "Please enter an answer.", parent=self)
            return

        field     = self._clarification_field
        task_title = self._clarification_title
        pending   = self._clarification_pending
        original  = self._clarification_original
        plan_date = self._clarification_date

        try:
            result = self.planner.continue_plan(
                original_input=original,
                pending_tasks=pending,
                plan_date=plan_date,
                field=field,
                value=answer,
                task_title=task_title,
            )
        except Exception as exc:
            self._plan_status.config(text=f"❌ Error: {exc}", fg="#991b1b")
            return

        if result.get("needs_clarification"):
            self._handle_plan_result(result, original, plan_date)
        else:
            self._cancel_clarification(silent=True)
            self._current_generated_plan = result
            self._render_plan_review_and_confirm(result)

    def _handle_plan_result(self, result, raw_input, plan_date):
        if result.get("needs_clarification"):
            self._clarification_active   = True
            self._clarification_question = result["question"]
            self._clarification_field    = result["field"]
            self._clarification_title    = result["task_title"]
            self._clarification_pending  = result.get("pending_tasks", [])
            self._clarification_original = result.get("original_input", raw_input)
            self._clarification_date     = result.get("plan_date", plan_date)
            self._show_clarification_panel(result["question"])
        else:
            self._cancel_clarification(silent=True)
            self._current_generated_plan = result
            self._render_plan_review_and_confirm(result)

    # ========================================================
    # PAGE: TODAY'S PLAN  (Live Execution Dashboard)
    # ========================================================

    def _page_today(self):
        self._clear_content_frame()
        self.planner.check_date_rollover()

        frame = tk.Frame(self.content, bg=BG_MAIN)
        frame.pack(fill="both", expand=True, padx=36, pady=28)

        active_plan = self.planner.get_active_today_plan()

        # Top Bar
        top_bar = tk.Frame(frame, bg=BG_MAIN)
        top_bar.pack(fill="x", pady=(0, 6))

        title_box = tk.Frame(top_bar, bg=BG_MAIN)
        title_box.pack(side="left")

        tk.Label(
            title_box,
            text="Today's Execution Dashboard 📋",
            font=FONT_TITLE, fg=FG_MAIN, bg=BG_MAIN,
        ).pack(anchor="w")

        today_label = format_date_display(today_str())
        tk.Label(
            title_box,
            text=f"Active daily execution plan for {today_label}.",
            font=FONT_BODY, fg=FG_MUTED, bg=BG_MAIN,
        ).pack(anchor="w", pady=(2, 0))

        right_box = tk.Frame(top_bar, bg=BG_MAIN)
        right_box.pack(side="right")

        if active_plan:
            tk.Label(
                right_box,
                text=" 🟢 ACTIVE PLAN ",
                font=("Segoe UI", 9, "bold"), fg="#166534", bg="#dcfce7",
                padx=10, pady=5,
            ).pack(side="left", padx=(0, 8))

            def _finalize_day_action():
                if messagebox.askyesno(
                    "Finalize Day",
                    "Are you sure you want to finalize today's plan?\n\n"
                    "This will move today's plan to permanent History as a finalized record.",
                    parent=self,
                ):
                    self.planner.finalize_active_day()
                    messagebox.showinfo("Day Finalized", "Today's plan has been finalized and saved to History.", parent=self)
                    self._show_page("history")

            HoverButton(
                right_box, hover_bg=PRIMARY_HOVER,
                text=" 🔒 Finalize Day ",
                font=FONT_SMALL, bg=BTN_BG, fg=BTN_FG,
                relief="flat", padx=10, pady=5, cursor="hand2",
                command=_finalize_day_action,
            ).pack(side="left", padx=(0, 6))

        HoverButton(
            right_box, hover_bg=BTN_SEC_HOVER,
            text=" 🔄 Refresh ",
            font=FONT_SMALL, bg=BTN_SEC_BG, fg=BTN_SEC_FG,
            relief="flat", padx=8, pady=5, cursor="hand2",
            command=self._page_today,
        ).pack(side="left")

        ttk.Separator(frame, orient="horizontal").pack(fill="x", pady=12)

        if not active_plan:
            empty_box = tk.Frame(
                frame, bg=BG_CARD, highlightbackground=BORDER_COLOR, highlightthickness=1, bd=0, padx=30, pady=40,
            )
            empty_box.pack(fill="both", expand=True, pady=10)

            tk.Label(empty_box, text="No Active Plan Confirmed for Today", font=FONT_TITLE, fg=FG_MAIN, bg=BG_CARD).pack(pady=(0, 8))
            tk.Label(
                empty_box,
                text="You haven't confirmed a plan for today yet.\nGo to Plan My Day to load your routines and create today's plan.",
                font=FONT_BODY, fg=FG_MUTED, bg=BG_CARD, justify="center",
            ).pack(pady=(0, 16))

            HoverButton(
                empty_box, hover_bg=PRIMARY_HOVER,
                text="  📅  Plan Today's Schedule  ",
                font=FONT_SUBHEAD, bg=BTN_BG, fg=BTN_FG,
                relief="flat", padx=18, pady=10, cursor="hand2",
                command=lambda: self._show_page("plan"),
            ).pack()
            return

        # Active Schedule Execution View
        schedule = active_plan.get("schedule", [])

        dashboard_row = tk.Frame(frame, bg=BG_MAIN)
        dashboard_row.pack(fill="both", expand=True)
        dashboard_row.columnconfigure(0, weight=3)
        dashboard_row.columnconfigure(1, weight=1)
        dashboard_row.rowconfigure(0, weight=1)

        left_col = tk.Frame(dashboard_row, bg=BG_MAIN)
        left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 14))

        scroll = ScrollableFrame(left_col, bg=BG_MAIN)
        scroll.pack(fill="both", expand=True)

        def _on_task_action(action, data):
            if action == "complete":
                self.planner.update_active_task(data, status="completed")
                self._page_today()
            elif action == "incomplete":
                self.planner.update_active_task(data, status="not_completed")
                self._page_today()
            elif action == "save_note":
                tid, note_str = data
                self.planner.update_active_task(tid, note=note_str)
                self._page_today()
            elif action == "save_edit":
                tid, title_str, start_str, end_str = data
                self.planner.update_active_task(tid, title=title_str, start_time=start_str, end_time=end_str)
                self._page_today()

        render_schedule(scroll.inner, schedule, bg=BG_MAIN, allow_actions=True, on_action=_on_task_action)

        # Right Summary Column (Progress Overview)
        right_col = tk.Frame(dashboard_row, bg=BG_CARD, highlightbackground=BORDER_COLOR, highlightthickness=1, bd=0, padx=18, pady=18)
        right_col.grid(row=0, column=1, sticky="nsew")

        tk.Label(right_col, text="📊 Progress Overview", font=FONT_HEADING, fg=FG_MAIN, bg=BG_CARD).pack(anchor="w", pady=(0, 12))

        completed_cnt = sum(1 for e in schedule if e.get("status") == "completed")
        not_comp_cnt = sum(1 for e in schedule if e.get("status") in ("not_completed", "not completed"))
        pending_cnt = sum(1 for e in schedule if e.get("status", "pending") == "pending")
        total_cnt = len(schedule)

        def _met(parent, title, val, color="#2563eb", bg_tint="#eff6ff"):
            box = tk.Frame(parent, bg=bg_tint, padx=12, pady=8, highlightbackground=BORDER_COLOR, highlightthickness=1, bd=0)
            box.pack(fill="x", pady=4)
            tk.Label(box, text=title, font=FONT_SMALL, fg=FG_MUTED, bg=bg_tint).pack(anchor="w")
            tk.Label(box, text=str(val), font=("Segoe UI", 16, "bold"), fg=color, bg=bg_tint).pack(anchor="w")

        _met(right_col, "Total Scheduled Items", total_cnt, color="#475569", bg_tint="#f1f5f9")
        _met(right_col, "Completed Tasks", completed_cnt, color="#166534", bg_tint="#dcfce7")
        _met(right_col, "Pending Tasks", pending_cnt, color="#854d0e", bg_tint="#fef9c3")
        _met(right_col, "Incomplete Tasks", not_comp_cnt, color="#991b1b", bg_tint="#fee2e2")

    # ========================================================
    # PAGE: HISTORY (IMMUTABLE BY DEFAULT + AUDITED HISTORICAL EDITS)
    # ========================================================

    def _page_history(self):
        self._clear_content_frame()
        self.planner.check_date_rollover()

        frame = tk.Frame(self.content, bg=BG_MAIN)
        frame.pack(fill="both", expand=True, padx=36, pady=28)

        tk.Label(
            frame, text="History & Past Plans 📜",
            font=FONT_TITLE, fg=FG_MAIN, bg=BG_MAIN,
        ).pack(anchor="w")

        tk.Label(
            frame, text="View completed historical days. Historical records are read-only by default and preserve complete audit trails.",
            font=FONT_SMALL, fg=FG_MUTED, bg=BG_MAIN,
        ).pack(anchor="w", pady=(2, 10))

        # Search Bar Card
        search_card = tk.Frame(frame, bg=BG_CARD, highlightbackground=BORDER_COLOR, highlightthickness=1, bd=0, padx=14, pady=10)
        search_card.pack(fill="x", pady=(0, 12))

        tk.Label(search_card, text="🔍 Search past plans", font=FONT_SUBHEAD, fg=FG_MAIN, bg=BG_CARD).pack(side="left", padx=(0, 10))
        self._hist_search_var = tk.StringVar()
        search_entry = tk.Entry(search_card, textvariable=self._hist_search_var, font=FONT_BODY, bg=ENTRY_BG, fg=ENTRY_FG, highlightbackground=ENTRY_BORDER, highlightthickness=1, relief="flat", width=28)
        search_entry.pack(side="left", padx=(0, 8), ipady=3)

        HoverButton(search_card, hover_bg=PRIMARY_HOVER, text="Search", font=FONT_BODY, bg=BTN_BG, fg=BTN_FG, relief="flat", padx=12, pady=4, cursor="hand2", command=self._history_search).pack(side="left", padx=4)
        HoverButton(search_card, hover_bg=BTN_SEC_HOVER, text="Show All", font=FONT_BODY, bg=BTN_SEC_BG, fg=BTN_SEC_FG, relief="flat", padx=10, pady=4, cursor="hand2", command=self._page_history).pack(side="left")

        self._history_list_container = ScrollableFrame(frame, bg=BG_MAIN)
        self._history_list_container.pack(fill="both", expand=True)

        records = self.planner.get_latest_plans(30)
        self._render_history_records(records)

    def _render_history_records(self, records):
        """Collapsible accordion-style history. ONE ROW PER DATE, all collapsed by default."""
        parent = self._history_list_container.inner
        for w in parent.winfo_children():
            w.destroy()

        if not records:
            card = tk.Frame(parent, bg=BG_CARD, highlightbackground=BORDER_COLOR,
                            highlightthickness=1, bd=0, padx=20, pady=30)
            card.pack(fill="x", pady=10)
            tk.Label(card, text="No history records found.", font=FONT_BODY,
                     fg=FG_MUTED, bg=BG_CARD).pack()
            return

        # Deduplicate: keep best record per date
        best_by_date = {}
        for rec in records:
            d = rec.get("date", "")
            if not d:
                continue
            existing = best_by_date.get(d)
            if existing is None:
                best_by_date[d] = rec
            else:
                if rec.get("status", "") == "finalized" and existing.get("status", "") != "finalized":
                    best_by_date[d] = rec
                elif len(rec.get("schedule", [])) > len(existing.get("schedule", [])):
                    best_by_date[d] = rec
                elif rec.get("finalized_at", "") > existing.get("finalized_at", ""):
                    best_by_date[d] = rec

        if not best_by_date:
            card = tk.Frame(parent, bg=BG_CARD, highlightbackground=BORDER_COLOR,
                            highlightthickness=1, bd=0, padx=20, pady=30)
            card.pack(fill="x", pady=10)
            tk.Label(card, text="No history records found.", font=FONT_BODY,
                     fg=FG_MUTED, bg=BG_CARD).pack()
            return

        sorted_dates = sorted(best_by_date.keys(), reverse=True)

        for rec_date in sorted_dates:
            record = best_by_date[rec_date]
            sched = record.get("schedule", [])
            audit_trail = record.get("audit_trail", [])
            is_edited = record.get("is_edited", False)
            finalized = record.get("finalized_at", record.get("created_at", ""))
            task_count = len([e for e in sched if e.get("type") != "break"])

            row_outer = tk.Frame(parent, bg=BG_CARD,
                                 highlightbackground=BORDER_COLOR, highlightthickness=1, bd=0)
            row_outer.pack(fill="x", pady=(0, 6))

            collapsed_hdr = tk.Frame(row_outer, bg=BG_CARD, padx=16, pady=10)
            collapsed_hdr.pack(fill="x")

            detail_frame = tk.Frame(row_outer, bg=BG_CARD, padx=16, pady=0)

            chev = tk.Label(collapsed_hdr, text="\u25b6", font=("Segoe UI", 9),
                            fg=FG_MUTED, bg=BG_CARD, cursor="hand2")
            chev.pack(side="left", padx=(0, 8))

            date_display = format_date_display(rec_date)
            date_lbl = tk.Label(collapsed_hdr, text=f"\ud83d\udcc5  {date_display}",
                                font=FONT_HEADING, fg=PRIMARY_BLUE, bg=BG_CARD, cursor="hand2")
            date_lbl.pack(side="left")

            chip_bg = "#dcfce7" if task_count > 0 else "#f1f5f9"
            chip_fg = "#166534" if task_count > 0 else FG_MUTED
            tk.Label(collapsed_hdr,
                     text=f"  {task_count} task{'s' if task_count != 1 else ''}  ",
                     font=("Segoe UI", 8, "bold"), fg=chip_fg, bg=chip_bg,
                     padx=4, pady=2).pack(side="left", padx=8)

            if is_edited:
                tk.Label(collapsed_hdr, text=" \u270e EDITED ",
                         font=("Segoe UI", 8, "bold"), fg="#92400e", bg="#fef3c7",
                         padx=4, pady=2).pack(side="left", padx=2)

            finalized_short = finalized[:10] if finalized else ""
            tk.Label(collapsed_hdr, text=f"Finalized {finalized_short}",
                     font=FONT_SMALL, fg=FG_MUTED, bg=BG_CARD).pack(side="right", padx=(0, 4))

            _state = {"expanded": False}

            def _make_toggle(chev_w, state_d, detail_f):
                def _toggle(event=None):
                    state_d["expanded"] = not state_d["expanded"]
                    if state_d["expanded"]:
                        detail_f.pack(fill="x", padx=0, pady=(0, 12))
                        chev_w.config(text="\u25bc")
                    else:
                        detail_f.pack_forget()
                        chev_w.config(text="\u25b6")
                return _toggle

            toggle_fn = _make_toggle(chev, _state, detail_frame)
            for widget in (collapsed_hdr, chev, date_lbl):
                widget.bind("<Button-1>", toggle_fn)

            sep = tk.Frame(detail_frame, bg=BORDER_COLOR, height=1)
            sep.pack(fill="x", pady=(0, 8))

            sched_frame = tk.Frame(detail_frame, bg=BG_CARD)
            sched_frame.pack(fill="x", pady=(4, 0))
            render_schedule(sched_frame, sched, bg=BG_CARD, compact=True)

            if audit_trail:
                audit_box = tk.Frame(detail_frame, bg="#fffbeb", padx=12, pady=8,
                                     highlightbackground="#fde68a", highlightthickness=1, bd=0)
                audit_box.pack(fill="x", pady=(8, 4))
                tk.Label(audit_box, text="\ud83d\udccb Historical Edit Audit Trail:",
                         font=("Segoe UI", 9, "bold"), fg="#92400e", bg="#fffbeb").pack(anchor="w")
                for a in audit_trail:
                    tk.Label(audit_box,
                             text=f"\u2022 [{a.get('edited_at')}] {a.get('task_title')} \u2014 \"{a.get('edit_reason')}\"",
                             font=FONT_SMALL, fg=FG_MAIN, bg="#fffbeb",
                             wraplength=700, justify="left").pack(anchor="w")

            edit_btn_row = tk.Frame(detail_frame, bg=BG_CARD)
            edit_btn_row.pack(fill="x", pady=(6, 4))

            def _open_historical_edit(pdate=rec_date, r_dict=record):
                if not messagebox.askyesno(
                    "Historical Edit Confirmation",
                    "You are about to modify a completed historical record.\n\n"
                    "This will create an immutable audit trail entry.\n\n"
                    "Do you want to continue?",
                    parent=self,
                ):
                    return

                dlg = tk.Toplevel(self)
                dlg.title(f"Controlled Historical Edit \u2013 {pdate}")
                dlg.geometry("440x360")
                dlg.configure(bg=BG_MAIN)

                tk.Label(dlg, text=f"Edit Historical Record for {pdate}",
                         font=FONT_HEADING, fg=FG_MAIN, bg=BG_MAIN).pack(pady=10)

                f = tk.Frame(dlg, bg=BG_MAIN, padx=20)
                f.pack(fill="both", expand=True)

                task_options = [e.get("title", f"Task {i}") for i, e in enumerate(r_dict.get("schedule", []))]
                if not task_options:
                    task_options = ["(No tasks)"]

                tk.Label(f, text="Select Task:", font=FONT_SMALL, fg=FG_MAIN, bg=BG_MAIN).pack(anchor="w")
                task_choice_var = tk.StringVar(value=task_options[0])
                ttk.Combobox(f, textvariable=task_choice_var, values=task_options, state="readonly", width=34).pack(fill="x", pady=4)

                tk.Label(f, text="New Status:", font=FONT_SMALL, fg=FG_MAIN, bg=BG_MAIN).pack(anchor="w", pady=(6, 0))
                status_var = tk.StringVar(value="completed")
                ttk.Combobox(f, textvariable=status_var, values=["completed", "not_completed", "pending"], state="readonly", width=34).pack(fill="x", pady=4)

                tk.Label(f, text="Mandatory Edit Reason / Note (*REQUIRED):",
                         font=("Segoe UI", 9, "bold"), fg="#991b1b", bg=BG_MAIN).pack(anchor="w", pady=(8, 0))
                note_var = tk.StringVar()
                n_ent = tk.Entry(f, textvariable=note_var, font=FONT_BODY, bg=ENTRY_BG, fg=ENTRY_FG,
                                 relief="flat", highlightbackground=ENTRY_BORDER, highlightthickness=1)
                n_ent.pack(fill="x", ipady=4, pady=4)

                def _save_hist_edit():
                    reason = note_var.get().strip()
                    if not reason:
                        messagebox.showerror("Validation Error",
                                             "A non-empty note is MANDATORY for historical edits.", parent=dlg)
                        return
                    t_name = task_choice_var.get()
                    st = status_var.get()
                    try:
                        self.planner.edit_historical_record(
                            plan_date=pdate, task_id=t_name,
                            changes={"status": st}, mandatory_note=reason)
                        messagebox.showinfo("Historical Edit Saved",
                                            "Historical record updated and audit trail preserved.", parent=dlg)
                        dlg.destroy()
                        self._page_history()
                    except Exception as err:
                        messagebox.showerror("Error", str(err), parent=dlg)

                HoverButton(dlg, hover_bg=PRIMARY_HOVER, text=" Confirm & Save Audit Record ",
                            font=FONT_SUBHEAD, bg=BTN_BG, fg=BTN_FG, relief="flat",
                            padx=14, pady=6, cursor="hand2", command=_save_hist_edit).pack(pady=12)

            HoverButton(edit_btn_row, hover_bg=BTN_SEC_HOVER,
                        text=" \u270e Edit Historical Task ", font=FONT_SMALL,
                        bg=BTN_SEC_BG, fg=BTN_SEC_FG, relief="flat",
                        padx=8, pady=3, cursor="hand2",
                        command=_open_historical_edit).pack(side="right")


    def _history_search(self):
        query = self._hist_search_var.get().strip()
        if not query:
            self._page_history()
            return
        results = self.planner.search_history(query)
        self._render_history_records(results)

    # ========================================================
    # PAGE: TASKS (PERSISTENT TASK STORAGE)
    # ========================================================

    def _page_tasks(self):
        self._clear_content_frame()
        frame = tk.Frame(self.content, bg=BG_MAIN)
        frame.pack(fill="both", expand=True, padx=36, pady=28)

        tk.Label(frame, text="Persistent Tasks ✅", font=FONT_TITLE, fg=FG_MAIN, bg=BG_MAIN).pack(anchor="w")
        tk.Label(frame, text="All parsed and manually added tasks across your schedule.", font=FONT_SMALL, fg=FG_MUTED, bg=BG_MAIN).pack(anchor="w", pady=(2, 14))

        tasks = self.planner.load_tasks()
        scroll = ScrollableFrame(frame, bg=BG_MAIN)
        scroll.pack(fill="both", expand=True)

        if not tasks:
            card = tk.Frame(scroll.inner, bg=BG_CARD, highlightbackground=BORDER_COLOR, highlightthickness=1, bd=0, padx=20, pady=30)
            card.pack(fill="x", pady=10)
            tk.Label(card, text="No persistent tasks found.", font=FONT_BODY, fg=FG_MUTED, bg=BG_CARD).pack()
            return

        for t in reversed(tasks):
            row = tk.Frame(scroll.inner, bg=BG_CARD, highlightbackground=BORDER_COLOR, highlightthickness=1, bd=0, padx=14, pady=10)
            row.pack(fill="x", pady=4)

            icon = get_icon_for_title(t.get("title", ""))
            tk.Label(row, text=f"{icon} {t.get('title', 'Untitled Task')}", font=FONT_SUBHEAD, fg=FG_MAIN, bg=BG_CARD).pack(side="left")

            st = t.get("status", "pending")
            if st in BADGE_STYLES:
                s_bg, s_fg = BADGE_STYLES[st]
                tk.Label(row, text=f" {st.upper()} ", font=("Segoe UI", 8, "bold"), fg=s_fg, bg=s_bg, padx=6, pady=2).pack(side="right", padx=6)

            tk.Label(row, text=f"Duration: {t.get('duration', 60)} min", font=FONT_SMALL, fg=FG_MUTED, bg=BG_CARD).pack(side="right", padx=6)

    # ========================================================
    # PAGE: ROUTINES (ROUTINE PERIODS + MON-SUN MAPS + GLOBAL ROUTINES)
    # ========================================================

    def _page_routines(self):
        self._clear_content_frame()
        frame = tk.Frame(self.content, bg=BG_MAIN)
        frame.pack(fill="both", expand=True, padx=36, pady=28)

        top_row = tk.Frame(frame, bg=BG_MAIN)
        top_row.pack(fill="x", pady=(0, 6))

        tk.Label(top_row, text="Routine Periods & Habit System 🔄", font=FONT_TITLE, fg=FG_MAIN, bg=BG_MAIN).pack(side="left")

        HoverButton(
            top_row, hover_bg=PRIMARY_HOVER,
            text="  + Create Routine Period  ",
            font=FONT_SUBHEAD, bg=BTN_BG, fg=BTN_FG,
            relief="flat", padx=14, pady=6, cursor="hand2",
            command=self._create_routine_period_wizard,
        ).pack(side="right")

        tk.Label(
            frame,
            text="Define date-bounded routine periods with common task libraries and independent Monday–Sunday daily overrides.",
            font=FONT_SMALL, fg=FG_MUTED, bg=BG_MAIN,
        ).pack(anchor="w", pady=(0, 14))

        scroll = ScrollableFrame(frame, bg=BG_MAIN)
        scroll.pack(fill="both", expand=True)
        body = scroll.inner

        # --- Section 1: Routine Periods ---
        tk.Label(body, text="📅 Active Routine Periods", font=FONT_HEADING, fg=FG_MAIN, bg=BG_MAIN).pack(anchor="w", pady=(0, 8))

        periods = self.planner.load_routine_periods()
        if not periods:
            c = tk.Frame(body, bg=BG_CARD, highlightbackground=BORDER_COLOR, highlightthickness=1, bd=0, padx=16, pady=16)
            c.pack(fill="x", pady=(0, 14))
            tk.Label(c, text="No custom routine periods defined yet. Click '+ Create Routine Period' above to define your semester or work routine.", font=FONT_BODY, fg=FG_MUTED, bg=BG_CARD).pack()
        else:
            for p in periods:
                self._render_routine_period_card(body, p)

        ttk.Separator(body, orient="horizontal").pack(fill="x", pady=16)

        # --- Section 2: Legacy / Global Default Routines ---
        leg_row = tk.Frame(body, bg=BG_MAIN)
        leg_row.pack(fill="x", pady=(0, 8))

        tk.Label(leg_row, text="🔁 Global Recurring Daily Routines", font=FONT_HEADING, fg=FG_MAIN, bg=BG_MAIN).pack(side="left")

        HoverButton(
            leg_row, hover_bg=BTN_SEC_HOVER,
            text=" + Add Global Routine ",
            font=FONT_SMALL, bg=BTN_SEC_BG, fg=BTN_SEC_FG,
            relief="flat", padx=10, pady=3, cursor="hand2",
            command=self._add_legacy_routine_dialog,
        ).pack(side="right")

        legacy_routines = self.planner.load_routines()
        for r in legacy_routines:
            self._render_legacy_routine_row(body, r)

    def _render_routine_period_card(self, parent, p):
        card = tk.Frame(parent, bg=BG_CARD, highlightbackground=BORDER_COLOR, highlightthickness=1, bd=0, padx=16, pady=14)
        card.pack(fill="x", pady=6)

        hdr = tk.Frame(card, bg=BG_CARD)
        hdr.pack(fill="x")

        tk.Label(hdr, text=f"🗓️ {p.get('name')}", font=FONT_HEADING, fg=PRIMARY_BLUE, bg=BG_CARD).pack(side="left")
        tk.Label(hdr, text=f" ({p.get('start_date')} → {p.get('end_date')})", font=FONT_SUBHEAD, fg=FG_MUTED, bg=BG_CARD).pack(side="left")

        pid = p.get("period_id")

        def _delete_p(period_id=pid):
            if messagebox.askyesno("Delete Routine Period", "Are you sure you want to delete this routine period?", parent=self):
                self.planner.delete_routine_period(period_id)
                self._page_routines()

        HoverButton(hdr, hover_bg=BTN_DANGER_HOVER, text=" Delete Period ", font=FONT_SMALL, bg=BTN_DANGER_BG, fg=BTN_DANGER_FG, relief="flat", padx=8, pady=2, cursor="hand2", command=_delete_p).pack(side="right")

        # Mon-Sun Summary Grid
        days_box = tk.Frame(card, bg=BG_PANEL, padx=10, pady=8, highlightbackground=BORDER_COLOR, highlightthickness=1, bd=0)
        days_box.pack(fill="x", pady=(10, 0))

        days_cfg = p.get("days_config", {})
        for day in DAYS_OF_WEEK:
            items = [it.get("name") for it in days_cfg.get(day, []) if it.get("enabled", True)]
            summary_str = ", ".join(items) if items else "No routines"
            d_row = tk.Frame(days_box, bg=BG_PANEL)
            d_row.pack(fill="x", pady=1)
            tk.Label(d_row, text=f"{day[:3]}:", font=("Segoe UI", 9, "bold"), fg=FG_MAIN, bg=BG_PANEL, width=5, anchor="w").pack(side="left")
            tk.Label(d_row, text=summary_str, font=FONT_SMALL, fg=FG_MUTED, bg=BG_PANEL).pack(side="left")

    def _render_legacy_routine_row(self, parent, r):
        """Renders global routine card with INLINE EDITING support."""
        row = tk.Frame(parent, bg=BG_CARD, highlightbackground=BORDER_COLOR, highlightthickness=1, bd=0, pady=10, padx=14)
        row.pack(fill="x", pady=4)
        self._draw_legacy_routine_row(row, r, mode="normal")

    def _draw_legacy_routine_row(self, row, r, mode="normal"):
        for w in row.winfo_children():
            w.destroy()

        name = r.get("name") or r.get("title", "Routine")
        start = r.get("start") or r.get("start_time", "00:00")
        end = r.get("end") or r.get("end_time", "00:00")
        active = r.get("enabled", r.get("active", True))
        rid = r.get("routine_id") or name
        icon = get_icon_for_title(name, etype="routine")

        if mode == "normal":
            tk.Label(row, text=f"{icon} {name}", font=FONT_SUBHEAD, fg=FG_MAIN, bg=BG_CARD).pack(side="left")
            tk.Label(row, text=f"  🕒 {format_12h(start)} – {format_12h(end)}", font=FONT_BODY, fg=FG_MUTED, bg=BG_CARD).pack(side="left")

            status_txt = "Enabled" if active else "Disabled"
            status_bg = "#dcfce7" if active else "#fee2e2"
            status_fg = "#166534" if active else "#991b1b"

            tk.Label(row, text=f" {status_txt} ", font=("Segoe UI", 8, "bold"), fg=status_fg, bg=status_bg, padx=6, pady=2).pack(side="right", padx=6)

            def _del_rout():
                if messagebox.askyesno("Delete Routine", f"Are you sure you want to delete '{name}'?", parent=self):
                    self.planner.data_manager.delete_routine(rid)
                    self._page_routines()

            HoverButton(row, hover_bg=BTN_DANGER_HOVER, text=" 🗑 Delete ", font=FONT_SMALL, bg=BTN_DANGER_BG, fg=BTN_DANGER_FG, relief="flat", padx=6, pady=2, cursor="hand2", command=_del_rout).pack(side="right", padx=(4, 0))

            HoverButton(row, hover_bg=BTN_SEC_HOVER, text=" ✎ Edit ", font=FONT_SMALL, bg=BTN_SEC_BG, fg=BTN_SEC_FG, relief="flat", padx=8, pady=2, cursor="hand2", command=lambda: self._draw_legacy_routine_row(row, r, mode="edit")).pack(side="right", padx=(4, 0))

            def _tog(routine_id=rid):
                self.planner.data_manager.toggle_routine_status(routine_id)
                self._page_routines()

            HoverButton(row, hover_bg=BTN_SEC_HOVER, text=" Toggle ", font=FONT_SMALL, bg=BTN_SEC_BG, fg=BTN_SEC_FG, relief="flat", padx=8, pady=2, cursor="hand2", command=_tog).pack(side="right")

        elif mode == "edit":
            tk.Label(row, text="Name:", font=FONT_SMALL, fg=FG_MAIN, bg=BG_CARD).pack(side="left")
            n_var = tk.StringVar(value=name)
            tk.Entry(row, textvariable=n_var, font=FONT_SMALL, width=18).pack(side="left", padx=4)

            tk.Label(row, text="Start:", font=FONT_SMALL, fg=FG_MAIN, bg=BG_CARD).pack(side="left", padx=(6, 0))
            s_var = tk.StringVar(value=start)
            tk.Entry(row, textvariable=s_var, font=FONT_SMALL, width=8).pack(side="left", padx=4)

            tk.Label(row, text="End:", font=FONT_SMALL, fg=FG_MAIN, bg=BG_CARD).pack(side="left", padx=(6, 0))
            e_var = tk.StringVar(value=end)
            tk.Entry(row, textvariable=e_var, font=FONT_SMALL, width=8).pack(side="left", padx=4)

            def _save_changes():
                new_n = n_var.get().strip()
                new_s = s_var.get().strip()
                new_e = e_var.get().strip()
                if not new_n:
                    messagebox.showwarning("Validation", "Name cannot be empty.", parent=self)
                    return
                updates = {
                    "name": new_n,
                    "title": new_n,
                    "start_time": new_s,
                    "start": new_s,
                    "end_time": new_e,
                    "end": new_e,
                }
                self.planner.data_manager.update_routine(rid, updates)
                r.update(updates)
                self._draw_legacy_routine_row(row, r, mode="normal")

            def _cancel():
                self._draw_legacy_routine_row(row, r, mode="normal")

            HoverButton(row, hover_bg=PRIMARY_HOVER, text=" 💾 Save ", font=FONT_SMALL, bg=BTN_BG, fg=BTN_FG, relief="flat", padx=8, pady=2, cursor="hand2", command=_save_changes).pack(side="left", padx=6)
            HoverButton(row, hover_bg=BTN_SEC_HOVER, text=" Cancel ", font=FONT_SMALL, bg=BTN_SEC_BG, fg=BTN_SEC_FG, relief="flat", padx=6, pady=2, cursor="hand2", command=_cancel).pack(side="left")

    def _create_routine_period_wizard(self):
        """Wizard to configure Routine Period with clean step layout and labeled inputs."""
        dlg = tk.Toplevel(self)
        dlg.title("Create Routine Period")
        dlg.geometry("680x740")
        dlg.configure(bg=BG_MAIN)

        tk.Label(dlg, text="Routine Period Configuration Wizard", font=FONT_TITLE, fg=FG_MAIN, bg=BG_MAIN).pack(pady=12)

        scroll = ScrollableFrame(dlg, bg=BG_MAIN)
        scroll.pack(fill="both", expand=True, padx=20, pady=6)
        f = scroll.inner

        # Step 0: Period Info & Date Range
        p_card = tk.Frame(f, bg=BG_CARD, padx=16, pady=14, highlightbackground=BORDER_COLOR, highlightthickness=1, bd=0)
        p_card.pack(fill="x", pady=6)

        tk.Label(p_card, text="Step 0: Period Details & Date Range", font=FONT_HEADING, fg=PRIMARY_BLUE, bg=BG_CARD).pack(anchor="w", pady=(0, 6))

        tk.Label(p_card, text="Period Name:", font=FONT_SMALL, fg=FG_MAIN, bg=BG_CARD).pack(anchor="w")
        name_var = tk.StringVar(value="Fall Semester 2026")
        tk.Entry(p_card, textvariable=name_var, font=FONT_BODY, width=36).pack(fill="x", pady=2)

        d_row = tk.Frame(p_card, bg=BG_CARD)
        d_row.pack(fill="x", pady=6)
        tk.Label(d_row, text="From Date (YYYY-MM-DD):", font=FONT_SMALL, fg=FG_MAIN, bg=BG_CARD).grid(row=0, column=0, sticky="w")
        tk.Label(d_row, text="To Date (YYYY-MM-DD):", font=FONT_SMALL, fg=FG_MAIN, bg=BG_CARD).grid(row=0, column=1, sticky="w", padx=12)

        s_date_var = tk.StringVar(value=today_str())
        e_date_var = tk.StringVar(value=(date.today() + timedelta(days=30)).isoformat())
        tk.Entry(d_row, textvariable=s_date_var, font=FONT_BODY, width=16).grid(row=1, column=0, sticky="w", pady=2)
        tk.Entry(d_row, textvariable=e_date_var, font=FONT_BODY, width=16).grid(row=1, column=1, sticky="w", padx=12, pady=2)

        # Step 1: Common Routine Tasks Library (POLISHED LABELED INPUTS)
        lib_card = tk.Frame(f, bg=BG_CARD, padx=16, pady=14, highlightbackground=BORDER_COLOR, highlightthickness=1, bd=0)
        lib_card.pack(fill="x", pady=6)

        tk.Label(lib_card, text="Step 1: Common Routine Tasks Library", font=FONT_HEADING, fg=PRIMARY_BLUE, bg=BG_CARD).pack(anchor="w", pady=(0, 4))
        tk.Label(lib_card, text="Define common reusable tasks that can be assigned across weekdays.", font=FONT_SMALL, fg=FG_MUTED, bg=BG_CARD).pack(anchor="w", pady=(0, 8))

        common_tasks = [
            {"name": "Exercise", "default_time": "06:00", "duration": 60, "category": "Health"},
            {"name": "Breakfast", "default_time": "07:30", "duration": 30, "category": "Meal"},
            {"name": "College", "default_time": "09:00", "duration": 240, "category": "Education"},
            {"name": "Lunch", "default_time": "13:00", "duration": 60, "category": "Meal"},
            {"name": "Study", "default_time": "20:00", "duration": 120, "category": "Education"},
        ]

        tasks_list_frame = tk.Frame(lib_card, bg=BG_CARD)
        tasks_list_frame.pack(fill="x", pady=4)

        def _refresh_lib_tasks():
            for w in tasks_list_frame.winfo_children():
                w.destroy()
            for idx, ct in enumerate(common_tasks):
                row = tk.Frame(tasks_list_frame, bg=PRIMARY_LIGHT, padx=8, pady=4, highlightbackground=BORDER_COLOR, highlightthickness=1, bd=0)
                row.pack(fill="x", pady=2)
                tk.Label(row, text=f"• {ct['name']} @ {ct['default_time']} ({ct['duration']} min)", font=FONT_SUBHEAD, fg=FG_MAIN, bg=PRIMARY_LIGHT).pack(side="left")
                def _del_ct(i=idx):
                    common_tasks.pop(i)
                    _refresh_lib_tasks()
                    _refresh_days_config()
                HoverButton(row, hover_bg="#fecaca", text="✕", font=FONT_SMALL, bg=BTN_DANGER_BG, fg=BTN_DANGER_FG, relief="flat", padx=6, pady=1, cursor="hand2", command=_del_ct).pack(side="right")

        _refresh_lib_tasks()

        # Add new common task with explicit form layout
        add_form = tk.Frame(lib_card, bg=BG_CARD)
        add_form.pack(fill="x", pady=(8, 4))

        tk.Label(add_form, text="Task Name:", font=FONT_SMALL, fg=FG_MAIN, bg=BG_CARD).grid(row=0, column=0, sticky="w")
        tk.Label(add_form, text="Start Time (HH:MM):", font=FONT_SMALL, fg=FG_MAIN, bg=BG_CARD).grid(row=0, column=1, sticky="w", padx=8)
        tk.Label(add_form, text="Duration (min):", font=FONT_SMALL, fg=FG_MAIN, bg=BG_CARD).grid(row=0, column=2, sticky="w", padx=8)

        ct_n_var = tk.StringVar()
        ct_t_var = tk.StringVar(value="08:00")
        ct_d_var = tk.StringVar(value="60")

        tk.Entry(add_form, textvariable=ct_n_var, font=FONT_BODY, width=20).grid(row=1, column=0, sticky="w", pady=2)
        tk.Entry(add_form, textvariable=ct_t_var, font=FONT_BODY, width=12).grid(row=1, column=1, sticky="w", padx=8, pady=2)
        tk.Entry(add_form, textvariable=ct_d_var, font=FONT_BODY, width=10).grid(row=1, column=2, sticky="w", padx=8, pady=2)

        def _add_ct():
            n = ct_n_var.get().strip()
            if not n:
                return
            common_tasks.append({
                "name": n,
                "default_time": ct_t_var.get().strip() or "08:00",
                "duration": int(ct_d_var.get().strip() or "60"),
                "category": "General",
            })
            ct_n_var.set("")
            _refresh_lib_tasks()
            _refresh_days_config()

        HoverButton(add_form, hover_bg=PRIMARY_HOVER, text=" + Add to Library ", font=FONT_SMALL, bg=BTN_BG, fg=BTN_FG, relief="flat", padx=10, pady=3, cursor="hand2", command=_add_ct).grid(row=1, column=3, sticky="w", padx=8, pady=2)

        # Step 2: Monday–Sunday Day-by-Day Configuration
        days_card = tk.Frame(f, bg=BG_CARD, padx=16, pady=14, highlightbackground=BORDER_COLOR, highlightthickness=1, bd=0)
        days_card.pack(fill="x", pady=6)

        tk.Label(days_card, text="Step 2: Monday – Sunday Configurations", font=FONT_HEADING, fg=PRIMARY_BLUE, bg=BG_CARD).pack(anchor="w", pady=(0, 4))
        tk.Label(days_card, text="Configure each day. Modifying a time on Monday overrides Monday without altering other days.", font=FONT_SMALL, fg=FG_MUTED, bg=BG_CARD).pack(anchor="w", pady=(0, 8))

        days_data = {
            day: [dict(ct) for ct in common_tasks]
            for day in DAYS_OF_WEEK
        }

        day_notebook = ttk.Notebook(days_card)
        day_notebook.pack(fill="both", expand=True, pady=4)

        day_frames = {}
        for day in DAYS_OF_WEEK:
            df = tk.Frame(day_notebook, bg=BG_MAIN, padx=10, pady=8)
            day_notebook.add(df, text=f" {day[:3]} ")
            day_frames[day] = df

        def _refresh_days_config():
            for day, df in day_frames.items():
                for w in df.winfo_children():
                    w.destroy()

                tk.Label(df, text=f"{day} Routines", font=FONT_SUBHEAD, fg=PRIMARY_BLUE, bg=BG_MAIN).pack(anchor="w", pady=(0, 4))

                items = days_data.get(day, [])
                for idx, item in enumerate(items):
                    row = tk.Frame(df, bg=BG_CARD, padx=8, pady=4, highlightbackground=BORDER_COLOR, highlightthickness=1, bd=0)
                    row.pack(fill="x", pady=2)

                    en_var = tk.BooleanVar(value=item.get("enabled", True))
                    def _toggle_en(i=idx, v=en_var, d=day):
                        days_data[d][i]["enabled"] = v.get()
                    tk.Checkbutton(row, text=item.get("name"), variable=en_var, font=FONT_SUBHEAD, bg=BG_CARD, command=_toggle_en).pack(side="left")

                    tk.Label(row, text="Time:", font=FONT_SMALL, fg=FG_MUTED, bg=BG_CARD).pack(side="left", padx=(10, 2))
                    t_var = tk.StringVar(value=item.get("default_time") or item.get("time", "08:00"))
                    def _update_t(i=idx, v=t_var, d=day):
                        days_data[d][i]["time"] = v.get()
                        days_data[d][i]["is_override"] = True
                    t_ent = tk.Entry(row, textvariable=t_var, font=FONT_SMALL, width=8)
                    t_ent.pack(side="left", padx=2)
                    t_ent.bind("<FocusOut>", lambda e, i=idx, v=t_var, d=day: _update_t(i, v, d))

                    tk.Label(row, text="Dur:", font=FONT_SMALL, fg=FG_MUTED, bg=BG_CARD).pack(side="left", padx=(6, 2))
                    dur_var = tk.StringVar(value=str(item.get("duration", 60)))
                    def _update_dur(i=idx, v=dur_var, d=day):
                        try:
                            days_data[d][i]["duration"] = int(v.get())
                        except ValueError:
                            pass
                    d_ent = tk.Entry(row, textvariable=dur_var, font=FONT_SMALL, width=5)
                    d_ent.pack(side="left", padx=2)
                    d_ent.bind("<FocusOut>", lambda e, i=idx, v=dur_var, d=day: _update_dur(i, v, d))

                    def _remove_from_day(i=idx, d=day):
                        days_data[d].pop(i)
                        _refresh_days_config()
                    HoverButton(row, hover_bg="#fecaca", text="✕", font=FONT_SMALL, bg=BTN_DANGER_BG, fg=BTN_DANGER_FG, relief="flat", padx=4, pady=1, cursor="hand2", command=_remove_from_day).pack(side="right")

                # Add new day-specific routine
                add_day_row = tk.Frame(df, bg=BG_MAIN)
                add_day_row.pack(fill="x", pady=6)
                new_n_var = tk.StringVar()
                new_t_var = tk.StringVar(value="08:00")
                tk.Entry(add_day_row, textvariable=new_n_var, font=FONT_SMALL, width=14).pack(side="left", padx=2)
                tk.Entry(add_day_row, textvariable=new_t_var, font=FONT_SMALL, width=8).pack(side="left", padx=2)
                def _add_to_day(d=day, nv=new_n_var, tv=new_t_var):
                    name_str = nv.get().strip()
                    if name_str:
                        days_data[d].append({
                            "name": name_str,
                            "time": tv.get().strip() or "08:00",
                            "duration": 60,
                            "is_override": True,
                            "enabled": True,
                        })
                        nv.set("")
                        _refresh_days_config()
                HoverButton(add_day_row, hover_bg=PRIMARY_HOVER, text="+ Add to this day", font=FONT_SMALL, bg=BTN_BG, fg=BTN_FG, relief="flat", padx=6, pady=2, cursor="hand2", command=_add_to_day).pack(side="left", padx=4)

        _refresh_days_config()

        # Step 3: Save Routine Period
        def _save_period():
            name = name_var.get().strip()
            s_date = s_date_var.get().strip()
            e_date = e_date_var.get().strip()

            valid, err = validate_date_range(s_date, e_date)
            if not valid:
                messagebox.showerror("Date Validation Error", err, parent=dlg)
                return

            formatted_days_config = {}
            for day in DAYS_OF_WEEK:
                formatted_days_config[day] = [
                    {
                        "name": it.get("name"),
                        "time": it.get("time") or it.get("default_time", "08:00"),
                        "duration": it.get("duration", 60),
                        "category": it.get("category", "General"),
                        "is_override": it.get("is_override", False),
                        "enabled": it.get("enabled", True),
                    }
                    for it in days_data.get(day, [])
                ]

            period_data = {
                "name": name,
                "start_date": s_date,
                "end_date": e_date,
                "common_tasks": common_tasks,
                "days_config": formatted_days_config,
                "enabled": True,
            }

            try:
                self.planner.save_routine_period(period_data)
                messagebox.showinfo("Success", f"Routine Period '{name}' saved successfully!", parent=dlg)
                dlg.destroy()
                self._page_routines()
            except Exception as e:
                messagebox.showerror("Error Saving Period", str(e), parent=dlg)

        HoverButton(
            dlg, hover_bg=BTN_SUCCESS_HOVER,
            text="  💾  Save Routine Period  ",
            font=FONT_HEADING, bg=BTN_SUCCESS_BG, fg="#ffffff",
            relief="flat", padx=20, pady=10, cursor="hand2",
            command=_save_period,
        ).pack(pady=12)

    def _add_legacy_routine_dialog(self):
        dlg = tk.Toplevel(self)
        dlg.title("Add Global Recurring Routine")
        dlg.geometry("400x320")
        dlg.configure(bg=BG_MAIN)

        tk.Label(dlg, text="Add Global Recurring Routine", font=FONT_HEADING, fg=FG_MAIN, bg=BG_MAIN).pack(pady=10)
        f = tk.Frame(dlg, bg=BG_MAIN, padx=20)
        f.pack(fill="both")

        tk.Label(f, text="Name:", font=FONT_SMALL, fg=FG_MAIN, bg=BG_MAIN).grid(row=0, column=0, sticky="w")
        n_var = tk.StringVar()
        tk.Entry(f, textvariable=n_var, font=FONT_BODY, width=22).grid(row=0, column=1, pady=4)

        tk.Label(f, text="Start (HH:MM):", font=FONT_SMALL, fg=FG_MAIN, bg=BG_MAIN).grid(row=1, column=0, sticky="w")
        st_var = tk.StringVar(value="08:00")
        tk.Entry(f, textvariable=st_var, font=FONT_BODY, width=22).grid(row=1, column=1, pady=4)

        tk.Label(f, text="End (HH:MM):", font=FONT_SMALL, fg=FG_MAIN, bg=BG_MAIN).grid(row=2, column=0, sticky="w")
        et_var = tk.StringVar(value="09:00")
        tk.Entry(f, textvariable=et_var, font=FONT_BODY, width=22).grid(row=2, column=1, pady=4)

        def _save_leg():
            name = n_var.get().strip()
            if not name:
                return
            self.planner.data_manager.add_routine({
                "name": name,
                "title": name,
                "start_time": st_var.get().strip(),
                "start": st_var.get().strip(),
                "end_time": et_var.get().strip(),
                "end": et_var.get().strip(),
                "days": DAYS_OF_WEEK,
                "enabled": True,
            })
            dlg.destroy()
            self._page_routines()

        HoverButton(dlg, hover_bg=PRIMARY_HOVER, text="Save Routine", font=FONT_SUBHEAD, bg=BTN_BG, fg=BTN_FG, relief="flat", padx=12, pady=6, cursor="hand2", command=_save_leg).pack(pady=16)

    # ========================================================
    # PAGE: MEMORY (LEARNED PREFERENCES + FUTURE CONFIRMED PLANS)
    # ========================================================

    def _page_memory(self):
        self._clear_content_frame()
        self.planner.check_date_rollover()

        frame = tk.Frame(self.content, bg=BG_MAIN)
        frame.pack(fill="both", expand=True, padx=36, pady=28)

        tk.Label(frame, text="Memory & Future Plans 🧠", font=FONT_TITLE, fg=FG_MAIN, bg=BG_MAIN).pack(anchor="w")
        tk.Label(frame, text="DayWise clearly distinguishes long-term user memory/preferences from future confirmed plans.", font=FONT_SMALL, fg=FG_MUTED, bg=BG_MAIN).pack(anchor="w", pady=(2, 12))

        scroll = ScrollableFrame(frame, bg=BG_MAIN)
        scroll.pack(fill="both", expand=True)
        body = scroll.inner

        # --- Section 1: Future Confirmed Plans ---
        tk.Label(body, text="📅 Future Confirmed Plans", font=FONT_HEADING, fg=PRIMARY_BLUE, bg=BG_MAIN).pack(anchor="w", pady=(0, 8))

        future_plans = self.planner.get_all_future_plans()
        if not future_plans:
            c = tk.Frame(body, bg=BG_CARD, highlightbackground=BORDER_COLOR, highlightthickness=1, bd=0, padx=16, pady=16)
            c.pack(fill="x", pady=(0, 14))
            tk.Label(c, text="No future confirmed plans pending. When you plan a future date in 'Plan My Day' and click Confirm, it will appear here.", font=FONT_BODY, fg=FG_MUTED, bg=BG_CARD).pack()
        else:
            for f_date, f_plan in sorted(future_plans.items()):
                self._render_future_plan_card(body, f_date, f_plan)

        ttk.Separator(body, orient="horizontal").pack(fill="x", pady=16)

        # --- Section 2: Learned User Memory & Preferences ---
        tk.Label(body, text="💡 Learned Facts, Preferences & Sleep Schedule", font=FONT_HEADING, fg=FG_MAIN, bg=BG_MAIN).pack(anchor="w", pady=(0, 8))

        mem_data = self.planner.load_memory()
        for cat in ["preferences", "routines", "constraints", "sleep_schedule", "future_events"]:
            entries = mem_data.get(cat, [])
            if entries:
                cat_card = tk.Frame(body, bg=BG_CARD, highlightbackground=BORDER_COLOR, highlightthickness=1, bd=0, padx=14, pady=10)
                cat_card.pack(fill="x", pady=4)
                tk.Label(cat_card, text=f"Category: {cat.replace('_', ' ').capitalize()}", font=FONT_SUBHEAD, fg=PRIMARY_BLUE, bg=BG_CARD).pack(anchor="w", pady=(0, 4))
                for ent in entries:
                    tk.Label(cat_card, text=f"• {ent.get('text')}", font=FONT_BODY, fg=FG_MAIN, bg=BG_CARD).pack(anchor="w")

    def _render_future_plan_card(self, parent, plan_date, plan_dict):
        card = tk.Frame(parent, bg=BG_CARD, highlightbackground=BORDER_COLOR, highlightthickness=1, bd=0, padx=16, pady=14)
        card.pack(fill="x", pady=6)

        hdr = tk.Frame(card, bg=BG_CARD)
        hdr.pack(fill="x")

        tk.Label(hdr, text=f"📅 Confirmed for: {format_date_display(plan_date)}", font=FONT_HEADING, fg="#0369a1", bg=BG_CARD).pack(side="left")
        tk.Label(hdr, text=" FUTURE CONFIRMED ", font=("Segoe UI", 8, "bold"), fg="#0369a1", bg="#e0f2fe", padx=6, pady=2).pack(side="left", padx=8)

        def _cancel_fut(pd=plan_date):
            if messagebox.askyesno("Cancel Future Plan", f"Are you sure you want to cancel the confirmed plan for {pd}?", parent=self):
                self.planner.delete_future_plan(pd)
                self._page_memory()

        HoverButton(hdr, hover_bg="#fecaca", text=" Cancel Plan ", font=FONT_SMALL, bg=BTN_DANGER_BG, fg=BTN_DANGER_FG, relief="flat", padx=8, pady=2, cursor="hand2", command=_cancel_fut).pack(side="right")

        sched = plan_dict.get("schedule", [])
        tasks_str = ", ".join([e.get("title", "") for e in sched[:6]])
        if len(sched) > 6:
            tasks_str += f" (+{len(sched)-6} more)"

        tk.Label(card, text=f"Scheduled Tasks ({len(sched)}): {tasks_str}", font=FONT_BODY, fg=FG_MUTED, bg=BG_CARD).pack(anchor="w", pady=(6, 0))

    # ========================================================
    # PAGE: SEARCH
    # ========================================================

    def _page_search(self):
        self._clear_content_frame()
        frame = tk.Frame(self.content, bg=BG_MAIN)
        frame.pack(fill="both", expand=True, padx=36, pady=28)

        tk.Label(frame, text="Global Search 🔍", font=FONT_TITLE, fg=FG_MAIN, bg=BG_MAIN).pack(anchor="w")
        tk.Label(frame, text="Search across tasks, routines, future plans, active plans, and history records.", font=FONT_SMALL, fg=FG_MUTED, bg=BG_MAIN).pack(anchor="w", pady=(2, 12))

        search_card = tk.Frame(frame, bg=BG_CARD, highlightbackground=BORDER_COLOR, highlightthickness=1, bd=0, padx=14, pady=10)
        search_card.pack(fill="x", pady=(0, 14))

        self._global_search_var = tk.StringVar()
        s_ent = tk.Entry(search_card, textvariable=self._global_search_var, font=FONT_BODY, bg=ENTRY_BG, fg=ENTRY_FG, highlightbackground=ENTRY_BORDER, highlightthickness=1, relief="flat", width=34)
        s_ent.pack(side="left", padx=(0, 8), ipady=4)
        s_ent.bind("<Return>", lambda e: self._perform_global_search())

        HoverButton(search_card, hover_bg=PRIMARY_HOVER, text="Search Everything", font=FONT_BODY, bg=BTN_BG, fg=BTN_FG, relief="flat", padx=14, pady=4, cursor="hand2", command=self._perform_global_search).pack(side="left")

        self._search_results_container = ScrollableFrame(frame, bg=BG_MAIN)
        self._search_results_container.pack(fill="both", expand=True)

    def _perform_global_search(self):
        query = self._global_search_var.get().strip().lower()
        parent = self._search_results_container.inner
        for w in parent.winfo_children():
            w.destroy()

        if not query:
            return

        hist_results = self.planner.search_history(query)
        fut_plans = self.planner.get_all_future_plans()
        routines = self.planner.load_routines()
        tasks = self.planner.load_tasks()

        found_any = False

        if hist_results:
            found_any = True
            tk.Label(parent, text=f"📜 Historical Records ({len(hist_results)})", font=FONT_HEADING, fg=PRIMARY_BLUE, bg=BG_MAIN).pack(anchor="w", pady=(6, 4))
            for h in hist_results:
                c = tk.Frame(parent, bg=BG_CARD, highlightbackground=BORDER_COLOR, highlightthickness=1, bd=0, padx=12, pady=8)
                c.pack(fill="x", pady=2)
                tk.Label(c, text=f"📅 {h.get('date')}", font=FONT_SUBHEAD, fg=FG_MAIN, bg=BG_CARD).pack(side="left")
                tk.Label(c, text=f" – {len(h.get('schedule', []))} items", font=FONT_SMALL, fg=FG_MUTED, bg=BG_CARD).pack(side="left")

        matching_fut = {d: p for d, p in fut_plans.items() if query in d.lower() or any(query in e.get("title", "").lower() for e in p.get("schedule", []))}
        if matching_fut:
            found_any = True
            tk.Label(parent, text=f"📅 Future Confirmed Plans ({len(matching_fut)})", font=FONT_HEADING, fg="#0369a1", bg=BG_MAIN).pack(anchor="w", pady=(10, 4))
            for d, p in matching_fut.items():
                c = tk.Frame(parent, bg=BG_CARD, highlightbackground=BORDER_COLOR, highlightthickness=1, bd=0, padx=12, pady=8)
                c.pack(fill="x", pady=2)
                tk.Label(c, text=f"Future: {d}", font=FONT_SUBHEAD, fg="#0369a1", bg=BG_CARD).pack(side="left")

        matching_routines = [r for r in routines if query in (r.get("name") or r.get("title", "")).lower()]
        if matching_routines:
            found_any = True
            tk.Label(parent, text=f"🔄 Routines ({len(matching_routines)})", font=FONT_HEADING, fg=FG_MAIN, bg=BG_MAIN).pack(anchor="w", pady=(10, 4))
            for r in matching_routines:
                c = tk.Frame(parent, bg=BG_CARD, highlightbackground=BORDER_COLOR, highlightthickness=1, bd=0, padx=12, pady=8)
                c.pack(fill="x", pady=2)
                tk.Label(c, text=f"Routine: {r.get('name')}", font=FONT_SUBHEAD, fg=FG_MAIN, bg=BG_CARD).pack(side="left")

        if not found_any:
            c = tk.Frame(parent, bg=BG_CARD, highlightbackground=BORDER_COLOR, highlightthickness=1, bd=0, padx=20, pady=20)
            c.pack(fill="x", pady=10)
            tk.Label(c, text=f"No results found matching '{query}'.", font=FONT_BODY, fg=FG_MUTED, bg=BG_CARD).pack()


# ============================================================
# ENTRY POINT
# ============================================================

def launch_gui():
    app = DayWiseApp()
    app.mainloop()


if __name__ == "__main__":
    launch_gui()
