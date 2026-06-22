#!/usr/bin/env python3
"""Profit-center x amount matrix path-tester for the yamaha-stage-2 Expense
Pre-Approval templates (20 = CAPEX, 7 = Non-CAPEX).

For every (template, profit center, amount tier) it:
  launch -> fill task #1 (Initiate Process) with that PC + amount and benign
  values for all other required fields -> drive the whole approval chain to
  completion, recording the ORDER in which approval tasks activate (the actual
  executed approver chain) -> delete the test workflow.

It does NOT decide pass/fail (template 7 legitimately skips higher tiers for
small amounts). It records what actually ran so you can compare to intent.
The full PC chain (all tasks gated to that profit center, ignoring amount) is
shown alongside, so amount-skipped tiers are obvious.

Usage (always via uv):
  uv run python run_matrix.py                 # both templates, 3 amount tiers
  uv run python run_matrix.py 20              # one template
  uv run python run_matrix.py --amounts 1000,4000,10000
  uv run python run_matrix.py --keep          # don't delete workflows
  uv run python run_matrix.py --workers 8     # concurrency (default 6)
"""
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import pneumatic as P
from build_map import build

PC_FIELD = "field-c8dac7"
AMOUNT_FIELD = "field-15c87b"
MAX_STEPS = 40


def find_missing_at_max(amounts, pcs, pc_chain, results):
    """A task that belongs to a profit-center chain but does NOT run even at
    the HIGHEST amount tested cannot be explained by amount tiering.
    Returns {task_number: profit_center} for the highest-amount run."""
    hi = max(amounts)
    miss = {}
    for pc in pcs:
        r = results.get((pc, hi))
        if not r or r.get("error"):
            continue
        for n in pc_chain.get(pc, []):
            if n not in r.get("ran", []):
                miss[n] = pc
    return miss


def starter_membership():
    """Return (starter_user_id, {group_id:set(member_ids)}, {group_id:name}).
    The starter is the API key's own user (workflow_starter on every launch);
    learn it from one throwaway workflow."""
    s, wf = P.post("/templates/20/run", {"name": "WHOAMI delete me"})
    wid = wf["id"]
    s, full = P.get(f"/workflows/{wid}")
    starter = full.get("workflow_starter")
    P.req("DELETE", f"/workflows/{wid}")
    s, d = P.get("/accounts/groups")
    gs = d.get("results", d) if isinstance(d, dict) else d
    gmem = {str(g["id"]): set(g.get("users", [])) for g in gs}
    gname = {str(g["id"]): g["name"] for g in gs}
    return starter, gmem, gname


def starter_tasks_for(tid, starter, gmem):
    """Task numbers whose performer group (or direct user) is the starter ->
    Pneumatic self-skips these (no self-approval), independent of amount."""
    s, t = P.get(f"/templates/{tid}")
    hits = {}
    for tk in t["tasks"]:
        if tk["number"] == 1:
            continue
        for rp in tk.get("raw_performers", []):
            if rp.get("type") == "group" and starter in gmem.get(str(rp.get("source_id")), set()):
                hits[tk["number"]] = str(rp.get("source_id"))
            elif rp.get("type") == "user" and str(rp.get("source_id")) == str(starter):
                hits[tk["number"]] = "direct"
    return hits


def make_output(fields, pc_value, amount):
    out = {}
    for f in fields:
        api, ftype = f["api_name"], f["type"]
        if api == PC_FIELD:
            out[api] = pc_value
        elif api == AMOUNT_FIELD:
            out[api] = amount
        elif ftype in ("dropdown", "radio"):
            sels = f.get("selections") or []
            if sels:
                out[api] = sels[0]["value"]
        elif ftype == "checkbox":
            sels = f.get("selections") or []
            if sels:
                out[api] = [sels[0]["value"]]
        elif ftype == "number":
            out[api] = 1
        elif ftype == "date":
            out[api] = time.time()
        else:
            out[api] = "Automated path test"
    return out


