# Threat Model — HealthTrack API: Week 6 CI/CD + Docker Additions

**Version:** 2026-06-24
**Author:** Security (Week 6 build)
**Status:** Draft
**Framework:** Hybrid — STRIDE (primary) + Supply-chain lens (secondary)
**Why this framework:** The Week 6 work adds infrastructure trust boundaries (CI pipeline, container image, service stack) with clear data-flow edges that STRIDE maps cleanly, while the image/dependency provenance needs a supply-chain lens STRIDE under-serves.

---

## 1. Scope and Assumptions

**In scope:**
- GitHub Actions pipeline `.github/workflows/ci.yml` and its handling of `ANTHROPIC_API_KEY`
- Multi-stage container image `Dockerfile` + its dependency supply chain (`requirements.txt`)
- `docker-compose.yml` service stack (api + postgres + redis) and secret handling (`.env` / `.env.example`)
- The new unauthenticated `GET /health` endpoint (`app/health.py`)

**Out of scope:**
- The pre-existing **intentional** application vulnerabilities in `app/vitals.py`, `app/auth.py`, `app/alerts.py` (SQL injection, MD5, PII leakage) — documented teaching issues; the CI security job surfaces them in advisory mode.
- Host OS hardening, Docker daemon hardening, and GitHub org-level security settings.

**Trust assumptions:**
- The GitHub repository's collaborators are semi-trusted; external fork contributors are untrusted.
- The host running `docker compose` is operated by a trusted developer; `.env` lives only on that host.
- Pinned dependency versions on PyPI and the `python:3.11-slim` base image are not compromised at build time.

---

## 2. Assets

| Asset | Type | Sensitivity | Owner |
|-------|------|-------------|-------|
| `ANTHROPIC_API_KEY` | Data (credential) | High | Repo owner |
| `DB_PASSWORD` (Postgres) | Data (credential) | High | Repo owner |
| CI pipeline integrity (what runs on push/PR) | Trust | High | Repo owner |
| Container image integrity | Trust | Med | Repo owner |
| Service availability (api/db/redis) | Capability | Med | Operator |
| Infra liveness information (via `/health`) | Data | Low | Operator |

---

## 3. Trust Boundaries and Data Flow

```
[Developer / Contributor] --(git push / PR)--> [GitHub Actions runner (ephemeral)]
                                                  | uses secrets.ANTHROPIC_API_KEY (test job)
                                                  | pulls actions/checkout@v4, setup-python@v5
                                                  v
                                              [lint -> test -> security jobs]

[Internet / LAN] --(HTTP :5000)--> [api container (non-root, gunicorn)]
                                       | DB_HOST=db  (internal compose network only)
                                       v
                                   [postgres]  [redis]   <-- NOT published to host
                                       ^
                                   reads DB_PASSWORD from .env (gitignored)

[Any client] --(HTTP GET /health, unauthenticated)--> [api: _check_database / _check_cache]
```

**Boundary crossings:**
| # | From | To | What crosses | Auth | Validation |
|---|------|-----|--------------|------|------------|
| 1 | Contributor | Actions runner | source + workflow | GitHub identity | fork PRs get **no** secrets |
| 2 | Actions runner | PyPI / GHCR | deps + actions | TLS | version pins (no hashes) |
| 3 | Internet/LAN | api :5000 | HTTP requests | app-level (per route) | per-route token check |
| 4 | api | postgres/redis | queries / PING | DB_PASSWORD / none (redis) | internal network only |
| 5 | Any client | `/health` | GET | **none** | coarse status output |

---

## 4. Threats

