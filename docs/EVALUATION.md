# Evaluation

How the Week 6 deliverables were validated, with the actual results observed during
the build. All figures below are measured, not estimated.

## Objective

Verify that the CI/CD pipeline, container image, and service stack meet the brief's
requirements and that `scripts/validate_ci.py` passes — without altering the app's
intentional teaching vulnerabilities.

## Test Suite — Unit/Integration Coverage

Command: `pytest --cov=app --cov-fail-under=90`

| Metric | Result |
|--------|--------|
| Tests | **45 passed** |
| Total coverage | **98.14%** (gate: 90%) |
| Test files | `tests/test_vitals.py`, `test_health.py`, `test_auth.py`, `test_alerts.py`, `test_routes.py` |

Per-module coverage (from `--cov-report=term-missing`):

| Module | Coverage |
|--------|----------|
| `app/__init__.py` | 100% |
| `app/auth.py` | 100% |
| `app/health.py` | 100% |
| `app/routes.py` | 100% |
| `app/vitals.py` | 100% |
| `app/alerts.py` | 87% (uncovered: `_execute_*`/`_send_sms`/`_get_alert` log-only stubs) |

Coverage categories exercised: happy path, edge (age boundaries, empty trends),
error/should-fail (`unknown vital_type → KeyError`, `value=None → TypeError`), and
auth/authz (401 no-token, 403 wrong-role). Tests **assert** the intentional bugs
rather than fixing them.

## Static Checks

| Check | Command | Result |
|-------|---------|--------|
| Lint | `ruff check app tests wsgi.py` | All checks passed |
| Deliverables | `python scripts/validate_ci.py` | **All checks passed** (exit 0), both bonuses detected |

## Container Image (Part 2)

| Metric | Result |
|--------|--------|
| Build | Succeeded (multi-stage) |
| Image size | **244MB disk / 58.4MB content** |
| User | non-root `appuser` (uid 10001) — verified `docker exec ht id` |
| HEALTHCHECK | reports **healthy** after start |
| Standalone `curl /health` | **HTTP 200**, body `{"status":"degraded","database":"error","cache":"error"}` (no deps, as expected) |

## Service Stack (Part 3)

| Check | Result |
|-------|--------|
| `docker compose up -d` | db + redis reach **Healthy** before api starts (ordering enforced) |
| `docker compose ps` | all three services **healthy** |
| db/redis host exposure | none — only `api` publishes `5000` (db/redis internal-only) |
| `curl /health` (stack up) | **HTTP 200**, body `{"status":"ok","database":"ok","cache":"ok"}` |
| `pytest` with stack running | 45 passed, 98% |

## CI Pipeline (Parts 1 & 4)

| Run | Result |
|-----|--------|
| Push to `main` | CI **success** — Lint ✅, Test ✅, Security ✅ |
| PR [#1](https://github.com/mwill20/HealthTrack-_API_AV/pull/1) | graded `ci.yml` **success** — all 3 jobs ✅ |

Note: the separate `ai-skill-review.yml` requires the `ANTHROPIC_API_KEY` repo secret;
it fails until the secret is added (expected, not a defect in the Week 6 pipeline).

## Baselines

- Coverage **before** this work: ~45% (3 tests). **After:** 98% (45 tests).
- `LICENSE`, `SECURITY.md`, threat model, architecture/limitations docs: absent before, present now.

## Reproducibility

```bash
python -m venv .venv && . .venv/Scripts/activate      # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
ruff check app tests wsgi.py
pytest --cov=app --cov-fail-under=90
python scripts/validate_ci.py        # set PYTHONUTF8=1 on Windows
docker build -t healthtrack:local . && docker images healthtrack:local
cp .env.example .env && docker compose up -d && curl http://localhost:5000/health
docker compose down
```

## Not Yet Measured

- Runtime performance, latency, throughput, and memory of the container under load.
- Behavior against a real (non-stub) database.