def drive(tid, pc_value, amount, fields, keep):
    """Run one workflow to completion; return the executed approver chain."""
    rec = {"profit_center": pc_value, "amount": amount, "ran": [], "error": None}
    s, wf = P.post(f"/templates/{tid}/run",
                   {"name": f"MATRIX t{tid} | {pc_value} | ${amount}"})
    if s not in (200, 201):
        rec["error"] = f"launch HTTP {s}: {str(wf)[:200]}"
        return rec
    wid = wf["id"]
    rec["workflow_id"] = wid
    try:
        s, wf = P.get(f"/workflows/{wid}")
        act = [t for t in wf["tasks"] if t["status"] == "active"]
        if not act or act[0]["number"] != 1:
            rec["error"] = "task#1 not active at start"
            return rec
        s, d = P.post(f"/workflows/{wid}/task-complete",
                      {"task_id": act[0]["id"],
                       "output": make_output(fields, pc_value, amount)})
        if s not in (200, 204):
            rec["error"] = f"initiate complete HTTP {s}: {str(d)[:200]}"
            return rec

        steps = 0
        order = []
        while steps < MAX_STEPS:
            s, wf = P.get(f"/workflows/{wid}")
            if wf.get("status") != 0:  # 0 = running
                break
            act = [t for t in wf["tasks"] if t["status"] == "active"]
            if not act:
                break
            for t in sorted(act, key=lambda x: x["number"]):
                order.append(t["number"])
                s, d = P.post(f"/workflows/{wid}/task-complete",
                              {"task_id": t["id"], "output": {}})
                if s not in (200, 204):
                    rec["error"] = f"complete #{t['number']} HTTP {s}: {str(d)[:200]}"
                    return rec
            steps += 1
        s, wf = P.get(f"/workflows/{wid}")
        rec["ran"] = order
        rec["final_status"] = wf.get("status")
        return rec
    finally:
        if not keep:
            P.req("DELETE", f"/workflows/{wid}")


def run_template(tid, amounts, keep, workers, starter, gmem):
    m = build(tid)
    fields = m["fields"]
    pc_chain = {pc: sorted(v) for pc, v in m["paths"].items()}
    names = {int(k): v for k, v in m["task_names"].items()}
    pcs = list(m["pc_selections"].keys())
    starter_tasks = starter_tasks_for(tid, starter, gmem)

    jobs = [(pc, amt) for pc in pcs for amt in amounts]
    print(f"\n{'='*78}\nTEMPLATE {tid}: {m['name']}  "
          f"({m['task_count']} tasks, {len(pcs)} profit centers x {len(amounts)} amounts "
          f"= {len(jobs)} runs)\n{'='*78}")

    results = {}
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(drive, tid, pc, amt, fields, keep): (pc, amt)
                for pc, amt in jobs}
        done = 0
        for fut in as_completed(futs):
            pc, amt = futs[fut]
            results[(pc, amt)] = fut.result()
            done += 1
            print(f"  ...{done}/{len(jobs)} done", end="\r")
    print(" " * 30, end="\r")

    missing = find_missing_at_max(amounts, pcs, pc_chain, results)
    # split: starter self-skips (expected) vs genuinely unexplained anomalies
    starter_skips = {n: pc for n, pc in missing.items() if n in starter_tasks}
    anomalies = {n: pc for n, pc in missing.items() if n not in starter_tasks}

    # console matrix
    for pc in pcs:
        full = pc_chain.get(pc, [])
        print(f"\n  {pc}   (PC chain: {full})")
        for amt in amounts:
            r = results[(pc, amt)]
            if r["error"]:
                print(f"     ${amt:<7} ERROR: {r['error']}")
                continue
            ran = r["ran"]
            skipped = [n for n in full if n not in ran]
            amt_skip = [n for n in skipped if n not in missing]
            stk = [n for n in skipped if n in starter_skips]
            anm = [n for n in skipped if n in anomalies]
            note = ""
            if amt_skip:
                note += f"  (amount-skipped tier: {amt_skip})"
            if stk:
                note += "  [starter self-skip: " + \
                    ", ".join(f"#{n}" for n in stk) + "]"
            if anm:
                note += "  [!! ANOMALY: " + \
                    ", ".join(f"#{n} {names.get(n,'')}" for n in anm) + "]"
            print(f"     ${amt:<7} ran {ran}{note}")

    if starter_skips:
        print(f"\n  i  Template {tid} starter self-skips (assigned to a group "
              f"containing the workflow starter -> Pneumatic skips, expected): " +
              ", ".join(f"#{n} {names.get(n,'')}" for n in sorted(starter_skips)))
    if anomalies:
        print(f"\n  !! Template {tid} TRUE ANOMALIES (skipped at ${max(amounts)}, "
              f"not starter, not amount): " +
              ", ".join(f"#{n} {names.get(n,'')} ({pc})"
                        for n, pc in sorted(anomalies.items())))

    report = {"template_id": tid, "name": m["name"], "amounts": amounts,
              "task_names": names, "pc_chain": pc_chain,
              "results": {f"{pc} @ {amt}": results[(pc, amt)]
                          for pc in pcs for amt in amounts}}
    report["starter_skips"] = {str(n): {"name": names.get(n, ""), "profit_center": pc,
                                        "group": starter_tasks.get(n)}
                               for n, pc in starter_skips.items()}
    report["anomalies"] = {str(n): {"name": names.get(n, ""), "profit_center": pc}
                           for n, pc in anomalies.items()}
    json.dump(report, open(f"matrix_t{tid}.json", "w"), indent=1)
    print(f"\n  -> wrote matrix_t{tid}.json")
    return tid, m, amounts, pcs, pc_chain, names, results, anomalies, starter_skips


