#!/usr/bin/env python3
"""Static wiring diagnostic for a template: for every approval task show
  - the profit center its skip_task gates on
  - the predecessor task its start_task waits on (resolved to a number)
  - its performer group + live member count
and flag anything suspicious (start predecessor not the prior task in the
same profit-center chain; performer group empty)."""
import json
import sys
import pneumatic as P

PC_FIELD = "field-c8dac7"


def load_groups():
    s, d = P.get("/accounts/groups")
    gs = d.get("results", d) if isinstance(d, dict) else d
    return {str(g["id"]): g for g in gs}


def diagnose(tid, groups):
    s, d = P.get(f"/templates/{tid}")
    tasks = d["tasks"]
    num = {t["api_name"]: t["number"] for t in tasks}
    bynum = {t["number"]: t for t in tasks}

    def skip_pc(t):
        for c in t.get("conditions", []):
            if c["action"] == "skip_task":
                for r in c["rules"]:
                    for p in r["predicates"]:
                        if p.get("field") == PC_FIELD:
                            return p.get("value")
        return None

    def start_pred(t):
        for c in t.get("conditions", []):
            if c["action"] == "start_task":
                for r in c["rules"]:
                    for p in r["predicates"]:
                        return num.get(p.get("field"))
        return None

    # group tasks by profit center
    chains = {}
    for t in tasks[1:]:
        chains.setdefault(skip_pc(t), []).append(t["number"])

    print(f"\n{'='*78}\nTEMPLATE {tid}: {d['name']}\n{'='*78}")
    for pc, nums in chains.items():
        nums.sort()
        print(f"\nPC {pc!r}  chain {nums}")
        prev_expected = 1  # first task in a chain should start after Initiate (1)
        for i, n in enumerate(nums):
            t = bynum[n]
            sp = start_pred(t)
            # performer group membership
            perf = ""
            for rp in t.get("raw_performers", []):
                if rp.get("type") == "group":
                    g = groups.get(str(rp.get("source_id")))
                    cnt = len(g.get("users", [])) if g else "??"
                    perf += f"group {rp.get('source_id')} '{rp.get('label')}' ({cnt} members)"
                else:
                    perf += f"{rp.get('type')} {rp.get('source_id')}"
            want = nums[i - 1] if i > 0 else 1
            flag = "" if sp == want else f"  <-- start waits on #{sp}, expected #{want}"
            empty = "  <-- EMPTY GROUP" if "(0 members)" in perf else ""
            print(f"   #{n:>2} {t['name']:<40} start_after=#{sp:<3} {perf}{flag}{empty}")


if __name__ == "__main__":
    groups = load_groups()
    for tid in (sys.argv[1:] or ["20", "7"]):
        diagnose_fn = diagnose if False else diagnose  # noqa
        diagnose(int(tid), groups)
