#!/usr/bin/env python3
"""One-shot viability probe against template 20 on yamaha-stage-2.

Answers:
  1. Does auth + base URL work?
  2. What is the real launch + workflow-read + complete-task shape?
  3. After completing the 'Initiate Process' task with a profit center,
     which tasks become active vs skipped? (does routing work?)
  4. Can this API token complete a downstream task assigned to someone else?

Uses profit center '10130 AV Support' -> expected active chain: tasks 17,18.
"""
import json
import pneumatic as P

TEMPLATE = 20
PC_SELECTION = "selection-6c980e"   # '10130 AV Support'
EXPECTED_TASKS = [17, 18]

# Every task-1 field is required; fill them all with safe test values.
OUTPUT = {
    "field-c8dac7": PC_SELECTION,        # Profit/Cost Center
    "field-8de817": "selection-dc99b2",  # One Time or Recurring -> One time
    "field-15c87b": 1000,                # Estimated Total Cost
    "field-4e1851": "selection-2a5baf",  # Multiple Quotes Obtained -> No
    "field-8f7ad8": "selection-c139f5",  # No. of Quotes -> 1 (one)
    "field-d9b9c3": "probe: details about quotes",
    "field-13d86b": "Probe Vendor",      # Vendor Name
    "field-d88887": "probe: vendor justification",
    "field-3279bf": "probe: background/purpose",
    "field-bef926": "probe: details of purchase",
    "field-0f592e": "probe: final destination",
    "field-a5b852": "selection-6d088d",  # Employee Acknowledgement -> Yes
    "field-ab2ba2": "selection-160904",  # Previous relationship -> No
    "field-78bb32": "probe: explanation of relationship",
    "field-c33bc3": "probe: notes and attachments",
}


def show(label, status, data):
    print(f"\n### {label}  -> HTTP {status}")
    if isinstance(data, (dict, list)):
        print(json.dumps(data, indent=1)[:1200])
    else:
        print(str(data)[:1200])


def dump_tasks(wf):
    print("  current_task:", (wf.get("current_task") or {}).get("number"),
          (wf.get("current_task") or {}).get("name"))
    print("  status:", wf.get("status"))
    for t in wf.get("tasks", []):
        print(f"    #{t.get('number'):>2} {t.get('status'):<12} {t.get('name')}")


def main():
    # 1) sanity: auth + base url
    s, d = P.get(f"/templates/{TEMPLATE}")
    print(f"[auth] GET /templates/{TEMPLATE} -> HTTP {s} "
          f"({d.get('name') if isinstance(d, dict) else d})")
    if s != 200:
        show("template fetch failed", s, d)
        return

    # 2) who am I (for the permission question)
    s, me = P.get("/accounts/users")
    if s == 200:
        users = me.get("results", me) if isinstance(me, dict) else me
        print(f"[users] {len(users)} users on instance")

    # 3) launch
    s, wf = P.post(f"/templates/{TEMPLATE}/run",
                   {"name": "API PROBE - delete me (AV Support)"})
    show("LAUNCH POST /templates/20/run", s, wf if s != 200 else
         {"id": wf.get("id"), "name": wf.get("name"), "status": wf.get("status")})
    if s not in (200, 201):
        return
    wid = wf.get("id")

    # 4) read workflow to find current task + task statuses BEFORE completing
    s, wf = P.get(f"/workflows/{wid}")
    print(f"\n[before] GET /workflows/{wid} -> HTTP {s}")
    if s == 200:
        dump_tasks(wf)
    cur = (wf.get("current_task") or {}) if s == 200 else {}
    task_id = cur.get("id")

    # 5) complete the Initiate Process task. Try the documented endpoint shape.
    body = {"task_id": task_id, "output": OUTPUT}
    s, d = P.post(f"/workflows/{wid}/task-complete", body)
    show(f"COMPLETE POST /workflows/{wid}/task-complete (task {task_id})", s, d)

    # 6) read workflow AFTER to see routing
    s, wf = P.get(f"/workflows/{wid}")
    print(f"\n[after] GET /workflows/{wid} -> HTTP {s}")
    if s == 200:
        dump_tasks(wf)
        active = [t["number"] for t in wf.get("tasks", [])
                  if t.get("status") in ("active", "running")]
        print(f"\n  EXPECTED active chain start: {EXPECTED_TASKS}")
        print(f"  OBSERVED active task(s):    {active}")

    # 7) permission test: try to complete the next (department-head) task
    cur = (wf.get("current_task") or {}) if s == 200 else {}
    nxt = cur.get("id")
    if nxt and nxt != task_id:
        s, d = P.post(f"/workflows/{wid}/task-complete",
                      {"task_id": nxt, "output": {}})
        show(f"DOWNSTREAM complete attempt (task {nxt}, #{cur.get('number')})", s, d)


if __name__ == "__main__":
    main()
