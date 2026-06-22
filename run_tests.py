#!/usr/bin/env python3
"""Automated path-testing of Pneumatic templates on yamaha-stage-2.

For every Profit/Cost Center option in a template, this:
  1. launches a workflow from the template
  2. completes task #1 ("Initiate Process") with all required fields filled,
     setting Profit/Cost Center = the option under test
  3. reads the workflow: the engine has pruned skipped tasks, so the remaining
     tasks are the realized "path"
  4. (default) completes the whole chain in sequence, recording the order in
     which tasks activate and confirming the workflow reaches completion
  5. compares the realized path to the expected path derived from the
     template's skip_task conditions, and reports PASS/FAIL
  6. deletes the test workflow (unless --keep)

Usage (always via uv):
  uv run python run_tests.py                # both templates (20, 7), full run
  uv run python run_tests.py 20             # one template
  uv run python run_tests.py --verify-only  # don't complete the chain
  uv run python run_tests.py --keep         # leave workflows on the instance
  uv run python run_tests.py --pc "10171 IT"  # single profit center
"""
import json
import sys
import time
import pneumatic as P
from build_map import build

PC_FIELD = "field-c8dac7"
MAX_STEPS = 30  # safety cap on chain length


def make_output(fields, pc_value):
    """Build a valid task-1 output: PC = value under test; every other
    required field filled with a benign, type-appropriate value."""
    out = {}
    for f in fields:
        api, ftype = f["api_name"], f["type"]
        if api == PC_FIELD:
            out[api] = pc_value
        elif ftype in ("dropdown", "radio"):
            sels = f.get("selections") or []
            if sels:
                out[api] = sels[0]["value"]
        elif ftype == "checkbox":
            sels = f.get("selections") or []
            if sels:
                out[api] = [sels[0]["value"]]
        elif ftype == "number":
            out[api] = 1000
        elif ftype in ("date",):
            out[api] = time.time()  # not used by these templates
        else:  # string, text, url, etc.
            out[api] = "Automated path test"
    return out


def active_tasks(wf):
    return [t for t in wf["tasks"] if t.get("status") == "active"]


def run_one(tid, pc_value, fields, expected, task_names, full, keep):
    label = f"{pc_value}"
    res = {"profit_center": pc_value, "expected": expected, "ok": False}

    s, wf = P.post(f"/templates/{tid}/run",
                   {"name": f"PATH TEST t{tid} | {pc_value}"})
    if s not in (200, 201):
        res["error"] = f"launch HTTP {s}: {wf}"
        return res
    wid = wf["id"]
    res["workflow_id"] = wid

    try:
        s, wf = P.get(f"/workflows/{wid}")
        act = active_tasks(wf)
        if not act or act[0]["number"] != 1:
            res["error"] = f"task1 not active: {[(t['number'],t['status']) for t in act]}"
            return res

        # complete the Initiate Process task with the profit center under test
        s, d = P.post(f"/workflows/{wid}/task-complete",
                      {"task_id": act[0]["id"], "output": make_output(fields, pc_value)})
        if s not in (200, 204):
            res["error"] = f"initiate complete HTTP {s}: {d}"
            return res

        # read realized path (skipped tasks are pruned by the engine)
        s, wf = P.get(f"/workflows/{wid}")
        realized = sorted(t["number"] for t in wf["tasks"] if t["number"] != 1)
        res["realized"] = realized

        activation_order = []
        if full:
            steps = 0
            while steps < MAX_STEPS:
                s, wf = P.get(f"/workflows/{wid}")
                if wf.get("status") not in (0,):  # 0 = running
                    break
                act = active_tasks(wf)
                if not act:
                    break
                for t in sorted(act, key=lambda x: x["number"]):
                    activation_order.append(t["number"])
                    s, d = P.post(f"/workflows/{wid}/task-complete",
                                  {"task_id": t["id"], "output": {}})
                    if s not in (200, 204):
                        res["error"] = f"complete #{t['number']} HTTP {s}: {d}"
                        return res
                steps += 1
            s, wf = P.get(f"/workflows/{wid}")
            res["final_status"] = wf.get("status")
            res["activation_order"] = activation_order

        # verdict
        res["path_match"] = realized == sorted(expected)
        seq_ok = (not full) or activation_order == sorted(expected)
        done_ok = (not full) or res.get("final_status") == 1
        res["seq_ok"] = seq_ok
        res["done_ok"] = done_ok
        res["ok"] = res["path_match"] and seq_ok and done_ok
        return res
    finally:
        if not keep:
            P.req("DELETE", f"/workflows/{wid}")


def run_template(tid, only_pc, full, keep):
    m = build(tid)  # fresh live map (also writes pc_map_<id>.json)
    fields = m["fields"]
    paths = m["paths"]
    sel_to_val = {v: k for k, v in m["pc_selections"].items()}  # unused; clarity

    print(f"\n{'='*72}\nTESTING template {tid}: {m['name']}  "
          f"({m['task_count']} tasks, {len(m['pc_selections'])} profit centers)\n{'='*72}")
    results = []
    items = [only_pc] if only_pc else list(m["pc_selections"].keys())
    for pc in items:
        expected = paths.get(pc, [])
        r = run_one(tid, pc, fields, expected, m["task_names"], full, keep)
        results.append(r)
        mark = "PASS" if r["ok"] else "FAIL"
        extra = ""
        if not r["ok"]:
            if "error" in r:
                extra = f"  ERROR: {r['error']}"
            else:
                extra = (f"  expected={sorted(expected)} realized={r.get('realized')}"
                         f" order={r.get('activation_order')} final={r.get('final_status')}")
        print(f"  [{mark}] {pc:<40} -> {sorted(expected)}{extra}")
    npass = sum(1 for r in results if r["ok"])
    print(f"\n  template {tid}: {npass}/{len(results)} paths PASS")
    report = {"template_id": tid, "name": m["name"], "pass": npass,
              "total": len(results), "results": results}
    json.dump(report, open(f"report_t{tid}.json", "w"), indent=1)
    print(f"  -> wrote report_t{tid}.json")
    return report


def main():
    argv = sys.argv[1:]
    full = "--verify-only" not in argv
    keep = "--keep" in argv
    only_pc = None
    if "--pc" in argv:
        only_pc = argv[argv.index("--pc") + 1]
    tids = [a for a in argv if a.isdigit()] or ["20", "7"]

    grand = []
    for tid in tids:
        grand.append(run_template(int(tid), only_pc, full, keep))

    print(f"\n{'#'*72}\nSUMMARY")
    for g in grand:
        print(f"  template {g['template_id']} ({g['name']}): "
              f"{g['pass']}/{g['total']} PASS")
    failures = [(g["template_id"], r["profit_center"])
                for g in grand for r in g["results"] if not r["ok"]]
    if failures:
        print("\n  FAILURES:")
        for tid, pc in failures:
            print(f"    t{tid}: {pc}")
    else:
        print("\n  All paths PASS.")


if __name__ == "__main__":
    main()
