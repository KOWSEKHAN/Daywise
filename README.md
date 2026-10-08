# Daywise 🗓️

An AI-assisted, NLP-driven daily schedule planner and desktop assistant built with a **Zero-Dependency Architecture** relying entirely on Python's Standard Library.

Daywise parses natural language inputs (such as *"Tomorrow I have a college class from 9 AM to 1 PM. Before that I want to exercise and have breakfast. After lunch I need to study Python for 2 hours."*), resolves time collisions, extracts routines and long-term memory, clarifies missing times interactively, and generates intelligent, time-blocked daily schedules.

---

## Key Features

- **Personal Planning Lifecycle**:
  - **Routine Periods & Common Library**: Define time-bounded routine periods (e.g. Semester, Project, Sprint) with a common task library and individual Monday–Sunday overrides.
  - **Date-Specific Plan My Day**: Pick any target date (Today or Future) to auto-load applicable routines, add one-time tasks with categories/durations, or provide natural language instructions.
  - **Explicit Plan Confirmation**:
    - **Today's Date**: Promoted directly into **Today's Active Plan** (`data/active_plan.json`).
    - **Future Dates**: Stored as **Future Confirmed Plans** (`data/future_plans.json`).
    - **Past Dates**: Guarded against accidental generation/confirmation (audited edits only).
  - **Today's Active Plan Execution**: Live status tracking (`completed`, `in_progress`, `not_completed`), notes logging, in-place time adjustments, and day finalization.
  - **Automated Midnight Rollover**: Automatically finalizes past active plans into immutable history records and promotes matching future confirmed plans into today's active plan.
  - **Audited Historical Edits**: Read-only history records with controlled, audited task updates requiring mandatory edit notes and preserving full before/after audit trails.
- **Natural Language Parsing**: Rule-based NLP heuristics extract tasks, fixed events, dates, durations, priorities, deadlines, and relative dependencies (`before`, `after`, `later in the day`).
- **Interactive Clarification System**: Detects ambiguous or missing event parameters (e.g. asking *"What time does your college class start?"*) before scheduling.
- **Intelligent Time-Blocking Scheduler**:
  - Anchors fixed events and daily routines (immovable blocks).
  - Shifts and packs flexible tasks into free slots without overlaps.
  - Automatically deduplicates routines (e.g., Gym Session, Breakfast, Lunch) against explicit user requests.
- **Zero-Dependency Desktop GUI**: Modern, responsive tabbed desktop interface powered by Python's built-in `tkinter`.
- **Local JSON Storage**: Persists tasks, history, routine periods, active plans, future plans, and user memories locally in `data/` without external database servers.

---

## Technology Stack

| Layer | Technology | Purpose | Status |
|---|---|---|---|
| **Language** | Python 3.10+ (tested on 3.10.11 & 3.14) | Application runtime | Active |
| **UI Framework** | Tkinter (`tkinter`, `ttk`) | Desktop graphical user interface | Built-in |
| **Storage** | JSON / File I/O (`json`, `os`) | Local file persistence | Built-in |
| **Testing** | `unittest` | Unit & lifecycle test suite (111 tests) | Built-in |
| **External Dependencies** | **None** | Zero third-party dependencies required | Standard Library |

---

## Getting Started

### Prerequisites