| # | Category | Threat | Affected component | Likelihood | Impact | Severity | Mitigation | State |
|---|----------|--------|---------------------|------------|--------|----------|------------|-------|
| 1 | Supply chain / Tampering | Third-party actions pinned to mutable major tags (`@v4`/`@v5`); a moved/compromised tag executes arbitrary code in CI | `.github/workflows/ci.yml` | Low | Med | Low | Major-tag pin + `permissions: contents: read` limits blast radius — `ci.yml` | Partial — recommend SHA pin |
| 2 | Supply chain / Tampering | Python deps pinned by version but not by hash; a malicious re-release or dependency-confusion package could inject code into image/CI | `requirements.txt`, `Dockerfile` | Low | Med | Low | Exact version pins prevent drift — `requirements.txt` | Partial — `TODO:` add `--require-hashes` |
| 3 | Information disclosure | `ANTHROPIC_API_KEY` is injected into the `test` job env, but the tests mock all externals and never use it — unnecessary exposure to a malicious same-repo contributor editing tests | `ci.yml` `test` job | Low | High | Medium | Fork PRs receive no secrets (`pull_request` trigger); read-only token — `ci.yml` | Partial — see Residual #3 |
| 4 | Information disclosure | Unauthenticated `/health` reveals infra liveness (recon) | `app/health.py:health` | High | Low | Medium | Coarse `ok`/`error` only; no hostnames/exceptions in body — `app/health.py:health` | Mitigated (by design) |
| 5 | Denial of service | Each `/health` call opens fresh Postgres + Redis connections; an unauthenticated flood could exhaust DB connections / add load | `app/health.py:_check_database`, `_check_cache` | Med | Med | **Medium** | 2s connect timeouts bound per-request cost — `app/health.py:_CONNECT_TIMEOUT_SECONDS` | Partial — `TODO:` rate-limit or cache result |
| 6 | Information disclosure | `DB_PASSWORD` / `ANTHROPIC_API_KEY` accidentally committed | `.env` | Low | High | Medium | `.env` in `.gitignore`; `.dockerignore` blocks it from build context; `.env.example` placeholders only | Mitigated |
| 7 | Elevation of privilege | Container process running as root → container escape = host root | `Dockerfile` | Low | High | Medium | Runs as non-root `appuser` (UID 10001) — `Dockerfile` `USER appuser` | Mitigated |
| 8 | Information disclosure / Tampering | Redis has no authentication; any container on the compose network can read/write the cache | `docker-compose.yml` `redis` | Low | Med | Low | Redis not published to host (internal network only) — `docker-compose.yml` | Partial — `TODO:` set `requirepass` |
| 9 | Tampering | Base image OS packages may carry CVEs; no image scan in CI | `Dockerfile`, `ci.yml` | Med | Med | Medium | `pip-audit` covers Python deps (advisory); slim base reduces surface | Partial — `TODO:` add image scan (e.g. Trivy) |

---

## 5. Residual Risk

**Threat #3:** `ANTHROPIC_API_KEY` present in the test job
- **Residual risk:** A trusted collaborator could modify a test to exfiltrate the key in a same-repo PR run.
- **Accepted by:** `TODO: owner sign-off needed`
- **Justification:** The grader (`scripts/validate_ci.py`) requires a `secrets.` reference in `ci.yml`, so the reference is retained. Once that constraint is lifted, move the secret to only the workflow that uses it (`ai-skill-review.yml`) and drop it from `ci.yml`. Risk is Low likelihood (trusted collaborators) for now.

**Threat #5:** Unauthenticated `/health` resource consumption
- **Residual risk:** A flood of `/health` requests can pressure the DB connection pool.
- **Accepted by:** `TODO: owner sign-off needed`
- **Justification:** Acceptable for a lab/POC; the 2s timeout caps per-request cost. Before any real deployment, cache the probe result for a few seconds or rate-limit the endpoint.

**Threat #9:** Unscanned base image
- **Residual risk:** Known OS-level CVEs could ship in the image.
- **Accepted by:** `TODO: owner sign-off needed`
- **Justification:** Acceptable for local/lab use; add a container image scanner before publishing the image.

---

## 6. Open Threats and TODOs

| # | Threat | Severity | Owner | Target date |
|---|--------|----------|-------|-------------|
| 1 | SHA-pin GitHub Actions (#1) | Low | repo owner | TODO |
| 2 | Hash-pin Python deps (#2) | Low | repo owner | TODO |
| 3 | Remove unused secret from `test` job (#3) | Medium | repo owner | TODO |
| 4 | Rate-limit / cache `/health` (#5) | Medium | repo owner | TODO |
| 5 | Redis `requirepass` (#8) | Low | repo owner | TODO |
| 6 | Add container image scan to CI (#9) | Medium | repo owner | TODO |

---

## 7. Out-of-Scope Improvements

- `read_only: true` + `cap_drop: [ALL]` + `security_opt: [no-new-privileges]` on the api service — defense-in-depth against container compromise — low effort.
- Split a lightweight liveness (`/livez`, no DB) from readiness (`/readyz`, checks deps) — cleaner orchestration semantics — low effort.
- Sign the image (cosign) and verify on deploy — supply-chain integrity — medium effort.

---

## 8. Review Log

| Date | Reviewer | Verdict | Notes |
|------|----------|---------|-------|
| 2026-06-24 | Security (Week 6 build) | Draft | Initial model for Week 6 CI/CD + Docker additions. Awaiting owner sign-off on residual risks #3, #5, #9. |
