#!/usr/bin/env python3
"""Finish the viability probe on an existing workflow: complete task 1 with a
profit center, observe routing, then attempt to complete the next (department-
head) task to learn whether the API token may complete others' tasks."""
import json
import sys
import pneumatic as P

wid = int(sys.argv[1]) if len(sys.argv) > 1 else 453

# Dropdown OUTPUT values are the selection VALUE STRINGS (not api_names).
OUTPUT = {
    "field-c8dac7": "10130 AV Support",     # -> expect tasks [20, 21]
    "field-8de817": "One time expense", "field-15c87b": 1000,
    "field-4e1851": "No", "field-8f7ad8": "1 (one)",
    "field-d9b9c3": "probe", "field-13d86b": "Probe Vendor",
    "field-d88887": "probe", "field-3279bf": "probe", "field-bef926": "probe",
    "field-0f592e": "probe", "field-a5b852": "Yes",
    "field-ab2ba2": "No", "field-78bb32": "probe",
    "field-c33bc3": "probe",
}


def active(wf):
    return [(t["id"], t["number"], t["name"]) for t in wf["tasks"]
            if t.get("status") == "active"]


def status_counts(wf):
    from collections import Counter
    return dict(Counter(t.get("status") for t in wf["tasks"]))


s, wf = P.get(f"/workflows/{wid}")
act = active(wf)
print("active before:", act)
t1 = act[0][0]

s, d = P.post(f"/workflows/{wid}/task-complete", {"task_id": t1, "output": OUTPUT})
print(f"\ncomplete task1 ({t1}) -> HTTP {s}")
if s != 200:
    print(json.dumps(d, indent=1)[:800]); sys.exit()

s, wf = P.get(f"/workflows/{wid}")
print("status counts:", status_counts(wf))
print("active after task1:", active(wf), "(expected #20,21 for AV Support)")

# permission test: complete the now-active department-head task
act = active(wf)
if act:
    nxt = act[0][0]
    s, d = P.post(f"/workflows/{wid}/task-complete", {"task_id": nxt, "output": {}})
    print(f"\nDOWNSTREAM complete task {nxt} (#{act[0][1]} {act[0][2]}) -> HTTP {s}")
    print(json.dumps(d, indent=1)[:600] if isinstance(d, (dict, list)) else str(d)[:600])
    s, wf = P.get(f"/workflows/{wid}")
    print("active after downstream:", active(wf))
    print("status counts:", status_counts(wf))
