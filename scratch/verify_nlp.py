import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.planner import Planner

p = Planner()
text = "Tomorrow I have a college class. Before that, I want to exercise and have breakfast. After lunch, I need to prepare for my interview, complete my assignment by evening, and spend some time with my friends later in the day."
res = p.plan(text)

print("=== PARSED TASKS ===")
for t in res["tasks"]:
    print(f"Title: {t.get('title')}")
    print(f"  Date: {t.get('date')}")
    print(f"  Time Type: {t.get('time_type')}")
    print(f"  Relationship: {t.get('relationship')}")
    print(f"  Context Window: {t.get('context_window')}")
    print(f"  Deadline Time: {t.get('deadline_time')}")
    print()

print("=== GENERATED SCHEDULE ===")
for s in res["schedule"]:
    print(f"{s.get('start')} - {s.get('end')} | {s.get('title')} [{s.get('type')}] ({s.get('time_type', 'N/A')})")
