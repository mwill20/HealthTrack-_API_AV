# Submission Evidence

Captured command outputs proving the Week 6 deliverables. Screenshots (PNG) are in
this folder alongside this file.

## 1. Passing CI run (Part 1)

Run: https://github.com/mwill20/HealthTrack-_API_AV/actions/runs/28147170519 (branch `main`)

```
Lint (ruff)                    — success
Test (pytest + coverage)       — success
Security scan (bandit + pip-audit) — success
```
Screenshot: `ci-run.png`

## 2. Docker image (Part 2)

```
$ docker images healthtrack:local --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"
REPOSITORY    TAG       SIZE
healthtrack   local     244MB

$ docker exec ht id
uid=10001(appuser) gid=10001(appuser) groups=10001(appuser)     # non-root

$ docker inspect --format '{{.State.Health.Status}}' ht
healthy
```

Standalone container (no db/redis) — `/health` still returns 200 (liveness):
```
$ curl -s -w " [HTTP %{http_code}]" http://localhost:5000/health
{"cache":"error","database":"error","status":"degraded"} [HTTP 200]
```

## 3. Full stack (Part 3)

```
$ docker compose ps --format "table {{.Service}}\t{{.Status}}"
SERVICE   STATUS
api       Up (healthy)
db        Up (healthy)
redis     Up (healthy)

$ curl -s -w " [HTTP %{http_code}]" http://localhost:5000/health
{"cache":"ok","database":"ok","status":"ok"} [HTTP 200]
```
Screenshot: `health-ok.png`

## 4. Pull request — all checks green (Part 4)

PR [#1](https://github.com/mwill20/HealthTrack-_API_AV/pull/1) after adding the
`ANTHROPIC_API_KEY` repo Actions secret:

```
AI Skill Review                    — pass
Lint (ruff)                        — pass
Security scan (bandit + pip-audit) — pass
Test (pytest + coverage)           — pass
```
Every workflow triggered by the PR passes.

## 5. Deliverable validation (Part 4)

```
$ python scripts/validate_ci.py
...
✓ All checks passed! Week 6 mini project complete.
```

## 6. Tests / coverage

```
$ pytest --cov=app --cov-fail-under=90
45 passed
Required test coverage of 90% reached. Total coverage: 98.14%
```

> Note: the separate `ai-skill-review.yml` workflow reads the `ANTHROPIC_API_KEY`
> **repo Actions secret** (not `.env`). With that secret set, it passes (see §4).
