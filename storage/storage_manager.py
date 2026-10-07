import json
import os
from datetime import datetime


# ============================================================
# PATH SETUP
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

DATA_DIR = os.path.join(
    BASE_DIR,
    "data"
)


# ============================================================
# ENSURE DATA DIRECTORY
# ============================================================

def ensure_data_directory():
    """
    Creates the data directory if it does not exist.
    """

    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)


# ============================================================
# GET FILE PATH
# ============================================================

def get_data_file(filename):
    """
    Returns the complete path of a JSON data file.
    """

    ensure_data_directory()

    return os.path.join(
        DATA_DIR,
        filename
    )


# ============================================================
# LOAD JSON
# ============================================================

def load_json(filename, default=None):
    """
    Loads JSON data from the data directory.

    If the file does not exist or contains invalid JSON,
    the provided default value is returned.
    """

    if default is None:
        default = []

    file_path = get_data_file(filename)

    if not os.path.exists(file_path):
        return default

    try:

        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except (json.JSONDecodeError, OSError):

        return default


# ============================================================
# SAVE JSON
# ============================================================

def save_json(filename, data):
    """
    Saves data into a JSON file.
    """

    file_path = get_data_file(filename)

    with open(
        file_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False
        )


# ============================================================
# LOAD HISTORY
# ============================================================

def load_history():
    """
    Loads all permanently stored schedule history.
    """

    history = load_json(
        "history.json",
        []
    )

    # Make sure history is always a list.
    if not isinstance(history, list):
        return []

    return history


# ============================================================
# SAVE HISTORY
# ============================================================

def save_history(history):
    """
    Saves the complete history list permanently.
    """

    save_json(
        "history.json",
        history
    )


# ============================================================
# CREATE HISTORY RECORD
# ============================================================

def create_history_record(schedule, plan_date=None):
    """
    Creates one history record for a generated daily plan.

    Parameters:
        schedule   -> generated schedule list
        plan_date  -> optional date in YYYY-MM-DD format
    """

    if plan_date is None:

        plan_date = datetime.now().strftime(
            "%Y-%m-%d"
        )

    created_at = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    return {
        "date": plan_date,
        "created_at": created_at,
        "schedule": schedule
    }


# ============================================================
# ADD PLAN TO HISTORY
# ============================================================

def add_plan_to_history(schedule, plan_date=None):
    """
    Adds a newly generated schedule to permanent history.

    Existing history is preserved.
    """

    history = load_history()

    new_record = create_history_record(
        schedule,
        plan_date
    )

    history.append(
        new_record
    )

    save_history(
        history
    )

    return new_record


# ============================================================
# GET HISTORY FOR A DATE
# ============================================================

def get_history_by_date(plan_date):
    """
    Returns all saved plans for a specific date.

    Example:
        get_history_by_date("2026-10-04")
    """

    history = load_history()

    matching_records = []

    for record in history:

        if record.get("date") == plan_date:

            matching_records.append(
                record
            )

    return matching_records


# ============================================================
# GET LATEST HISTORY
# ============================================================

def get_latest_history(limit=10):
    """
    Returns the latest saved history records.

    Important:
    This does NOT delete older records.

    It only controls how many records are returned
    for display.
    """

    history = load_history()

    return history[-limit:]


# ============================================================
# SEARCH HISTORY
# ============================================================

def search_history(search_text):
    """
    Searches saved plans by date or schedule text.

    This will later be used by:

        🔍 Search past plans
    """

    search_text = search_text.strip().lower()

    if not search_text:
        return []

    history = load_history()

    results = []

    for record in history:

        record_date = str(
            record.get("date", "")
        ).lower()

        schedule = record.get(
            "schedule",
            []
        )

        schedule_text = json.dumps(
            schedule,
            ensure_ascii=False
        ).lower()

        if (
            search_text in record_date
            or search_text in schedule_text
        ):

            results.append(
                record
            )

    return results


# ============================================================
# TESTING
# ============================================================

if __name__ == "__main__":

    print("DayWise Storage Manager")
    print("-----------------------")

    ensure_data_directory()

    print(
        f"Data directory: {DATA_DIR}"
    )

    # --------------------------------------------------------
    # Test history
    # --------------------------------------------------------

    test_schedule = [
        {
            "start": "09:00",
            "end": "11:00",
            "title": "Study Python",
            "type": "task",
            "task_id": "test1234",
            "segment_number": 1,
            "total_segments": 1
        },
        {
            "start": "11:00",
            "end": "11:15",
            "title": "Short break",
            "type": "break"
        }
    ]

    record = add_plan_to_history(
        test_schedule
    )

    print()
    print("History Record Saved")
    print("--------------------")

    print(
        json.dumps(
            record,
            indent=4,
            ensure_ascii=False
        )
    )

    print()
    print("Latest History")
    print("---------------")

    latest = get_latest_history(
        10
    )

    print(
        json.dumps(
            latest,
            indent=4,
            ensure_ascii=False
        )
    )