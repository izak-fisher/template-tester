#!/usr/bin/env python3
"""Fetch a LIVE template and derive:
  - the profit-center dropdown selections (value -> selection api_name)
  - the full task-1 required-field list
  - profit center value -> expected (skip-unless) task numbers/names

Writes pc_map_<id>.json for the runner to consume.
"""
import json
import sys
import pneumatic as P

PC_FIELD = "field-c8dac7"  # Profit/Cost Center (same api_name across instances)


def build(tid):
    s, d = P.get(f"/templates/{tid}")
    if s != 200:
        raise SystemExit(f"GET /templates/{tid} -> {s}: {d}")

    tasks = d["tasks"]
    t1 = tasks[0]
    assert t1["number"] == 1, "task 1 is not first?"

    # task-1 fields
    fields = []
    pc_selections = {}   # value string -> selection api_name
    for f in t1.get("fields", []):
        fields.append({
            "api_name": f["api_name"], "type": f["type"],
            "name": f["name"], "required": f.get("is_required"),
            "selections": [{"value": sl["value"], "api_name": sl["api_name"]}
                           for sl in (f.get("selections") or [])],
        })
        if f["api_name"] == PC_FIELD:
            for sl in f.get("selections") or []:
                pc_selections[sl["value"]] = sl["api_name"]

    # profit center value -> task numbers (skip_task unless PC equals value)
    name_by_num = {t["number"]: t["name"] for t in tasks}
    paths = {}
    for t in tasks[1:]:
        for c in t.get("conditions", []):
            if c.get("action") != "skip_task":
                continue
            for r in c["rules"]:
                for p in r["predicates"]:
                    if p.get("field") == PC_FIELD and p.get("operator") == "not_equals":
                        paths.setdefault(p["value"], []).append(t["number"])

    out = {
        "template_id": tid, "name": d["name"],
        "task_count": len(tasks),
        "fields": fields,
        "pc_selections": pc_selections,
        "paths": paths, "task_names": name_by_num,
    }
    path = f"pc_map_{tid}.json"
    json.dump(out, open(path, "w"), indent=1)

    print(f"=== template {tid}: {d['name']} ({len(tasks)} tasks) ===")
    print(f"task-1 fields: {len(fields)} | profit centers: {len(pc_selections)}")
    unmatched = set(pc_selections) - set(paths)
    for val, sel in pc_selections.items():
        ts = paths.get(val, [])
        names = [name_by_num[n] for n in ts]
        print(f"  {val!r:42} [{sel}] -> {ts} {names if not ts else ''}")
    if unmatched:
        print(f"  !! profit centers with NO gated tasks: {unmatched}")
    # tasks gated by a PC value that isn't a known selection (typo risk)
    ghost = set(paths) - set(pc_selections)
    if ghost:
        print(f"  !! condition values not in dropdown selections: {ghost}")
    print(f"  -> wrote {path}")
    return out


if __name__ == "__main__":
    for tid in (sys.argv[1:] or ["20", "7"]):
        build(int(tid))
        print()
