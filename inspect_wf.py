#!/usr/bin/env python3
"""Inspect the structure of a launched workflow to locate the active task id
and understand the task object shape (current_task was null)."""
import json
import sys
import pneumatic as P

wid = sys.argv[1] if len(sys.argv) > 1 else "453"
s, wf = P.get(f"/workflows/{wid}")
print("HTTP", s)
print("top-level keys:", sorted(wf.keys()) if isinstance(wf, dict) else wf)
print("\ncurrent_task value:", json.dumps(wf.get("current_task")))

tasks = wf.get("tasks", [])
print(f"\n{len(tasks)} tasks; first task object full:")
print(json.dumps(tasks[0], indent=1)[:1500])

print("\nactive task(s):")
for t in tasks:
    if t.get("status") == "active":
        print(json.dumps({k: t.get(k) for k in
              ("id", "number", "name", "status", "api_name")}, indent=1))