def write_markdown(runs, starter, starter_email):
    lines = ["# Path-test matrix — Expense Pre-Approval templates",
             "",
             "Each cell lists the approval tasks that **actually executed** "
             "(in activation order) for that profit center + amount.",
             "",
             f"> Test workflows are started by **{starter_email}** (user {starter}, "
             "the API key's user). Pneumatic skips any task assigned to the workflow "
             "starter (no self-approval), so steps whose approver group includes this "
             "user self-skip regardless of amount — marked `ⓢ`. `⚠️` marks a task "
             "skipped for no reason found in the API (a real issue to check in the UI).",
             ""]
    for tid, m, amounts, pcs, pc_chain, names, results, anom, stkip in runs:
        lines.append(f"## Template {tid}: {m['name']}")
        lines.append("")
        if stkip:
            lines.append("**ⓢ Starter self-skips** (assigned to a group containing the "
                         f"workflow starter {starter_email} → Pneumatic skips them; they "
                         "would run for a different initiator, so they can't be validated "
                         "through this API key):")
            for n, pc in sorted(stkip.items()):
                lines.append(f"- #{n} {names.get(n,'')} — under profit center `{pc}`")
            lines.append("")
        if anom:
            lines.append("**⚠️ True anomalies** (skipped even at the highest amount, NOT a "
                         "starter self-skip and NOT amount tiering — check in the UI):")
            for n, pc in sorted(anom.items()):
                lines.append(f"- #{n} {names.get(n,'')} — under profit center `{pc}`")
            lines.append("")
        if not stkip and not anom:
            lines.append("_All paths execute their full chain at a sufficient amount._")
            lines.append("")
        hdr = "| Profit Center | Full PC chain | " + \
            " | ".join(f"${a}" for a in amounts) + " |"
        lines.append(hdr)
        lines.append("|" + "---|" * (2 + len(amounts)))
        for pc in pcs:
            full = pc_chain.get(pc, [])
            cells = []
            for amt in amounts:
                r = results[(pc, amt)]
                if r["error"]:
                    cells.append("ERROR")
                    continue
                ran = r["ran"]
                skipped = [n for n in full if n not in ran]
                cell = f"{ran}"
                if any(n in stkip for n in skipped):
                    cell += " ⓢ"
                if any(n in anom for n in skipped):
                    cell += " ⚠️"
                cells.append(cell)
            lines.append(f"| {pc} | {full} | " + " | ".join(cells) + " |")
        lines.append("")
        # legend of task numbers -> names for this template
        lines.append("<details><summary>task number → name</summary>")
        lines.append("")
        for n in sorted(names):
            lines.append(f"- #{n} {names[n]}")
        lines.append("")
        lines.append("</details>")
        lines.append("")
    open("REPORT.md", "w").write("\n".join(lines))
    print("\n-> wrote REPORT.md")


def report_only(tids, starter, gmem, gname, starter_email):
    """Rebuild REPORT.md from saved matrix_t*.json (no workflows launched)."""
    runs = []
    for tid in tids:
        d = json.load(open(f"matrix_t{tid}.json"))
        amounts = d["amounts"]
        names = {int(k): v for k, v in d["task_names"].items()}
        pc_chain = {k: v for k, v in d["pc_chain"].items()}
        pcs = list(pc_chain.keys())
        results = {}
        for key, rec in d["results"].items():
            pc, amt = key.rsplit(" @ ", 1)
            results[(pc, int(amt))] = rec
        starter_tasks = starter_tasks_for(tid, starter, gmem)
        missing = find_missing_at_max(amounts, pcs, pc_chain, results)
        stkip = {n: pc for n, pc in missing.items() if n in starter_tasks}
        anom = {n: pc for n, pc in missing.items() if n not in starter_tasks}
        m = {"name": d["name"], "task_count": len(names)}
        runs.append((tid, m, amounts, pcs, pc_chain, names, results, anom, stkip))
    write_markdown(runs, starter, starter_email)
    print("DONE (report-only). See REPORT.md.")


def main():
    argv = sys.argv[1:]
    keep = "--keep" in argv
    amounts = [1000, 4000, 10000]
    if "--amounts" in argv:
        amounts = [int(x) for x in argv[argv.index("--amounts") + 1].split(",")]
    workers = 6
    if "--workers" in argv:
        workers = int(argv[argv.index("--workers") + 1])
    tids = [int(a) for a in argv if a.isdigit()] or [20, 7]

    starter, gmem, gname = starter_membership()
    s, d = P.get("/accounts/users")
    us = d.get("results", d) if isinstance(d, dict) else d
    starter_email = next((u.get("email") for u in us if u.get("id") == starter), str(starter))
    print(f"workflow starter = {starter_email} (user {starter})")

    if "--report-only" in argv:
        report_only(tids, starter, gmem, gname, starter_email)
        return

    runs = [run_template(tid, amounts, keep, workers, starter, gmem) for tid in tids]
    write_markdown(runs, starter, starter_email)
    print("\nDONE. See REPORT.md for the readable matrix.")


if __name__ == "__main__":
    main()
