# template-tester

A small harness for exercising [Pneumatic](https://pneumatic.app) workflow templates through the
public API — launching real workflows, driving each task to completion **as the user actually
assigned to it**, and checking that a template routes and gates the way it is supposed to.

Built against a self-hosted Pneumatic instance (public API on port `8001`, web client on `443`).

> This repo contains the **generic harness only**. Customer-specific scenarios, findings, reports
> and screenshots are deliberately gitignored — see `.gitignore`.

## Setup

```bash
cp .env.example .env      # then set PNEUMATIC_API_KEY=<your key>
```

No third-party packages for the API layer; the GUI layer needs Playwright. Run everything through
**uv**, from inside this directory (so `import pneumatic` / `import roles` resolve):

```bash
uv run python your_script.py
uv run --with playwright python _gui.py
```

`PNEUMATIC_API_KEY` is required. `PNEUMATIC_BASE_URL` overrides the instance; set it to point the
same scripts at another deployment without touching `.env`:

```bash
PNEUMATIC_BASE_URL='https://<instance>:8001' PNEUMATIC_API_KEY='<key>' uv run python ...
```

## What's here

- **`pneumatic.py`** — dependency-free API client. `get()`, `post()`, `req(method, path, body)`.
  Returns `(status, parsed_json)` and never raises on an HTTP error, so probing is cheap.
  Reads `.env` next to the file; real env vars win.

- **`roles.py`** — multi-user support. An account owner can retrieve **every** user's API token
  (`GET /accounts/users/api-key`, joined to `/accounts/users` by email — the response carries no
  `id`). `build()` returns `{users, tok, name2id, id2name}`; `call(uid, method, path, body, R)` and
  `complete_as(uid, wid, task_id, output, R)` then act **as that user**. A Pneumatic token *is* a
  user identity, which is what makes realistic multi-approver testing possible.
  **These are full per-user credentials — keep them in memory, never write them to disk.**

- **`_gui.py`** — Playwright helpers: `login(page)` and `shot(page, name)` → `_shots/`. The web
  client does **not** accept an API key: it authenticates with a session token from
  `POST /api/auth/token/obtain` (port 443, `{"username", "password"}`, sent as
  `Authorization: Token <t>`), so GUI automation needs a real password. Credentials come from
  `PNEU_GUI_EMAIL` / `PNEU_GUI_PASSWORD` and are never written to disk.

- **`_t69.py`** — helpers for a disposable sandbox template used to test
  `require_completion_by_all` behaviour: swap step-1 performers, start, inspect, clean up. Point
  `BASE` at your own throwaway template.

- **`build_map.py`**, `diagnose.py`, `inspect_wf.py`, `probe.py`, `complete_probe.py`,
  `run_tests.py`, `run_matrix.py` — supporting tools for mapping a template's routing, dumping its
  static wiring, and sweeping a matrix of kickoff values. They expect a template whose field
  layout you supply.

## API notes worth knowing

Learned the hard way; they apply to any instance:

- `POST /templates/{id}/run` launches; `POST /workflows/{id}/task-complete` (`{task_id, output}` →
  204) completes. Dropdown outputs take the selection **value string**, not its `api_name`.
- `current_task` is always null — read the active task from `tasks[]`. Skipped branches are pruned
  after task 1.
- **Read `require_completion_by_all` from the TEMPLATE, not the workflow** — the workflow task JSON
  returns `None` for it.
- Templates round-trip: `GET` → modify → `PUT /templates/{id}` is byte-identical apart from
  `date_updated`. No-op PUT first to validate.
- Datasets: `PATCH /datasets/{id}` takes **`{"items": [...]}` only** — sending the full object
  (with `id`, `date_created_tsp`) returns 500. New items omit `id`.
- Task lists (the "My Tasks" view) are
  `GET /v3/tasks?limit=&offset=&is_completed=<bool>&assigned_to=<uid>&ordering=date`. **Page through
  it** — a bare `limit=100` silently drops recent tasks for busy users and invents phantom
  asymmetries between them.
- **Starter self-skip:** Pneumatic skips any task assigned to the workflow starter (no
  self-approval). If your API key's user is a member of an approver group, those steps will never
  run for workflows that user starts — pick a *clean starter* who performs nowhere in the template.
- `DELETE /workflows/{id}` to clean up. Workflow IDs are a global auto-increment counter.

## Conventions

- Everything runs against a **staging/test** instance. Back up any object before mutating it, and
  restore it afterwards.
- Test workflows are deleted after each run.
