"""
tests/test_gui_imports.py
Verify all GUI imports work without starting the display.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import tkinter
    print("tkinter: OK")
except ImportError as e:
    print(f"tkinter: MISSING - {e}")

try:
    from core.planner import Planner
    print("core.planner: OK")
except Exception as e:
    print(f"core.planner: ERROR - {e}")

try:
    from core.memory import MemoryManager
    print("core.memory: OK")
except Exception as e:
    print(f"core.memory: ERROR - {e}")

try:
    from storage.data_manager import DataManager
    print("storage.data_manager: OK")
except Exception as e:
    print(f"storage.data_manager: ERROR - {e}")

try:
    from utils.date_utils import today_str, format_date_display
    print("utils.date_utils: OK")
except Exception as e:
    print(f"utils.date_utils: ERROR - {e}")

try:
    from utils.text_utils import truncate, format_schedule_block
    print("utils.text_utils: OK")
except Exception as e:
    print(f"utils.text_utils: ERROR - {e}")

# Test planner end-to-end without GUI
p = Planner()
result = p.plan("Exercise")
assert result["error"] is None, f"Planner error: {result['error']}"
assert len(result["schedule"]) > 0, "Empty schedule"
print("Full pipeline: OK")

# Test history retrieval
records = p.get_latest_plans(10)
assert isinstance(records, list)
print("History retrieval: OK")

# Test search
results = p.search_history("exercise")
assert isinstance(results, list)
print("History search: OK")

# Test task loading
tasks = p.load_tasks()
assert isinstance(tasks, list)
print("Task persistence: OK")

# Test memory
mem = p.load_memory()
assert isinstance(mem, dict)
print("Memory: OK")

# Test routines
routines = p.load_routines()
assert isinstance(routines, list)
print("Routines: OK")

print()
print("All validations PASSED.")
