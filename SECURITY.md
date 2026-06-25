# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| `main`  | Best effort |

## Project Status & Important Notice

HealthTrack API is a **teaching project**. `app/vitals.py`, `app/auth.py`, and
`app/alerts.py` contain **intentional, documented vulnerabilities** used for
hands-on security training (SQL injection via f-strings, hardcoded credentials,
MD5 password hashing, PII over-exposure, missing authorization checks). These
are **not** to be deployed and are **not** treated as reportable vulnerabilities.
See `CLAUDE.md` and `README.md` for the catalog of intentional issues.

This policy covers the **infrastructure added in Week 6** (CI/CD pipeline,
Docker image, service stack, and the `/health` endpoint).

## Security Assumptions

- The repository's collaborators are semi-trusted; external fork contributors are untrusted.
- The host running `docker compose` is operated by a trusted developer.
- `.env` lives only on the local host and is never committed (`.gitignore` enforces this).
- Pinned dependency versions and the `python:3.11-slim` base image are not compromised at build time.

## Threat Model Summary

The full model is at
[`docs/threat-models/THREAT_MODEL_week6_cicd_docker.md`](docs/threat-models/THREAT_MODEL_week6_cicd_docker.md).

| Asset | Threat | Control |
|-------|--------|---------|
| `ANTHROPIC_API_KEY` | Leak via CI logs / malicious test edit | GitHub encrypted secret; `pull_request` trigger withholds secrets from fork PRs; `permissions: contents: read` — `.github/workflows/ci.yml` |
| `DB_PASSWORD` | Accidental commit | `.env` gitignored; `.dockerignore` excludes it from the build context; placeholders only in `.env.example` |
| Container host | Container escape → host root | Runs as non-root `appuser` (UID 10001) — `Dockerfile` |
| Postgres / Redis | External access | Not published to the host; reachable only on the internal compose network — `docker-compose.yml` |
| Infra liveness | Recon via `/health` | Coarse `ok`/`error` only; no hostnames or exceptions in the response body — `app/health.py:health` |

Known residual risks (awaiting owner sign-off) are tracked in the threat model:
unused secret in the `test` job, unauthenticated `/health` resource use, and the
unscanned base image.

## Secret & Sensitive-Data Handling

- Never commit secrets, API keys, tokens, private logs, or real patient data.
- All credentials are supplied at runtime via environment variables (`.env` locally,
  GitHub secrets in CI) — never hardcoded in source or baked into the image.
- The CI security job (`bandit` + `pip-audit`) runs in **advisory** mode because the
  app ships intentional teaching vulnerabilities; it surfaces findings without
  blocking. Harden the app and flip `continue-on-error` to `false` before any real use.

## Reporting a Vulnerability

For an issue in the **Week 6 infrastructure** (not the intentional teaching code),
open a GitHub issue describing the problem and affected files. Do **not** include
real secrets or sensitive data in the report. `TODO:` add a private security contact
before this repository is published externally.
