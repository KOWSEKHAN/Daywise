"""
ui/gui.py

DayWise Tkinter Desktop GUI - Rich Timeline & Dashboard Visual Theme

A clean, responsive, professional desktop daily planning application.
Rich visual timeline cards, emojis, pastel badges, and dashboard overview.
No third-party libraries – pure Python + Tkinter standard library.

Interactive Clarification System:
When the planner requires more information (e.g., college start/end times),
the Plan My Day page shows a focused clarification prompt instead of a schedule,
collecting the missing data before generating the final plan.
"""

import re
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, datetime

from core.planner import Planner
from core.scheduler import time_to_minutes, minutes_to_time
from utils.date_utils import format_date_display, today_str
from utils.text_utils import truncate


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
    # Priorities & Types
    "very high": ("#fee2e2", "#991b1b"),  # soft red
    "high":      ("#ffedd5", "#9a3412"),  # soft orange
    "normal":    ("#fef9c3", "#854d0e"),  # soft yellow
    "low":       ("#dcfce7", "#166534"),  # soft green
    "fixed":     ("#dbeafe", "#1e40af"),  # soft blue
    "event":     ("#dbeafe", "#1e40af"),  # soft blue
    "task":      ("#e0e7ff", "#3730a3"),  # soft indigo
    "routine":   ("#e0f2fe", "#0369a1"),  # soft cyan
    "break":     ("#f1f5f9", "#475569"),  # soft gray

    # Statuses
    "pending":   ("#ffedd5", "#9a3412"),  # soft orange
    "scheduled": ("#dbeafe", "#1e40af"),  # soft blue
    "completed": ("#dcfce7", "#166534"),  # soft green
    "cancelled": ("#fee2e2", "#991b1b"),  # soft red
}

# Node colors for visual timeline
TIMELINE_DOTS = ["🟢", "🔵", "🟣", "🟠", "🔴", "🟤", "⚪"]


# ============================================================
# EMOJI & SUBTITLE HELPERS
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
        dt = datetime.strptime(time_str, "%H:%M")
        return dt.strftime("%I:%M %p").lstrip("0")
    except Exception:
        return time_str


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
        self.config(bg=self._hover_bg)

    def _on_leave(self, _event):
        self.config(bg=self._default_bg)


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

        # Mouse-wheel scrolling
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(
            int(-1 * (e.delta / 120)), "units"
        ))


# ============================================================
# SCHEDULE TIMELINE CARD RENDERING WIDGET
# ============================================================

