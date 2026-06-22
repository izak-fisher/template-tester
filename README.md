# template-tester

Automated path-testing of the Pneumatic **Expense Pre-Approval** templates on
`yamaha-stage-2.pneumatic.app` via the public API. It launches real workflows,
fills the **Initiate Process** step, drives every approval task to completion,
and records which approval chain actually executed for each
**profit center × amount** combination — so you can confirm every routing path
works as intended.

## Setup

Copy `.env.example` to `.env` and set your Pneumatic API key (the `.env` file is
gitignored):

```bash
cp .env.example .env
# then edit .env and set PNEUMATIC_API_KEY=<your key>
```

No third-party packages, but run everything through **uv**:

```bash
uv run python run_matrix.py            # both templates (20 + 7), amounts 1k/4k/10k
```

`PNEUMATIC_API_KEY` is required; `PNEUMATIC_BASE_URL` is optional (defaults to the
yamaha-stage-2 `:8001` endpoint). The key is read from `.env` next to the scripts.

## Main entrypoint: `run_matrix.py`

For each (template, profit center, amount) it: launches a workflow → completes
task #1 with that profit center + amount (all other required fields auto-filled
with benign values) → completes each approval task in sequence → records the
executed chain → **deletes** the test workflow.

```bash
uv run python run_matrix.py 20                 # one template
uv run python run_matrix.py --amounts 1000,4000,10000
uv run python run_matrix.py --keep             # leave workflows on the instance
uv run python run_matrix.py --workers 8        # concurrency (default 6)
```

Outputs:
- **`REPORT.md`** — readable matrix: profit center × amount → executed approval
  tasks, with ⚠️ on tasks skipped even at the highest amount (unexplained by
  amount tiering → likely a template bug; verify in the Pneumatic UI).
- `matrix_t<id>.json` — full machine-readable results.

It does **not** hard-code a pass/fail (template 7 legitimately skips higher
approval tiers for small amounts). It records what actually ran; you compare to
intent. A task missing from a chain **even at the highest amount** is the signal
for a genuine problem.

## How routing works (what we learned)

- Task **#1 "Initiate Process"** holds the kick-off fields (the template's
  `kickoff` form is empty). **Profit/Cost Center** (`field-c8dac7`, 24 options)
  selects the department approval sub-chain.
- **Template 20 (CAPEX):** profit center is the only router; the full chain runs
  regardless of amount.
- **Template 7 (Non-CAPEX):** ALSO gated by **Estimated Total Cost**
  (`field-15c87b`) — higher approval tiers are skipped for small amounts
  (~$3k and ~$6k thresholds). This is by design.
- **Starter self-skip (both templates):** `#14 Director Approval CMP` and
  `#64 Director Approval AV-Speciality` never run, even at $10k — **not a bug**.
  Pneumatic skips any task assigned to the `workflow_starter` (no self-approval),
  and the API key's user (`isaiah.fisher@pneumatic.app`, user 1) is a member of
  both those approver groups. Across both templates, the tasks whose group
  contains the starter are exactly {14, 64} — exactly the skipped tasks. These
  two paths can't be validated through this key (they'd run for a different
  initiator); the report marks them `ⓢ`. Everything else routes correctly.

The report separates three cases: `ⓢ` starter self-skip (expected), amount-tier
skip (expected, template 7 only), and `⚠️` true anomaly (none currently found).

## Supporting scripts

- `pneumatic.py` — tiny stdlib API client (auth, GET/POST/DELETE).
- `build_map.py` — fetches a live template and derives the profit-center → tasks
  map + task-1 field list (`pc_map_<id>.json`). Run: `uv run python build_map.py`.
- `diagnose.py` — static wiring dump (per task: skip profit center, start
  predecessor, performer group + member count). Run: `uv run python diagnose.py 20`.
- `probe.py`, `complete_probe.py`, `inspect_wf.py`, `run_tests.py` — the
  step-by-step viability probes used to reverse-engineer the API (kept for
  reference).

## API notes

See the `pneumatic-run-api` memory for the full quirk list. Highlights:
`POST /templates/{id}/run` to launch; `POST /workflows/{id}/task-complete`
(`{task_id, output}`, returns 204) to complete — dropdown outputs take the
selection **value string**, not its api_name; `current_task` is always null
(read the active task from `tasks[]`); skipped branches are pruned after task 1;
`DELETE /workflows/{id}` to clean up.
