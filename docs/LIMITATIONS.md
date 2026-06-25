# Limitations

This is a **teaching project**. It is intentionally incomplete and intentionally
insecure in places. Read this before using any part of it as a reference.

## Known Limitations

- **No real database.** The service layer's `_execute_read`/`_execute_write`
  (`app/vitals.py`, `app/alerts.py`) are stubs that return canned values. Recording
  or querying vitals does **not** persist anything. Only `/health` (`app/health.py`)
  opens real Postgres/Redis connections.
- **Intentional vulnerabilities remain.** `app/vitals.py`, `app/auth.py`, and
  `app/alerts.py` ship deliberate flaws (SQL injection via f-strings, hardcoded
  credentials, MD5 password hashing, PII over-exposure, missing ward-boundary
  authorization). These are teaching targets — **do not treat the app as secure.**
- **Authentication is a stub.** `auth.login` validates against a hardcoded stub user,
  tokens are MD5 and never expire, and the session store (`TOKEN_STORE`) is in-memory
  — all sessions are lost on restart and cannot be shared across workers/replicas.
- **No rate limiting.** No endpoint (including `/health`) is rate-limited.
- **`/health` is liveness, not readiness.** It always returns HTTP 200 while the
  process is up; a 503 is never returned when dependencies are down (status is in the
  body only). See [TRADEOFFS.md](TRADEOFFS.md) #2.
- **Coverage tests document, not fix.** Several tests assert the buggy behavior
  (e.g. `value=None` raises) to reach the coverage gate without altering the app.

## Failure Modes

- **Dependency down:** `/health` reports `database: error` / `cache: error` (still 200).
  Other routes that "use" the DB still succeed because the DB layer is stubbed.
- **Missing/invalid token:** protected routes return `401 Unauthorized`.
- **Unknown `vital_type`:** `calculate_alert_threshold` raises `KeyError`; `record_vitals`
  swallows it (no alert) but still "writes".
- **`value=None`:** `record_vitals` crashes with `TypeError` (unhandled — documented).
- **CI security findings:** `bandit`/`pip-audit` flag the intentional issues; the job
  is advisory and does not block.

## Assumptions

- Local/lab use only. Collaborators are semi-trusted; the host running compose is trusted.
- `.env` holds local-only values and is never committed.
- The pinned base image and dependency versions are uncompromised at build time.

## When NOT to Use This Project

- As a template for a production health API — the persistence and auth layers are stubs.
- As an example of secure coding — the service modules are deliberately insecure.
- To store or process real patient data (PHI) — there is no real, secured datastore.

## Future Work

From the threat model and tradeoffs log (owner sign-off pending):

- Replace DB stubs with a parameterised, real persistence layer.
- Fix the intentional vulnerabilities; flip the CI security job to **blocking**.
- Split `/livez` (liveness) and `/readyz` (readiness); rate-limit `/health`.
- SHA-pin GitHub Actions; hash-pin Python deps; add container image CVE scanning.
- Add `docs/EVALUATION.md`, `docs/DEPLOYMENT.md`, and an architecture diagram image.