def render_schedule(parent, schedule, bg=BG_MAIN, compact=False):
    """
    Renders a schedule list into `parent` as a visual timeline with cards, emojis, and soft badges.
    Guarantees no duplicate visual rows.
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
            text="No schedule entries available for this day.",
            font=FONT_BODY,
            bg=BG_CARD,
            fg=FG_MUTED,
        ).pack()
        return

    # Filter out duplicate visual schedule items if any
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
        etype = str(entry.get("type", "task")).lower()
        priority = str(entry.get("priority", "")).lower()
        title_text = entry.get("title", "Task")
        icon = get_icon_for_title(title_text, etype=etype)
        desc_text = get_description_for_title(title_text, etype=etype)

        start_12 = format_12h(entry.get("start", "00:00"))
        end_12 = format_12h(entry.get("end", "00:00"))

        dot = TIMELINE_DOTS[idx % len(TIMELINE_DOTS)]

        row_frame = tk.Frame(timeline_container, bg=bg)
        row_frame.pack(fill="x", expand=True, pady=6)

        # Timeline Left Pillar: Dot + Connector Line + Time
        pillar = tk.Frame(row_frame, bg=bg, width=140)
        pillar.pack(side="left", fill="y", padx=(0, 8))

        dot_label = tk.Label(
            pillar, text=f"{dot} {start_12}",
            font=FONT_MONO, fg=PRIMARY_BLUE, bg=bg, anchor="w"
        )
        dot_label.pack(anchor="w")

        tk.Label(
            pillar, text=f"   – {end_12}",
            font=FONT_SMALL, fg=FG_MUTED, bg=bg, anchor="w"
        ).pack(anchor="w")

        # Timeline Card (Right)
        card = tk.Frame(
            row_frame, bg=BG_CARD,
            highlightbackground=BORDER_COLOR, highlightthickness=1,
            bd=0, pady=10, padx=14,
        )
        card.pack(side="left", fill="x", expand=True)

        # Card Top Row: Icon + Title + Badges
        top_line = tk.Frame(card, bg=BG_CARD)
        top_line.pack(fill="x")

        tk.Label(
            top_line, text=f"{icon} ",
            font=("Segoe UI", 12), bg=BG_CARD
        ).pack(side="left")

        tk.Label(
            top_line, text=title_text,
            font=FONT_SUBHEAD, fg=FG_MAIN, bg=BG_CARD,
            anchor="w"
        ).pack(side="left")

        if etype == "task":
            seg = entry.get("segment_number")
            tot = entry.get("total_segments")
            if seg and tot and tot > 1:
                tk.Label(
                    top_line, text=f" (Part {seg}/{tot})",
                    font=FONT_SMALL, fg=FG_MUTED, bg=BG_CARD,
                ).pack(side="left")

        # Badges (Right side of card)
        badges_box = tk.Frame(top_line, bg=BG_CARD)
        badges_box.pack(side="right")

        if priority and priority in BADGE_STYLES:
            p_bg, p_fg = BADGE_STYLES[priority]
            tk.Label(
                badges_box, text=f" {priority.upper()} ",
                font=("Segoe UI", 8, "bold"), fg=p_fg,
                bg=p_bg, padx=6, pady=2,
            ).pack(side="right", padx=(4, 0))

        badge_key = etype if etype in BADGE_STYLES else "task"
        b_bg, b_fg = BADGE_STYLES[badge_key]
        tk.Label(
            badges_box, text=f" {etype.upper()} ",
            font=("Segoe UI", 8, "bold"), fg=b_fg,
            bg=b_bg, padx=6, pady=2,
        ).pack(side="right")

        # Card Bottom Row: Secondary Description
        if not compact:
            tk.Label(
                card, text=desc_text,
                font=FONT_SMALL, fg=FG_MUTED, bg=BG_CARD,
                anchor="w"
            ).pack(anchor="w", pady=(4, 0))


# ============================================================
# MAIN APPLICATION WINDOW
# ============================================================

class DayWiseApp(tk.Tk):

    def __init__(self):
        super().__init__()

        self.planner = Planner()

        self.title("DayWise – Intelligent Daily Planning Dashboard")
        self.geometry("1380x840")
        self.minsize(980, 650)
        self.configure(bg=BG_MAIN)

        self._current_page = None

        # ---- Clarification state ----
        # These are set while waiting for user to answer clarification questions.
        self._clarification_active    = False
        self._clarification_question  = ""
        self._clarification_field     = ""
        self._clarification_title     = ""
        self._clarification_pending   = []   # parsed tasks preserved between rounds
        self._clarification_original  = ""   # original raw user input
        self._clarification_date      = ""   # plan date string

        self._build_layout()
        self._show_page("home")

    # --------------------------------------------------------
    # LAYOUT BUILDER
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
            footer,
            text=format_date_display(today_str()),
            font=FONT_SMALL, fg=FG_SIDEBAR, bg=BG_SIDEBAR,
            justify="left",
        ).pack(anchor="w")

    # --------------------------------------------------------
    # PAGE ROUTER
    # --------------------------------------------------------

    def _show_page(self, page_name):
        """Clear content area and render requested page."""

        # Switching away from plan page resets clarification state
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

        for widget in self.content.winfo_children():
            widget.destroy()

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
    # PAGE: HOME
    # ========================================================

    def _page_home(self):
        frame = tk.Frame(self.content, bg=BG_MAIN)
        frame.pack(fill="both", expand=True, padx=36, pady=28)

        tk.Label(
            frame, text="Welcome to DayWise",
            font=FONT_TITLE, fg=FG_MAIN, bg=BG_MAIN,
        ).pack(anchor="w")

        tk.Label(
            frame,
            text="Your intelligent daily planning companion.",
            font=FONT_BODY, fg=FG_MUTED, bg=BG_MAIN,
        ).pack(anchor="w", pady=(2, 18))

        # Quick Action Cards
        actions = [
            ("📅  Plan My Day",
             "Enter natural language tasks and get an intelligent schedule.",
             "plan"),
            ("📋  View Today's Plan",
             "See the schedule generated for today.",
             "today"),
            ("📜  History",
             "Browse and search past plans.",
             "history"),
            ("✅  Tasks",
             "View and manage saved tasks.",
             "tasks"),
        ]

        cards_row = tk.Frame(frame, bg=BG_MAIN)
        cards_row.pack(fill="x", pady=10)

        for i, (title, desc, page) in enumerate(actions):
            card = tk.Frame(
                cards_row, bg=BG_CARD,
                highlightbackground=BORDER_COLOR, highlightthickness=1,
                bd=0, padx=16, pady=16, cursor="hand2",
            )
            card.grid(row=0, column=i, padx=6, sticky="nsew")
            cards_row.columnconfigure(i, weight=1)

            tk.Label(
                card, text=title, font=FONT_SUBHEAD,
                fg=PRIMARY_BLUE, bg=BG_CARD,
            ).pack(anchor="w")

            tk.Label(
                card, text=desc, font=FONT_SMALL,
                fg=FG_MUTED, bg=BG_CARD,
                wraplength=190, justify="left",
            ).pack(anchor="w", pady=(6, 0))

            card.bind("<Button-1>", lambda e, p=page: self._show_page(p))
            for child in card.winfo_children():
                child.bind("<Button-1>", lambda e, p=page: self._show_page(p))

        # Latest schedule preview section
        tk.Label(
            frame, text="Latest Schedule Preview",
            font=FONT_HEADING, fg=FG_MAIN, bg=BG_MAIN,
        ).pack(anchor="w", pady=(24, 8))

        preview = ScrollableFrame(frame, bg=BG_MAIN)
        preview.pack(fill="both", expand=True)

        today_records = self.planner.get_today_plan()
        render_schedule(preview.inner, today_records, bg=BG_MAIN, compact=True)

    # ========================================================
    # PAGE: PLAN MY DAY
    # ========================================================

    def _page_plan(self):
        frame = tk.Frame(self.content, bg=BG_MAIN)
        frame.pack(fill="both", expand=True, padx=36, pady=28)

        tk.Label(
            frame, text="Plan My Day",
            font=FONT_TITLE, fg=FG_MAIN, bg=BG_MAIN,
        ).pack(anchor="w")

        tk.Label(
            frame,
            text="Type your tasks in natural language. Separate multiple tasks with commas or 'and'.",
            font=FONT_BODY, fg=FG_MUTED, bg=BG_MAIN,
        ).pack(anchor="w", pady=(2, 14))

        # ---- Input card ----
        input_card = tk.Frame(
            frame, bg=BG_CARD,
            highlightbackground=BORDER_COLOR, highlightthickness=1,
            bd=0, padx=16, pady=14,
        )
        input_card.pack(fill="x", pady=(0, 14))

        hint = 'Example: "I have college tomorrow. I want to exercise and have breakfast before college."'
        tk.Label(
            input_card, text=hint,
            font=FONT_SMALL, fg=FG_MUTED, bg=BG_CARD,
            wraplength=800, justify="left",
        ).pack(anchor="w", pady=(0, 8))

        self._input_text = tk.Text(
            input_card, height=4, width=80,
            font=FONT_BODY,
            bg=ENTRY_BG, fg=ENTRY_FG,
            highlightbackground=ENTRY_BORDER, highlightthickness=1,
            relief="flat", padx=10, pady=8,
            wrap="word",
        )
        self._input_text.pack(fill="x", pady=(0, 10))
        self._input_text.focus_set()

        date_row = tk.Frame(input_card, bg=BG_CARD)
        date_row.pack(anchor="w", pady=(0, 10))

        tk.Label(
            date_row, text="Plan for date (YYYY-MM-DD):",
            font=FONT_BODY, fg=FG_MUTED, bg=BG_CARD,
        ).pack(side="left", padx=(0, 8))

        self._plan_date_var = tk.StringVar(value=today_str())
        date_entry = tk.Entry(
            date_row, textvariable=self._plan_date_var,
            font=FONT_BODY, bg=ENTRY_BG, fg=ENTRY_FG,
            highlightbackground=ENTRY_BORDER, highlightthickness=1,
            relief="flat", width=14,
        )
        date_entry.pack(side="left")

        btn_row = tk.Frame(input_card, bg=BG_CARD)
        btn_row.pack(anchor="w")

        plan_btn = HoverButton(
            btn_row, hover_bg=PRIMARY_HOVER,
            text="  📅  Generate My Plan  ",
            font=FONT_SUBHEAD,
            bg=BTN_BG, fg=BTN_FG,
            relief="flat", padx=16, pady=8, cursor="hand2",
            command=self._run_plan,
        )
        plan_btn.pack(side="left", padx=(0, 10))

        clear_btn = HoverButton(
            btn_row, hover_bg=BTN_SEC_HOVER,
            text="  ✕  Clear  ",
            font=FONT_BODY,
            bg=BTN_SEC_BG, fg=BTN_SEC_FG,
            relief="flat", padx=10, pady=8, cursor="hand2",
            command=self._clear_plan_input,
        )
        clear_btn.pack(side="left")

        self._plan_status = tk.Label(
            frame, text="", font=FONT_BODY,
            fg="#166534", bg=BG_MAIN,
        )
        self._plan_status.pack(anchor="w", pady=(0, 6))

        # ---- Clarification Panel (hidden until needed) ----
        self._clarif_panel = tk.Frame(
            frame, bg="#fffbeb",
            highlightbackground="#fbbf24", highlightthickness=2,
            bd=0, padx=20, pady=18,
        )
        # Not packed initially — shown only when clarification is needed

        clarif_header = tk.Frame(self._clarif_panel, bg="#fffbeb")
        clarif_header.pack(fill="x", pady=(0, 8))

        tk.Label(
            clarif_header,
            text="🤔  DayWise needs a little more information",
            font=FONT_SUBHEAD, fg="#92400e", bg="#fffbeb",
        ).pack(side="left")

        self._clarif_question_label = tk.Label(
            self._clarif_panel,
            text="",
            font=FONT_BODY, fg=FG_MAIN, bg="#fffbeb",
            wraplength=700, justify="left",
        )
        self._clarif_question_label.pack(anchor="w", pady=(0, 10))

        self._clarif_answer_var = tk.StringVar()
        clarif_entry = tk.Entry(
            self._clarif_panel,
            textvariable=self._clarif_answer_var,
            font=("Segoe UI", 13),
            bg=ENTRY_BG, fg=ENTRY_FG,
            highlightbackground="#fbbf24", highlightthickness=2,
            relief="flat", width=28,
        )
        clarif_entry.pack(anchor="w", ipady=6, pady=(0, 10))
        clarif_entry.bind("<Return>", lambda e: self._submit_clarification())
        self._clarif_entry_widget = clarif_entry

        clarif_btn_row = tk.Frame(self._clarif_panel, bg="#fffbeb")
        clarif_btn_row.pack(anchor="w")

        HoverButton(
            clarif_btn_row, hover_bg=PRIMARY_HOVER,
            text="  Continue  ➜  ",
            font=FONT_SUBHEAD,
            bg=BTN_BG, fg=BTN_FG,
            relief="flat", padx=16, pady=8, cursor="hand2",
            command=self._submit_clarification,
        ).pack(side="left", padx=(0, 10))

        HoverButton(
            clarif_btn_row, hover_bg=BTN_SEC_HOVER,
            text="  Cancel  ",
            font=FONT_BODY,
            bg=BTN_SEC_BG, fg=BTN_SEC_FG,
            relief="flat", padx=10, pady=8, cursor="hand2",
            command=self._cancel_clarification,
        ).pack(side="left")

        # ---- Results section ----
        tk.Label(
            frame, text="Generated Schedule:",
            font=FONT_HEADING, fg=FG_MAIN, bg=BG_MAIN,
        ).pack(anchor="w", pady=(4, 6))

        result_frame = ScrollableFrame(frame, bg=BG_MAIN)
        result_frame.pack(fill="both", expand=True)
        self._plan_result_frame = result_frame.inner

        # If clarification was already active when we re-rendered the page
        if self._clarification_active:
            self._show_clarification_panel(
                self._clarification_question,
            )

    # --------------------------------------------------------
    # PLAN EXECUTION
    # --------------------------------------------------------

    def _clear_plan_input(self):
        self._input_text.delete("1.0", "end")
        self._cancel_clarification()

    def _run_plan(self):
        """Execute planning pipeline and display results or clarification prompt."""
        raw_input = self._input_text.get("1.0", "end").strip()
        plan_date = self._plan_date_var.get().strip() or today_str()

        if not raw_input:
            self._plan_status.config(
                text="⚠ Please enter at least one task.",
                fg="#9a3412",
            )
            return

        # Reset any previous clarification state
        self._cancel_clarification(silent=True)

        self._plan_status.config(
            text="⏳ Generating schedule...", fg=FG_MUTED
        )
        self.update_idletasks()

        try:
            result = self.planner.plan(raw_input, plan_date)
        except Exception as exc:
            self._plan_status.config(
                text=f"❌ Error: {exc}", fg="#991b1b"
            )
            return

        self._handle_plan_result(result, raw_input, plan_date)

    def _handle_plan_result(self, result, raw_input, plan_date):
        """Common handler for both first-call and continue-call plan results."""
        if result.get("needs_clarification"):
            # Store clarification state
            self._clarification_active   = True
            self._clarification_question = result["question"]
            self._clarification_field    = result["field"]
            self._clarification_title    = result["task_title"]
            self._clarification_pending  = result.get("pending_tasks", [])
            self._clarification_original = result.get("original_input", raw_input)
            self._clarification_date     = result.get("plan_date", plan_date)

            self._plan_status.config(
                text="💬 Please answer the question below to continue.",
                fg="#92400e",
            )
            self._show_clarification_panel(result["question"])
            return

        # Clear clarification state on success
        self._cancel_clarification(silent=True)

        if result.get("error"):
            self._plan_status.config(
                text=f"⚠ {result['error']}", fg="#9a3412"
            )
            return

        schedule = result.get("schedule", [])
        task_count = len(result.get("tasks", []))

        self._plan_status.config(
            text=(
                f"✅ Schedule generated successfully — "
                f"{len(schedule)} entries, "
                f"{task_count} task(s) saved."
            ),
            fg="#166534",
        )

        render_schedule(
            self._plan_result_frame, schedule, bg=BG_MAIN
        )

    # --------------------------------------------------------
    # CLARIFICATION PANEL HELPERS
    # --------------------------------------------------------

    def _show_clarification_panel(self, question):
        """Show the clarification panel with the given question."""
        if not hasattr(self, "_clarif_panel"):
            return
        self._clarif_question_label.config(text=question)
        self._clarif_answer_var.set("")
        self._clarif_panel.pack(fill="x", pady=(0, 14), before=self._plan_result_frame.master)
        self._clarif_entry_widget.focus_set()

    def _hide_clarification_panel(self):
        """Hide the clarification panel."""
        if hasattr(self, "_clarif_panel"):
            self._clarif_panel.pack_forget()

    def _cancel_clarification(self, silent=False):
        """Reset all clarification state."""
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
        """User clicked Continue after answering a clarification question."""
        answer = self._clarif_answer_var.get().strip()
        if not answer:
            self._plan_status.config(
                text="⚠ Please enter an answer before continuing.",
                fg="#9a3412",
            )
            return

        field     = self._clarification_field
        task_title = self._clarification_title
        pending   = self._clarification_pending
        original  = self._clarification_original
        plan_date = self._clarification_date

        self._plan_status.config(text="⏳ Processing...", fg=FG_MUTED)
        self.update_idletasks()

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
            self._plan_status.config(
                text=f"❌ Error: {exc}", fg="#991b1b"
            )
            return

        self._handle_plan_result(result, original, plan_date)

    # ========================================================
    # PAGE: TODAY'S PLAN  (Rich Visual Timeline Dashboard)
    # ========================================================

    def _page_today(self):
        frame = tk.Frame(self.content, bg=BG_MAIN)
        frame.pack(fill="both", expand=True, padx=36, pady=28)

        # Header Row
        top_bar = tk.Frame(frame, bg=BG_MAIN)
        top_bar.pack(fill="x", pady=(0, 6))

        title_box = tk.Frame(top_bar, bg=BG_MAIN)
        title_box.pack(side="left")

        tk.Label(
            title_box,
            text="Good Morning! 👋",
            font=FONT_TITLE, fg=FG_MAIN, bg=BG_MAIN,
        ).pack(anchor="w")

        tk.Label(
            title_box,
            text="Here's your personalized plan for today.",
            font=FONT_BODY, fg=FG_MUTED, bg=BG_MAIN,
        ).pack(anchor="w", pady=(2, 0))

        right_box = tk.Frame(top_bar, bg=BG_MAIN)
        right_box.pack(side="right")

        date_pill = tk.Label(
            right_box,
            text=f" 📅 Today, {format_date_display(today_str())} ",
            font=("Segoe UI", 9, "bold"), fg="#1e40af", bg="#dbeafe",
            padx=10, pady=5,
        )
        date_pill.pack(side="left", padx=(0, 8))

        HoverButton(
            right_box, hover_bg=BTN_SEC_HOVER,
            text=" 🔄 Refresh ",
            font=FONT_BODY,
            bg=BTN_SEC_BG, fg=BTN_SEC_FG,
            relief="flat", padx=10, pady=4, cursor="hand2",
            command=self._page_today,
        ).pack(side="left")

        ttk.Separator(frame, orient="horizontal").pack(
            fill="x", pady=12
        )

        schedule = self.planner.get_today_plan()

        dashboard_row = tk.Frame(frame, bg=BG_MAIN)
        dashboard_row.pack(fill="both", expand=True)

        dashboard_row.columnconfigure(0, weight=3)
        dashboard_row.columnconfigure(1, weight=1)
        dashboard_row.rowconfigure(0, weight=1)

        # --- Left Column: Rich Visual Timeline ---
        left_col = tk.Frame(dashboard_row, bg=BG_MAIN)
        left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 14))

        tk.Label(
            left_col, text="🕒 Your Daily Schedule",
            font=FONT_HEADING, fg=FG_MAIN, bg=BG_MAIN,
        ).pack(anchor="w", pady=(0, 8))

        scroll = ScrollableFrame(left_col, bg=BG_MAIN)
        scroll.pack(fill="both", expand=True)

        render_schedule(scroll.inner, schedule, bg=BG_MAIN)

        # --- Right Column: Summary Card Dashboard ---
        right_col = tk.Frame(
            dashboard_row, bg=BG_CARD,
            highlightbackground=BORDER_COLOR, highlightthickness=1,
            bd=0, padx=18, pady=18,
        )
        right_col.grid(row=0, column=1, sticky="nsew")

        tk.Label(
            right_col, text="📊 Day Overview",
            font=FONT_HEADING, fg=FG_MAIN, bg=BG_CARD,
        ).pack(anchor="w", pady=(0, 14))

        # Unique schedule metrics calculation
        seen_keys = set()
        unique_schedule = []
        for e in schedule:
            key = ((e.get("title") or "").strip().lower(), e.get("start"), e.get("end"))
            if key not in seen_keys:
                seen_keys.add(key)
                unique_schedule.append(e)

        total_items = len(unique_schedule)
        tasks_count = sum(1 for e in unique_schedule if e.get("type") == "task")
        routines_count = sum(1 for e in unique_schedule if e.get("type") == "routine")
        breaks_count = sum(1 for e in unique_schedule if e.get("type") == "break")

        total_minutes = 0
        for e in unique_schedule:
            if "start" in e and "end" in e:
                try:
                    s_m = time_to_minutes(e["start"])
                    e_m = time_to_minutes(e["end"])
                    if e_m > s_m:
                        total_minutes += (e_m - s_m)
                except Exception:
                    pass
        hours = total_minutes // 60
        mins = total_minutes % 60
        time_display = f"{hours}h {mins}m" if hours > 0 else f"{mins}m"

        def _metric_box(parent, title, val, color="#2563eb", bg_tint="#eff6ff"):
            box = tk.Frame(
                parent, bg=bg_tint, padx=12, pady=10,
                highlightbackground=BORDER_COLOR, highlightthickness=1, bd=0
            )
            box.pack(fill="x", pady=5)
            tk.Label(
                box, text=title, font=FONT_SMALL, fg=FG_MUTED, bg=bg_tint
            ).pack(anchor="w")
            tk.Label(
                box, text=str(val), font=("Segoe UI", 16, "bold"), fg=color, bg=bg_tint
            ).pack(anchor="w", pady=(2, 0))

        _metric_box(right_col, "Total Unique Activities", total_items, PRIMARY_BLUE, "#eff6ff")
        _metric_box(right_col, "Total Scheduled Time", time_display, "#0369a1", "#e0f2fe")
        _metric_box(right_col, "Tasks Planned", tasks_count, "#3730a3", "#e0e7ff")
        _metric_box(right_col, "Routines & Breaks", f"{routines_count} routines, {breaks_count} breaks", "#475569", "#f1f5f9")

    # ========================================================
    # PAGE: HISTORY
    # ========================================================

    def _page_history(self):
        frame = tk.Frame(self.content, bg=BG_MAIN)
        frame.pack(fill="both", expand=True, padx=36, pady=28)

        tk.Label(
            frame, text="History",
            font=FONT_TITLE, fg=FG_MAIN, bg=BG_MAIN,
        ).pack(anchor="w")

        tk.Label(
            frame, text="View your past days of planned schedules. All records are permanently preserved.",
            font=FONT_SMALL, fg=FG_MUTED, bg=BG_MAIN,
        ).pack(anchor="w", pady=(2, 10))

        # Search Bar Card  ← EXACT REQUIRED LABEL: "🔍 Search past plans"
        search_card = tk.Frame(
            frame, bg=BG_CARD,
            highlightbackground=BORDER_COLOR, highlightthickness=1,
            bd=0, padx=14, pady=10,
        )
        search_card.pack(fill="x", pady=(0, 12))

        tk.Label(
            search_card,
            text="🔍 Search past plans",
            font=FONT_SUBHEAD, fg=FG_MAIN, bg=BG_CARD,
        ).pack(side="left", padx=(0, 10))

        self._hist_search_var = tk.StringVar()
        search_entry = tk.Entry(
            search_card,
            textvariable=self._hist_search_var,
            font=FONT_BODY, bg=ENTRY_BG, fg=ENTRY_FG,
            highlightbackground=ENTRY_BORDER, highlightthickness=1,
            relief="flat", width=28,
        )
        search_entry.pack(side="left", padx=(0, 8), ipady=3)

        HoverButton(
            search_card, hover_bg=PRIMARY_HOVER,
            text="Search",
            font=FONT_BODY, bg=BTN_BG, fg=BTN_FG,
            relief="flat", padx=12, pady=4, cursor="hand2",
            command=self._history_search,
        ).pack(side="left", padx=(0, 6))

        HoverButton(
            search_card, hover_bg=BTN_SEC_HOVER,
            text="Show All",
            font=FONT_BODY, bg=BTN_SEC_BG, fg=BTN_SEC_FG,
            relief="flat", padx=10, pady=4, cursor="hand2",
            command=self._history_show_all,
        ).pack(side="left")

        paned = tk.Frame(frame, bg=BG_MAIN)
        paned.pack(fill="both", expand=True)

        list_frame = tk.Frame(
            paned, bg=BG_CARD, width=250,
            highlightbackground=BORDER_COLOR, highlightthickness=1, bd=0
        )
        list_frame.pack(side="left", fill="y", padx=(0, 10))
        list_frame.pack_propagate(False)

        tk.Label(
            list_frame, text="Last 10 Days",
            font=FONT_SUBHEAD, fg=FG_MAIN, bg=BG_CARD,
        ).pack(anchor="w", padx=12, pady=10)

        self._hist_listbox = tk.Listbox(
            list_frame, font=FONT_BODY,
            bg=BG_CARD, fg=FG_MAIN,
            selectbackground=PRIMARY_BLUE,
            selectforeground="#ffffff",
            relief="flat", bd=0,
            activestyle="none",
        )
        self._hist_listbox.pack(
            fill="both", expand=True, padx=4, pady=(0, 6)
        )
        self._hist_listbox.bind(
            "<<ListboxSelect>>", self._on_history_select
        )

        detail_outer = tk.Frame(paned, bg=BG_MAIN)
        detail_outer.pack(
            side="left", fill="both", expand=True
        )

        self._hist_detail_label = tk.Label(
            detail_outer, text="Select a plan to view details",
            font=FONT_SUBHEAD, fg=FG_MUTED, bg=BG_MAIN,
        )
        self._hist_detail_label.pack(anchor="w", pady=(0, 6))

        detail_scroll = ScrollableFrame(
            detail_outer, bg=BG_MAIN
        )
        detail_scroll.pack(fill="both", expand=True)
        self._hist_detail_inner = detail_scroll.inner

        self._hist_records = []
        self._history_show_all()

    def _history_show_all(self):
        records = self.planner.get_latest_plans(10)
        self._populate_history_list(records)

    def _history_search(self):
        query = self._hist_search_var.get().strip()
        if not query:
            self._history_show_all()
            return
        records = self.planner.search_history(query)
        self._populate_history_list(records)

    def _populate_history_list(self, records):
        self._hist_records = records
        self._hist_listbox.delete(0, "end")

        if not records:
            self._hist_listbox.insert("end", "  No records found.")
            render_schedule(self._hist_detail_inner, [], bg=BG_MAIN)
            return

        for rec in records:
            label = (
                f"  📅 {rec.get('date', '?')} "
                f"({len(rec.get('schedule', []))} items)"
            )
            self._hist_listbox.insert("end", label)

    def _on_history_select(self, _event):
        sel = self._hist_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        if idx >= len(self._hist_records):
            return
        record = self._hist_records[idx]
        date_label = format_date_display(
            record.get("date", "")
        )
        self._hist_detail_label.config(
            text=f"Schedule for {date_label}",
            fg=FG_MAIN,
        )
        render_schedule(
            self._hist_detail_inner,
            record.get("schedule", []),
            bg=BG_MAIN,
        )

    # ========================================================
    # PAGE: TASKS
    # ========================================================

    def _page_tasks(self):
        frame = tk.Frame(self.content, bg=BG_MAIN)
        frame.pack(fill="both", expand=True, padx=36, pady=28)

        tk.Label(
            frame, text="Task Manager",
            font=FONT_TITLE, fg=FG_MAIN, bg=BG_MAIN,
        ).pack(anchor="w")

        tk.Label(
            frame,
            text="All tasks saved by DayWise. Click a task row to update its status.",
            font=FONT_SMALL, fg=FG_MUTED, bg=BG_MAIN,
        ).pack(anchor="w", pady=(2, 12))

        tasks = self.planner.load_tasks()

        if not tasks:
            empty_card = tk.Frame(
                frame, bg=BG_CARD,
                highlightbackground=BORDER_COLOR, highlightthickness=1,
                bd=0, pady=40, padx=20,
            )
            empty_card.pack(fill="x", pady=20)
            tk.Label(
                empty_card,
                text="No tasks saved yet.\n\nPlan your day to create tasks.",
                font=FONT_BODY, fg=FG_MUTED, bg=BG_CARD,
                justify="center",
            ).pack()
            return

        hdr = tk.Frame(
            frame, bg=BG_PANEL,
            highlightbackground=BORDER_COLOR, highlightthickness=1, bd=0,
            pady=8, padx=12
        )
        hdr.pack(fill="x")

        hdr.columnconfigure(0, weight=3, minsize=200)
        hdr.columnconfigure(1, weight=1, minsize=90)
        hdr.columnconfigure(2, weight=1, minsize=80)
        hdr.columnconfigure(3, weight=1, minsize=80)
        hdr.columnconfigure(4, weight=1, minsize=90)
        hdr.columnconfigure(5, weight=1, minsize=100)

        headers = [
            ("Title", 0, "w"),
            ("Date", 1, "w"),
            ("Duration", 2, "w"),
            ("Priority", 3, "w"),
            ("Context", 4, "w"),
            ("Status", 5, "e"),
        ]
        for text, col, sticky in headers:
            tk.Label(
                hdr, text=text, font=FONT_SUBHEAD,
                fg=FG_MAIN, bg=BG_PANEL, anchor=sticky
            ).grid(row=0, column=col, sticky=sticky, padx=4)

        scroll = ScrollableFrame(frame, bg=BG_MAIN)
        scroll.pack(fill="both", expand=True, pady=(0, 8))

        for task in tasks:
            self._task_row(scroll.inner, task)

    def _task_row(self, parent, task):
        status = str(task.get("status", "pending")).lower()
        duration_min = task.get("duration", 0)
        if duration_min >= 60:
            h = duration_min // 60
            m = duration_min % 60
            duration_str = f"{h}h {m}m" if m > 0 else f"{h}h"
        else:
            duration_str = f"{duration_min}m"

        title_text = task.get("title", "?")
        icon = get_icon_for_title(title_text)

        row = tk.Frame(
            parent, bg=BG_CARD,
            highlightbackground=BORDER_COLOR, highlightthickness=1, bd=0,
            pady=8, padx=12, cursor="hand2"
        )
        row.pack(fill="x", padx=2, pady=3)

        row.columnconfigure(0, weight=3, minsize=200)
        row.columnconfigure(1, weight=1, minsize=90)
        row.columnconfigure(2, weight=1, minsize=80)
        row.columnconfigure(3, weight=1, minsize=80)
        row.columnconfigure(4, weight=1, minsize=90)
        row.columnconfigure(5, weight=1, minsize=100)

        # Title
        tk.Label(
            row, text=f"{icon} {title_text}",
            font=FONT_BODY, fg=FG_MAIN, bg=BG_CARD, anchor="w"
        ).grid(row=0, column=0, sticky="w", padx=4)

        # Date
        tk.Label(
            row, text=str(task.get("date", "-")),
            font=FONT_BODY, fg=FG_MUTED, bg=BG_CARD, anchor="w"
        ).grid(row=0, column=1, sticky="w", padx=4)

        # Duration
        tk.Label(
            row, text=duration_str,
            font=FONT_BODY, fg=FG_MUTED, bg=BG_CARD, anchor="w"
        ).grid(row=0, column=2, sticky="w", padx=4)

        # Priority
        p_val = str(task.get("priority", "normal")).upper()
        p_color = "#ef4444" if p_val == "HIGH" else "#3b82f6" if p_val == "MEDIUM" else FG_MUTED
        tk.Label(
            row, text=p_val,
            font=("Segoe UI", 9, "bold"), fg=p_color, bg=BG_CARD, anchor="w"
        ).grid(row=0, column=3, sticky="w", padx=4)

        # Context
        c_val = str(task.get("context", "-")).capitalize()
        tk.Label(
            row, text=c_val,
            font=FONT_BODY, fg=FG_MUTED, bg=BG_CARD, anchor="w"
        ).grid(row=0, column=4, sticky="w", padx=4)

        # Status badge
        s_bg, s_fg = BADGE_STYLES.get(status, ("#f1f5f9", "#475569"))
        s_badge = tk.Label(
            row, text=f" {status.upper()} ",
            font=("Segoe UI", 8, "bold"), fg=s_fg, bg=s_bg,
            padx=8, pady=3,
        )
        s_badge.grid(row=0, column=5, sticky="e", padx=4)

        row.bind("<Button-1>", lambda e, t=task: self._status_dialog(t))
        for child in row.winfo_children():
            child.bind("<Button-1>", lambda e, t=task: self._status_dialog(t))

    def _status_dialog(self, task):
        dlg = tk.Toplevel(self)
        dlg.title("Update Task Status")
        dlg.configure(bg=BG_MAIN)
        dlg.geometry("360x250")
        dlg.resizable(False, False)

        tk.Label(
            dlg,
            text=truncate(task.get("title", "Task"), 38),
            font=FONT_SUBHEAD, fg=FG_MAIN, bg=BG_MAIN,
        ).pack(pady=(16, 4))

        tk.Label(
            dlg, text="Set new status:",
            font=FONT_BODY, fg=FG_MUTED, bg=BG_MAIN,
        ).pack()

        status_var = tk.StringVar(
            value=task.get("status", "pending")
        )

        for s in ("pending", "scheduled", "completed", "cancelled"):
            tk.Radiobutton(
                dlg, text=s.capitalize(),
                variable=status_var, value=s,
                font=FONT_BODY, fg=FG_MAIN,
                bg=BG_MAIN, activebackground=BG_MAIN,
                selectcolor=PRIMARY_LIGHT,
            ).pack(anchor="w", padx=50, pady=2)

        def _apply():
            new_status = status_var.get()
            task_id = task.get("task_id")
            if task_id:
                self.planner.update_task_status(task_id, new_status)
            dlg.destroy()
            self._show_page("tasks")

        HoverButton(
            dlg, hover_bg=PRIMARY_HOVER,
            text="  Apply Status  ",
            font=FONT_BODY, bg=BTN_BG, fg=BTN_FG,
            relief="flat", padx=12, pady=6, cursor="hand2",
            command=_apply,
        ).pack(pady=14)

    # ========================================================
    # PAGE: ROUTINES (Rich Routine Card Design)
    # ========================================================

    def _page_routines(self):
        frame = tk.Frame(self.content, bg=BG_MAIN)
        frame.pack(fill="both", expand=True, padx=36, pady=28)

        top_row = tk.Frame(frame, bg=BG_MAIN)
        top_row.pack(fill="x", pady=(0, 6))

        tk.Label(
            top_row, text="Routine Management",
            font=FONT_TITLE, fg=FG_MAIN, bg=BG_MAIN,
        ).pack(side="left")

        HoverButton(
            top_row, hover_bg=PRIMARY_HOVER,
            text="  + Add Routine  ",
            font=FONT_SUBHEAD,
            bg=BTN_BG, fg=BTN_FG,
            relief="flat", padx=14, pady=6, cursor="hand2",
            command=self._add_routine_dialog,
        ).pack(side="right")

        tk.Label(
            frame,
            text="Configure recurring daily routines. Active routines automatically block time in your schedule.",
            font=FONT_SMALL, fg=FG_MUTED, bg=BG_MAIN,
        ).pack(anchor="w", pady=(0, 14))

        routines = self.planner.load_routines()
        scroll = ScrollableFrame(frame, bg=BG_MAIN)
        scroll.pack(fill="both", expand=True, pady=(0, 8))

        if not routines:
            empty_card = tk.Frame(
                scroll.inner, bg=BG_CARD,
                highlightbackground=BORDER_COLOR, highlightthickness=1,
                bd=0, pady=40, padx=20,
            )
            empty_card.pack(fill="x", pady=20)
            tk.Label(
                empty_card,
                text="No routines defined yet.\n\nClick '+ Add Routine' above to create one.",
                font=FONT_BODY, fg=FG_MUTED, bg=BG_CARD,
                justify="center",
            ).pack()
        else:
            for r in routines:
                self._render_routine_row(scroll.inner, r)

    def _render_routine_row(self, parent, r):
        """Renders routine as a rich dashboard card matching reference design."""
        row = tk.Frame(
            parent, bg=BG_CARD,
            highlightbackground=BORDER_COLOR, highlightthickness=1, bd=0,
            pady=12, padx=16,
        )
        row.pack(fill="x", expand=True, padx=4, pady=6)

        name = r.get("name") or r.get("title", "Routine")
        start = r.get("start") or r.get("start_time", "00:00")
        end = r.get("end") or r.get("end_time", "00:00")
        start_12 = format_12h(start)
        end_12 = format_12h(end)
        time_str = f"{start_12} – {end_12}"
        active = r.get("enabled", r.get("active", True))
        rid = r.get("routine_id") or name
        icon = get_icon_for_title(name, etype="routine")

        # Top line: Icon + Routine Name + Status Badge
        header_line = tk.Frame(row, bg=BG_CARD)
        header_line.pack(fill="x")

        tk.Label(
            header_line, text=f"{icon} ",
            font=("Segoe UI", 14), bg=BG_CARD
        ).pack(side="left")

        tk.Label(
            header_line, text=name,
            font=FONT_HEADING, fg=FG_MAIN, bg=BG_CARD,
        ).pack(side="left")

        status_txt = "Enabled" if active else "Disabled"
        status_bg = "#dcfce7" if active else "#fee2e2"
        status_fg = "#166534" if active else "#991b1b"

        tk.Label(
            header_line, text=f" {status_txt} ",
            font=("Segoe UI", 8, "bold"), fg=status_fg, bg=status_bg,
            padx=8, pady=3,
        ).pack(side="right")

        # Subtitle line: Time & Recurrence Days
        days = r.get("days", [])
        days_str = ", ".join(days) if days and len(days) < 7 else "Everyday (Monday – Sunday)"
        
        info_line = tk.Frame(row, bg=BG_CARD)
        info_line.pack(fill="x", pady=(6, 8))

        tk.Label(
            info_line, text=f"🕒  {time_str}  |  📅  {days_str}",
            font=FONT_BODY, fg=FG_MUTED, bg=BG_CARD,
        ).pack(anchor="w")

        # Action Buttons
        btn_frame = tk.Frame(row, bg=BG_CARD)
        btn_frame.pack(anchor="e")

        HoverButton(
            btn_frame, hover_bg="#bbf7d0" if active else "#fca5a5",
            text=f" {'Disable' if active else 'Enable'} ",
            font=FONT_SMALL, bg=status_bg, fg=status_fg,
            relief="flat", padx=10, pady=4, cursor="hand2",
            command=lambda: self._toggle_routine(rid),
        ).pack(side="left", padx=4)

        HoverButton(
            btn_frame, hover_bg=BTN_SEC_HOVER,
            text=" Edit ",
            font=FONT_SMALL, bg=BTN_SEC_BG, fg=BTN_SEC_FG,
            relief="flat", padx=10, pady=4, cursor="hand2",
            command=lambda: self._edit_routine_dialog(r),
        ).pack(side="left", padx=4)

        HoverButton(
            btn_frame, hover_bg=BTN_DANGER_HOVER,
            text=" Delete ",
            font=FONT_SMALL, bg=BTN_DANGER_BG, fg=BTN_DANGER_FG,
            relief="flat", padx=10, pady=4, cursor="hand2",
            command=lambda: self._delete_routine_action(r),
        ).pack(side="left", padx=4)

    def _add_routine_dialog(self):
        self._routine_form_dialog(title="Add New Routine", routine=None)

    def _edit_routine_dialog(self, routine):
        self._routine_form_dialog(title="Edit Routine", routine=routine)

    def _routine_form_dialog(self, title, routine=None):
        dlg = tk.Toplevel(self)
        dlg.title(title)
        dlg.configure(bg=BG_MAIN)
        dlg.geometry("440x460")
        dlg.resizable(False, False)

        tk.Label(
            dlg, text=title, font=FONT_HEADING,
            fg=FG_MAIN, bg=BG_MAIN,
        ).pack(pady=(16, 12))

        form = tk.Frame(dlg, bg=BG_MAIN, padx=24)
        form.pack(fill="both", expand=True)

        tk.Label(form, text="Routine Name:", font=FONT_BODY, fg=FG_MAIN, bg=BG_MAIN).pack(anchor="w", pady=(6, 2))
        name_var = tk.StringVar(value=routine.get("name", "") if routine else "")
        name_entry = tk.Entry(form, textvariable=name_var, font=FONT_BODY, bg=ENTRY_BG, fg=ENTRY_FG, highlightbackground=ENTRY_BORDER, highlightthickness=1, relief="flat")
        name_entry.pack(fill="x", ipady=4)
        name_entry.focus_set()

        time_row = tk.Frame(form, bg=BG_MAIN)
        time_row.pack(fill="x", pady=(10, 2))

        tk.Label(time_row, text="Start Time (HH:MM):", font=FONT_BODY, fg=FG_MAIN, bg=BG_MAIN).grid(row=0, column=0, sticky="w")
        tk.Label(time_row, text="End Time (HH:MM):", font=FONT_BODY, fg=FG_MAIN, bg=BG_MAIN).grid(row=0, column=1, sticky="w", padx=(20, 0))

        start_var = tk.StringVar(value=routine.get("start_time", routine.get("start", "06:00")) if routine else "06:00")
        start_entry = tk.Entry(time_row, textvariable=start_var, font=FONT_BODY, bg=ENTRY_BG, fg=ENTRY_FG, highlightbackground=ENTRY_BORDER, highlightthickness=1, relief="flat", width=12)
        start_entry.grid(row=1, column=0, sticky="w", ipady=4, pady=(2, 0))

        end_var = tk.StringVar(value=routine.get("end_time", routine.get("end", "07:00")) if routine else "07:00")
        end_entry = tk.Entry(time_row, textvariable=end_var, font=FONT_BODY, bg=ENTRY_BG, fg=ENTRY_FG, highlightbackground=ENTRY_BORDER, highlightthickness=1, relief="flat", width=12)
        end_entry.grid(row=1, column=1, sticky="w", padx=(20, 0), ipady=4, pady=(2, 0))

        tk.Label(form, text="Recurrence Days:", font=FONT_BODY, fg=FG_MAIN, bg=BG_MAIN).pack(anchor="w", pady=(12, 4))
        days_frame = tk.Frame(form, bg=BG_MAIN)
        days_frame.pack(fill="x", pady=2)

        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        day_vars = {}
        existing_days = routine.get("days", day_names) if routine else day_names

        for d in day_names:
            var = tk.BooleanVar(value=(d in existing_days))
            day_vars[d] = var
            cb = tk.Checkbutton(
                days_frame, text=d[:3], variable=var,
                font=FONT_SMALL, fg=FG_MAIN, bg=BG_MAIN,
                activebackground=BG_MAIN, selectcolor=PRIMARY_LIGHT
            )
            cb.pack(side="left", padx=1)

        def _save():
            name = name_var.get().strip()
            start = start_var.get().strip()
            end = end_var.get().strip()

            if not name:
                messagebox.showerror("Validation Error", "Routine Name cannot be empty.", parent=dlg)
                return

            time_regex = r"^([01]?\d|2[0-3]):[0-5]\d$"
            if not re.match(time_regex, start):
                messagebox.showerror("Validation Error", "Start Time must be valid HH:MM format (e.g. 06:30).", parent=dlg)
                return
            if not re.match(time_regex, end):
                messagebox.showerror("Validation Error", "End Time must be valid HH:MM format (e.g. 07:30).", parent=dlg)
                return

            s_min = time_to_minutes(start)
            e_min = time_to_minutes(end)
            if e_min <= s_min:
                messagebox.showerror("Validation Error", "End Time must be after Start Time.", parent=dlg)
                return

            selected_days = [d for d, v in day_vars.items() if v.get()]
            if not selected_days:
                selected_days = day_names

            rec = {
                "routine_id": routine.get("routine_id") if routine else None,
                "name": name,
                "title": name,
                "start_time": start,
                "start": start,
                "end_time": end,
                "end": end,
                "days": selected_days,
                "enabled": routine.get("enabled", True) if routine else True,
                "active": routine.get("active", True) if routine else True,
            }
            self.planner.data_manager.add_routine(rec)
            dlg.destroy()
            self._show_page("routines")

        btn_box = tk.Frame(dlg, bg=BG_MAIN)
        btn_box.pack(pady=16)

        HoverButton(
            btn_box, hover_bg=PRIMARY_HOVER,
            text="  Save Routine  ", font=FONT_SUBHEAD,
            bg=BTN_BG, fg=BTN_FG, relief="flat", padx=14, pady=6, cursor="hand2",
            command=_save,
        ).pack(side="left", padx=6)

        HoverButton(
            btn_box, hover_bg=BTN_SEC_HOVER,
            text=" Cancel ", font=FONT_BODY,
            bg=BTN_SEC_BG, fg=BTN_SEC_FG, relief="flat", padx=10, pady=6, cursor="hand2",
            command=dlg.destroy,
        ).pack(side="left", padx=6)

    def _delete_routine_action(self, r):
        name = r.get("name") or r.get("title", "Routine")
        rid = r.get("routine_id") or name
        if messagebox.askyesno("Confirm Delete", f"Delete routine '{name}'?\nThis will remove it from future plans."):
            self.planner.data_manager.delete_routine(rid)
            self._show_page("routines")

    def _toggle_routine(self, rid):
        self.planner.data_manager.toggle_routine_status(rid)
        self._show_page("routines")

    # ========================================================
    # PAGE: MEMORY
    # ========================================================

    def _page_memory(self):
        frame = tk.Frame(self.content, bg=BG_MAIN)
        frame.pack(fill="both", expand=True, padx=36, pady=28)

        tk.Label(
            frame, text="Long-term Memory",
            font=FONT_TITLE, fg=FG_MAIN, bg=BG_MAIN,
        ).pack(anchor="w")

        tk.Label(
            frame,
            text="DayWise remembers useful information to improve future planning.",
            font=FONT_BODY, fg=FG_MUTED, bg=BG_MAIN,
        ).pack(anchor="w", pady=(2, 16))

        memory = self.planner.load_memory()

        scroll = ScrollableFrame(frame, bg=BG_MAIN)
        scroll.pack(fill="both", expand=True)

        category_labels = {
            "preferences":   ("⚙  Preferences",          PRIMARY_BLUE),
            "routines":      ("🔄  Recurring Activities", "#0369a1"),
            "future_events": ("📅  Future Events",        "#9a3412"),
            "constraints":   ("🚫  Schedule Constraints", "#991b1b"),
            "sleep_schedule":("😴  Sleep Schedule",       FG_MUTED),
        }

        has_any = False

        for cat, (label, colour) in category_labels.items():
            entries = memory.get(cat, [])
            if not entries:
                continue
            has_any = True

            tk.Label(
                scroll.inner, text=label,
                font=FONT_SUBHEAD, fg=colour, bg=BG_MAIN,
            ).pack(anchor="w", padx=4, pady=(12, 4))

            for entry in entries:
                card = tk.Frame(
                    scroll.inner, bg=BG_CARD,
                    highlightbackground=BORDER_COLOR, highlightthickness=1, bd=0,
                    padx=14, pady=8,
                )
                card.pack(fill="x", expand=True, padx=4, pady=3)

                tk.Label(
                    card,
                    text=entry.get("text", str(entry)),
                    font=FONT_BODY, fg=FG_MAIN, bg=BG_CARD,
                    wraplength=650, justify="left",
                ).pack(anchor="w")

                added = entry.get("added_at", "")
                if added:
                    tk.Label(
                        card, text=f"Stored: {added}",
                        font=FONT_SMALL, fg=FG_MUTED, bg=BG_CARD,
                    ).pack(anchor="w")

        if not has_any:
            empty_card = tk.Frame(
                scroll.inner, bg=BG_CARD,
                highlightbackground=BORDER_COLOR, highlightthickness=1,
                bd=0, pady=40, padx=20,
            )
            empty_card.pack(fill="x", pady=20)
            tk.Label(
                empty_card,
                text=(
                    "No memory entries yet.\n\n"
                    "DayWise will remember useful facts as you interact with it.\n\n"
                    'Try: "I prefer studying at night" or\n'
                    '"I have college from 9 AM to 4 PM"'
                ),
                font=FONT_BODY, fg=FG_MUTED, bg=BG_CARD,
                justify="center",
            ).pack()

    # ========================================================
    # PAGE: SEARCH
    # ========================================================

    def _page_search(self):
        frame = tk.Frame(self.content, bg=BG_MAIN)
        frame.pack(fill="both", expand=True, padx=36, pady=28)

        tk.Label(
            frame, text="Search",
            font=FONT_TITLE, fg=FG_MAIN, bg=BG_MAIN,
        ).pack(anchor="w")

        # Exact required label: "🔍 Search past plans"
        tk.Label(
            frame, text="🔍 Search past plans",
            font=FONT_HEADING, fg=FG_MAIN, bg=BG_MAIN,
        ).pack(anchor="w", pady=(8, 4))

        tk.Label(
            frame,
            text="Search by date (YYYY-MM-DD), task title, or keyword.",
            font=FONT_SMALL, fg=FG_MUTED, bg=BG_MAIN,
        ).pack(anchor="w", pady=(0, 10))

        search_card = tk.Frame(
            frame, bg=BG_CARD,
            highlightbackground=BORDER_COLOR, highlightthickness=1,
            bd=0, padx=14, pady=10,
        )
        search_card.pack(fill="x", pady=(0, 14))

        self._search_var = tk.StringVar()
        search_entry = tk.Entry(
            search_card,
            textvariable=self._search_var,
            font=FONT_BODY, bg=ENTRY_BG, fg=ENTRY_FG,
            highlightbackground=ENTRY_BORDER, highlightthickness=1,
            relief="flat", width=42,
        )
        search_entry.pack(side="left", padx=(0, 10), ipady=4)
        search_entry.focus_set()
        search_entry.bind("<Return>", lambda e: self._do_search())

        HoverButton(
            search_card, hover_bg=PRIMARY_HOVER,
            text="  🔍  Search  ",
            font=FONT_SUBHEAD, bg=BTN_BG, fg=BTN_FG,
            relief="flat", padx=12, pady=6, cursor="hand2",
            command=self._do_search,
        ).pack(side="left")

        self._search_result_label = tk.Label(
            frame, text="", font=FONT_BODY,
            fg=FG_MUTED, bg=BG_MAIN,
        )
        self._search_result_label.pack(anchor="w", pady=(0, 8))

        scroll = ScrollableFrame(frame, bg=BG_MAIN)
        scroll.pack(fill="both", expand=True)
        self._search_results_frame = scroll.inner

    def _do_search(self):
        query = self._search_var.get().strip()
        if not query:
            self._search_result_label.config(
                text="Enter a search term above.", fg=FG_MUTED
            )
            return

        results = self.planner.search_history(query)
        self._search_result_label.config(
            text=f"{len(results)} result(s) found for '{query}'",
            fg="#166534" if results else "#9a3412",
        )

        for w in self._search_results_frame.winfo_children():
            w.destroy()

        if not results:
            empty_card = tk.Frame(
                self._search_results_frame, bg=BG_CARD,
                highlightbackground=BORDER_COLOR, highlightthickness=1,
                bd=0, pady=30, padx=20,
            )
            empty_card.pack(fill="x", pady=10)
            tk.Label(
                empty_card,
                text="No plans found matching your search.",
                font=FONT_BODY, fg=FG_MUTED, bg=BG_CARD,
            ).pack()
            return

        for record in results:
            date_label = format_date_display(
                record.get("date", "")
            )
            created = record.get("created_at", "")[:16]
            header = tk.Frame(
                self._search_results_frame,
                bg=PRIMARY_LIGHT, pady=6, padx=12,
                highlightbackground=BORDER_COLOR, highlightthickness=1, bd=0
            )
            header.pack(fill="x", expand=True, pady=(10, 0))

            tk.Label(
                header,
                text=f"📅  {date_label}  |  Created: {created}",
                font=FONT_SUBHEAD, fg=PRIMARY_BLUE, bg=PRIMARY_LIGHT,
            ).pack(anchor="w")

            render_schedule(
                self._search_results_frame,
                record.get("schedule", []),
                bg=BG_MAIN,
            )


# ============================================================
# ENTRY POINT
# ============================================================

def launch_gui():
    app = DayWiseApp()
    app.mainloop()


if __name__ == "__main__":
    launch_gui()
