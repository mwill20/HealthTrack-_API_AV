# AGENTS.md — Instructions for AI Coding Assistants

Guidance for Codex, Claude, and other AI agents working in this repository.
Read this and `CLAUDE.md` before making changes.

## What this project is

HealthTrack API is a **teaching project** — a Flask patient-vitals REST API. The HTTP
and service layers are real; the database access functions are **stubs**; and the
service modules contain **intentional vulnerabilities** for security training.
Week 6 added a CI/CD pipeline and Docker containerisation.

## Hard rules

1. **Do NOT fix the intentional vulnerabilities** in `app/vitals.py`, `app/auth.py`,
   or `app/alerts.py` (SQL injection, hardcoded creds, MD5, PII exposure, missing
   authz). They are deliberate teaching targets. See [docs/LIMITATIONS.md](docs/LIMITATIONS.md).
2. **Never commit secrets.** `.env` is gitignored; only `.env.example` (placeholders)
   is committed. Credentials come from env vars / GitHub secrets at runtime.
3. **No `.env` in the Docker image.** Secrets are injected at runtime, never baked in.
4. **No commit or push without explicit instruction.**
5. **Keep the security scan honest.** The CI `security` job is advisory because of the
   intentional vulns — do not silence findings beyond the documented `--exit-zero`.

## Project layout

- `app/` — Flask app (`__init__.py` factory, `routes.py`, `vitals.py`, `auth.py`, `alerts.py`, `health.py`)
- `wsgi.py` — gunicorn entrypoint (`wsgi:app`)
- `tests/` — pytest suite (+ `conftest.py` at root)
- `.github/workflows/ci.yml` — lint → test → advisory security (the graded pipeline)
- `.github/workflows/ai-skill-review.yml` — AI PR-review Skills (needs `ANTHROPIC_API_KEY`)
- `docs/` — architecture, limitations, tradeoffs, threat model, brief, submission notes
- `scripts/validate_ci.py` — the deliverable checker (the spec)

## Coding standards (from CLAUDE.md)

- Python 3.11+; type hints on public functions; docstrings on public functions.
- In **new** code: parameterised SQL only, secrets via `os.getenv`, no PII/credentials in logs.
- Pin dependency versions exactly. Runtime deps in `requirements.txt`; test tooling in `requirements-dev.txt`.
- Lint is correctness-only (`ruff` `E`+`F`, see `ruff.toml`) — don't reformat the frozen teaching modules.

## How to validate changes

```bash
pip install -r requirements-dev.txt
ruff check app tests wsgi.py
pytest --cov=app --cov-fail-under=90        # keep coverage >= 90%
python scripts/validate_ci.py               # set PYTHONUTF8=1 on Windows
```

For Docker changes: `docker build -t healthtrack:local .` then `docker compose up -d`
and confirm `curl http://localhost:5000/health` returns 200.

## Record your tradeoffs

Any change involving a real tradeoff gets a new row in [docs/TRADEOFFS.md](docs/TRADEOFFS.md).
New trust boundaries trigger a threat-model update under `docs/threat-models/`.

## Repo-local skills

`.claude/skills/` defines `pr-review`, `security-audit`, and `test-coverage` skills
(run via `python plugins/run_skill.py`). Use them when reviewing changes to `app/`.