1. **Python 3.10 or higher**:
   - On **Windows**: When installing Python from [python.org](https://www.python.org/), ensure you check:
     -  **Add Python to PATH**
     -  **tcl/tk and IDLE** (required for Tkinter GUI)
   - On **Linux (Debian/Ubuntu)**:
     ```bash
     sudo apt update && sudo apt install python3 python3-tk
     ```
   - On **macOS**:
     ```brew install python-tk```

2. **No `pip install` needed**:
   Daywise has zero external packages. Everything runs out of the box with standard Python.

### Running the Application

Launch the desktop interface:

```bash
# Windows (via launcher or python)
py main.py
# or
python main.py
```

### Running Tests

Execute the complete regression and lifecycle test suite:

```bash
# Windows
py -m unittest discover tests

# Linux / macOS
python3 -m unittest discover tests
```

Expected result:
```text
Ran 111 tests in ~9s
OK
All validations PASSED.
```

---

## Directory Structure

```text
Daywise/
├── core/                  # Core Business Logic & Algorithms
│   ├── parser.py          # NLP heuristics, regex extractors, clarification detectors
│   ├── planner.py         # Orchestrator for full lifecycle, routines, confirmation, rollover
│   ├── scheduler.py       # Time-blocking algorithm, slot allocator, collision repair
│   └── memory.py          # Long-term memory extraction & preference tracking
├── data/                  # Local JSON data store (auto-generated; ignored by git)
│   ├── active_plan.json   # Today's active execution plan
│   ├── future_plans.json  # Confirmed future daily plans
│   ├── routine_periods.json # Date-bounded routine periods with Mon-Sun day maps
│   ├── history.json       # Permanent historical records and audit logs
│   ├── tasks.json         # Tasks and status records
│   ├── routines.json      # Default daily routines (legacy fallback)
│   ├── events.json        # User calendar events
│   └── memory.json        # Long-term user memories
├── models/                # Data structures & schemas
│   ├── task.py            # Task definitions & lifecycle source/status fields
│   ├── routine.py         # RoutinePeriod, RoutineTaskTemplate, DayRoutineItem
│   ├── plan.py            # PlanRecord & PlanStatus lifecycle states
│   ├── history.py         # HistoricalRecord & HistoricalEditAudit
│   └── event.py           # Event definitions
├── storage/               # Persistence layer
│   ├── data_manager.py    # High-level data access API for all lifecycle artifacts
│   └── storage_manager.py # Low-level atomic file read/write operations
├── ui/                    # Presentation layer
│   └── gui.py             # Full-featured Tkinter desktop GUI
├── utils/                 # Utility functions
│   ├── date_utils.py      # Date calculations, range validation, overlaps
│   └── text_utils.py      # String sanitization & normalization
├── tests/                 # Unit & lifecycle test suite
│   ├── test_daywise.py    # 100 core regression tests
│   ├── test_lifecycle.py  # 11 comprehensive lifecycle system tests
│   └── test_gui_imports.py# GUI import sanity check
├── .gitignore             # Standard git ignore rules (ignores data/*.json & cache)
├── .python-version        # Version specification (3.10.11)
├── requirements.txt       # Project dependencies notice (Standard Library only)
├── main.py                # Application entry point
└── README.md              # Project documentation
```

---

## The Complete Planning Lifecycle

```text
1. ROUTINES (Periods & Common Library)
   │  Define date ranges (e.g. 2026-10-01 to 2026-10-31)
   │  Configure common tasks + Mon-Sun day-specific overrides
   ▼
2. PLAN MY DAY (Date Selection)
   │  Select Target Date (Today or Future Date)
   │  Auto-loads applicable routines for that date and weekday
   │  Add one-time tasks or input natural language prompt
   ▼
3. GENERATE PLAN & REVIEW
   │  Deterministic time-blocking scheduler generates collision-free timetable
   │  User reviews schedule preview and makes manual adjustments
   ▼
4. CONFIRM PLAN
   ├─► IF Target Date == Today  ──► Today's Active Plan (data/active_plan.json)
   ├─► IF Target Date >  Today  ──► Future Confirmed Plan (data/future_plans.json)
   └─► IF Target Date <  Today  ──► Rejected (Must use Historical Edit)
   ▼
5. TODAY'S ACTIVE PLAN (Execution)
   │  Live status updates (Completed, In Progress, Not Completed)
   │  Add notes, adjust time blocks in real time
   ▼
6. DAY CLOSURE & MIDNIGHT ROLLOVER
   │  Automatic or manual day finalization
   │  Moves active plan to data/history.json
   │  Promotes matching future confirmed plan to active plan
   ▼
7. HISTORY & AUDIT TRAIL
   │  Read-only permanent records
   │  Controlled edits require mandatory note and log before/after audit entries
```

---

## Key Design Principles

1. **Zero-Dependency Rule**: The project strictly uses the standard library (`tkinter`, `json`, `datetime`, `re`, `uuid`, `unittest`).
2. **Local-First & Privacy Preserving**: All plans, routines, and memories remain exclusively on local disk in `data/`.
3. **Decoupled Architecture**: `ui/gui.py` contains zero scheduling or business logic; all interactions pass through `core.planner.Planner`.
4. **Collision Guarantee**: `core/scheduler.py` guarantees zero time slot overlaps for all fixed events, routines, and flexible tasks.
5. **Audited History**: Historical records cannot be silently mutated; every modification requires an explanatory note and appends to an immutable audit trail.
