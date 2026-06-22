#!/usr/bin/env python3
"""Minimal stdlib-only Pneumatic API client for the yamaha-stage-2 instance.

Reuses the auth/transport pattern from ../../move-templates/move_templates.py.
The self-hosted API lives on the subdomain at port 8001 over https.
"""
import json
import os
import urllib.request
import urllib.error

BASE = "https://yamaha-stage-2.pneumatic.app:8001"


def _load_dotenv(path):
    if not os.path.exists(path):
        return
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


# Load a local .env (next to this file) if present. See .env.example.
_load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
API_KEY = os.environ.get("PNEUMATIC_API_KEY")
BASE = os.environ.get("PNEUMATIC_BASE_URL", BASE)


def req(method, path, body=None):
    """Return (status, parsed_json_or_text). Never raises on HTTP error."""
    if not API_KEY:
        raise SystemExit("Missing PNEUMATIC_API_KEY. Copy .env.example to .env "
                         "and set PNEUMATIC_API_KEY=<your key>.")
    url = path if path.startswith("http") else BASE + path
    headers = {"Authorization": f"Bearer {API_KEY}"}
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    r = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=60) as resp:
            txt = resp.read().decode()
            return resp.status, (json.loads(txt) if txt else None)
    except urllib.error.HTTPError as e:
        txt = e.read().decode()
        try:
            return e.code, json.loads(txt)
        except Exception:
            return e.code, txt


def get(path):
    return req("GET", path)


def post(path, body):
    return req("POST", path, body)
