# 🎓 Lesson 01: The Assembly Line — CI/CD Pipeline & Docker Containerisation

## 🛡️ Welcome Back, Security Analyst!

Ever watched a SOAR playbook fan out — one trigger firing an enrichment step, a
gate, then a response action, each only running if the one before it passed? 🔍
Today we're exploring the **Week 6 delivery pipeline** for HealthTrack API — the
"assembly line" that turns a `git push` into automated linting, testing, security
scanning, and a runnable container. The moving parts: `.github/workflows/ci.yml`,
the `Dockerfile`, `docker-compose.yml`, and the `/health` endpoint in `app/health.py`.

---

## 🎯 Learning Objectives

By the end of this lesson you will be able to:

- Explain how GitHub Actions jobs chain with `needs:` to form a gated pipeline
- Describe why a multi-stage `Dockerfile` produces a smaller, safer image
- Justify running a container as a non-root user
- Explain healthcheck-gated startup in `docker-compose.yml` (`depends_on: service_healthy`)
- Defend the liveness-vs-readiness design choice behind `/health`

**Time estimate:** 45 minutes | **Prerequisites:** basic git; ability to read YAML

---

## 🧠 What This Component Does — Plain English

A **CI/CD pipeline** is automation that runs every time code changes. "CI"
(Continuous Integration) means: whenever someone pushes or opens a pull request,
a clean machine checks the code out, runs the linters and tests, and reports
back. If anything fails, the change is flagged before it can merge. The goal is
that broken or insecure code never silently lands on the main branch.

**Containerisation** (Docker) packages the app plus its exact dependencies into a
single image that runs identically on any machine — your laptop, a teammate's, a
server. `docker-compose` then wires several containers together (the API, a
Postgres database, a Redis cache) into one stack you start with a single command.

**Real-world analogy:** The pipeline is a SOAR playbook — a trigger (`push`/PR)
kicks off ordered stages (enrich → validate → respond), and a failed gate halts
the rest. The Docker image is a forensic "gold image": a known-good, reproducible
build you can stamp out anywhere, so "works on my machine" stops being a defense.

---

## 🔵🟡🔴 Career Lens — Three Perspectives on This Component

### 🔵 Analyst Lens — What a SOC Analyst Sees Here

You already live inside pipelines that fire on events and branch on conditions.
A GitHub Actions workflow is the same shape: `on: push`/`pull_request` is the
**correlation rule's trigger**, each `job` is a **playbook stage**, and `needs:`
is the **"only run this step if the prior one succeeded"** logic you set in a SOAR
playbook. The `security` job (`bandit` + `pip-audit`) is literally a SAST + SCA
enrichment step — the same instinct as running an artifact through VirusTotal and
a CVE feed before you act on it.

**SOC parallel:** `ci.yml` is a SOAR playbook — trigger on event, run ordered
enrichment/validation stages, and gate the outcome on whether each stage passed.

---

### 🟡 Engineer Lens — What a Cybersecurity Engineer Builds Here

The engineering substance is in three decisions. **(1) Job ordering with `needs:`**
— `test` and `security` both declare `needs: [lint]`, so lint is the cheap fast
gate and the expensive jobs only run if it passes (a fan-out: `lint → {test, security}`).
**(2) Multi-stage Docker build** — a `builder` stage installs dependencies into a
virtualenv; a separate slim `runtime` stage copies only that venv, leaving the
build cache and tooling behind. **(3) Least privilege at two layers** — the
workflow pins `permissions: contents: read`, and the container drops to a non-root
`appuser`. Each is a defensible code-review answer, not a default.

**Engineering decision to own:** the multi-stage build. Be ready to explain that
the final image contains the runtime venv + app code only — no pip cache, no
compilers, no tests — which shrinks both image size and attack surface.

---

### 🔴 AI Security Engineer Lens — What an AI/ML Security Engineer Watches For

This pipeline touches an AI surface: `ci.yml` injects `ANTHROPIC_API_KEY` from
GitHub secrets, and a sibling workflow (`ai-skill-review.yml`) calls an LLM to
review PRs. Two ML-specific concerns: **secret exposure** (a model-calling job
holds a credential — a malicious PR that edits the job could exfiltrate it; the
`pull_request` trigger withholds secrets from fork PRs, which is the key control)
and **indirect prompt injection** (the AI review reads the PR diff — attacker-
controlled text — so its output must never gate a security decision deterministically).

**AI security surface:** any CI job that holds an LLM API key is a credential-theft
target; scope the secret to only the job that needs it and never let attacker-
controlled diff text drive an automated merge/deploy action.

---

## 🗺️ Where This Fits in the System

```
git push / PR  →  ci.yml [ lint ] ──▶ [ test (≥90% cov) ]
                                  └──▶ [ security (advisory) ]

docker compose up ─▶ [ db: postgres ]  (healthcheck: pg_isready)
                     [ redis ]         (healthcheck: redis-cli ping)
                          │  api waits via depends_on: service_healthy
                          ▼
                     [ api: gunicorn → /health ]  ◀── [THIS LESSON]
```

Remove the pipeline and broken code merges silently. Remove healthcheck gating and
the api starts before Postgres is ready, so early requests fail with connection errors.

---

## 🔑 Key Concepts

### Job dependency (`needs:`)
Declaring `needs: [lint]` on a job tells GitHub Actions not to start it until
`lint` succeeds. This turns independent jobs into an ordered pipeline and avoids
wasting compute on code that already failed a cheaper check.

### Multi-stage build
A `Dockerfile` with more than one `FROM`. Early stages build artifacts; the final
stage copies only what it needs. Everything not copied forward is discarded — so
build-time tools never ship in the runtime image.

### Liveness vs. readiness
**Liveness** = "is the process up?" **Readiness** = "can it serve real traffic
(are its dependencies reachable)?" Conflating them causes orchestration bugs; this
project's `/health` is a liveness signal that *also reports* dependency status.

---

## 📝 Code Walkthrough

### The gated pipeline

```yaml
# .github/workflows/ci.yml
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  contents: read

jobs:
  lint:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install ruff==0.8.4
      - run: ruff check app tests wsgi.py

  test:
    needs: [lint]
    env:
      ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
    steps:
      - run: pip install -r requirements-dev.txt
      - run: pytest --cov=app --cov-report=term-missing --cov-fail-under=90
```

**Line-by-line breakdown:**

| Lines | What it does | Why it was designed this way |
|-------|-------------|------------------------------|
| `on:` | Fires on push to main and any PR to main | PR runs catch problems *before* merge |
| `permissions: contents: read` | Read-only repo token | Least privilege — this pipeline never writes |
| `needs: [lint]` | Test waits for lint | Don't spend minutes testing code that won't lint |
| `secrets.ANTHROPIC_API_KEY` | Pulls the key from the encrypted store | Never hardcode credentials in source |
| `--cov-fail-under=90` | Fails below 90% coverage | A minimum-evidence threshold, like baseline log coverage |

**Design pattern used:** a dependency graph (DAG) of jobs — the fan-out `lint → {test, security}`.

### The multi-stage image

```dockerfile
# Dockerfile
FROM python:3.11-slim AS builder
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim AS runtime
ENV PATH="/opt/venv/bin:$PATH"
COPY --from=builder /opt/venv /opt/venv
COPY app ./app
COPY wsgi.py ./
RUN useradd --create-home --uid 10001 appuser && chown -R appuser:appuser /app
USER appuser
EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:5000/health', timeout=3).status == 200 else 1)"
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "wsgi:app"]
```

> ⚠️ **Common pitfall:** binding gunicorn to `127.0.0.1` instead of `0.0.0.0`
> makes the app unreachable from outside the container even with `-p 5000:5000`.
> Inside a container, isolation comes from Docker's network namespace — not the
> bind address — so you bind all interfaces *within* the container.

### Healthcheck-gated startup

```yaml
# docker-compose.yml (api service)
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
```

The api does not start until Postgres and Redis report healthy via *their own*
healthchecks (`pg_isready`, `redis-cli ping`). That is what makes `/health` show
`database: ok` / `cache: ok` instead of racing a half-started database.

### The liveness endpoint

```python
# app/health.py
    db_ok = _check_database()
    cache_ok = _check_cache()
    body = {
        "status": "ok" if (db_ok and cache_ok) else "degraded",
        "database": "ok" if db_ok else "error",
        "cache": "ok" if cache_ok else "error",
    }
    return jsonify(body), 200
```

Returns **200 whenever the app is up** (liveness), with dependency status in the
body. That is why `docker run` of just the image (no db/redis) still returns 200
with `status: degraded` — exactly what Part 2 of the brief checks.

---

## 🧪 Hands-On Exercises

> Before starting: activate the venv (`.venv\Scripts\Activate.ps1`) and ensure
> Docker Desktop is running for the Docker exercises.

### 🔬 Exercise 1: Run the pipeline's gates locally

Proves the same checks CI runs pass on your machine.

```powershell
ruff check app tests wsgi.py
pytest --cov=app --cov-fail-under=90
```

📊 **Expected output:**
```
All checks passed!
Required test coverage of 90% reached. Total coverage: 98.14%
45 passed
```

✅ **You succeeded if:** coverage prints ≥90% and 45 tests pass.

---

### 🔬 Exercise 2: Build the image and check its size

Tests the multi-stage build.

```powershell
docker build -t healthtrack:local .
docker images healthtrack:local
```

📊 **Expected output:**
```
REPOSITORY     TAG     IMAGE ID      CREATED         SIZE
healthtrack    local   <id>          <time> ago      ~150-200MB
```

✅ **You succeeded if:** the image builds and is a few hundred MB (not >1GB) — proof the build tooling did not ship.

---

### 🔬 Exercise 3: Standalone container — liveness still green

Shows `/health` returns 200 even with no database.

```powershell
docker run -d -p 5000:5000 --name ht healthtrack:local
curl http://localhost:5000/health
docker rm -f ht
```

📊 **Expected output:**
```
{"cache":"error","database":"error","status":"degraded"}
```
(HTTP status 200)

✅ **You succeeded if:** you get a 200 with `status: degraded` — liveness is up, dependencies are honestly reported down.

---

### 🔬 Exercise 4: Full stack — dependencies report healthy

```powershell
copy .env.example .env   # then edit values
docker compose up -d
docker compose ps
curl http://localhost:5000/health
docker compose down
```

📊 **Expected output:**
```
{"cache":"ok","database":"ok","status":"ok"}
```

✅ **You succeeded if:** all services show healthy and `/health` reports `ok`/`ok`.

---

## 📚 Interview Preparation

### 🟡 Cybersecurity Engineering Interview

**Q:** Why use a multi-stage Docker build instead of a single stage, and what is the
security benefit?

**A:** A single stage leaves the compiler, pip cache, and any build-time packages
in the final image — extra weight and extra attack surface. A multi-stage build
installs dependencies in a `builder` stage, then the `runtime` stage copies only
the resulting virtualenv and the app code. Nothing else crosses the stage boundary,
so the shipped image is smaller and contains fewer exploitable components. Combined
with dropping to a non-root user, a container escape lands an attacker in a minimal,
unprivileged environment rather than a root shell with a toolchain.

*Why this answer works:* It connects an image-size optimization directly to attack-surface reduction — engineering reasoning tied to a security outcome.

---

### 🔴 AI Security Engineering Interview

**Q:** This pipeline has a job that calls an LLM with an API key, and another that
reads the PR diff for AI review. What are the risks and how would you contain them?

**A:** Two surfaces. First, credential theft: any job holding `ANTHROPIC_API_KEY` is
a target — a malicious PR editing that job could print the secret. The control is
that `pull_request` (not `pull_request_target`) withholds secrets from fork PRs, and
the secret should be scoped to only the job that needs it. Second, indirect prompt
injection: the AI reviewer ingests attacker-controlled diff text, so its output is
untrusted and must never deterministically gate a merge or deploy — a human or a
rule-based check stays in the loop. That mirrors the project rule that probabilistic
model output never gates a security decision.

*Why this answer works:* It treats the CI system as an AI attack surface — secret scope plus untrusted-input boundaries — not just a build tool.

---

## ✅ Key Takeaways

- `needs:` turns jobs into a gated pipeline: `lint → {test, security}`.
- Multi-stage builds ship only the runtime artifact — smaller image, smaller attack surface.
- Non-root `USER` means a container escape isn't an automatic host-root compromise.
- `depends_on: service_healthy` sequences startup so the api never races its database.
- `/health` is liveness (always 200 when up) that also reports dependency status.

---

## 📋 Quick Reference Card

| Item | Value |
|------|-------|
| Files | `.github/workflows/ci.yml`, `Dockerfile`, `docker-compose.yml`, `app/health.py` |
| Pipeline entry | `on: push` / `pull_request` to `main` |
| Image entry point | `gunicorn ... wsgi:app` |
| Health endpoint | `GET /health` → 200 + `{status, database, cache}` |
| Key config | `ANTHROPIC_API_KEY` (CI secret); `DB_*`, `REDIS_URL` (env) |
| Coverage gate | `--cov-fail-under=90` (currently 98%) |
| Validate | `python scripts/validate_ci.py` |

---

## 📌 Implemented vs. Recommended

### What This Project Implements ✅
- Gated pipeline with `needs:` ordering — `.github/workflows/ci.yml`
- Multi-stage, non-root, healthchecked image — `Dockerfile`
- Healthcheck-gated compose stack with internal-only db/redis — `docker-compose.yml`
- Liveness `/health` with dependency report — `app/health.py:health`

### General Best Practices — Recommended but Not Implemented Here
- SHA-pinned actions + hash-pinned deps — `Recommended (not implemented here)`
- Container image CVE scanning (e.g. Trivy) in CI — `Recommended (not implemented here)`
- Split `/livez` (liveness) and `/readyz` (readiness) endpoints — `Recommended (not implemented here)`

---

## ⚖️ Decisions & Trade-offs

### Decisions Touched
| Decision | Statement | Why It Matters Here |
|----------|-----------|---------------------|
| Advisory security scan | `security` job is `continue-on-error: true` | App ships intentional vulns; blocking would make the pipeline un-green |
| Liveness `/health` (200 always) | Endpoint reports deps but never 503s | Lets the standalone container pass Part 2's 200 check |

### What We Explicitly Rejected
- **`curl`-based HEALTHCHECK:** rejected to avoid installing `curl` in the image — used Python stdlib `urllib` instead.
- **Single requirements file:** rejected; split runtime vs `requirements-dev.txt` to keep pytest out of the prod image.

### Trade-off Log
| Choice Made | What We Gained | What We Gave Up |
|-------------|----------------|-----------------|
| Advisory security job | A green pipeline on a vuln-laden teaching app | No hard block on new real vulns until `continue-on-error` flips |
| 200-always `/health` | Standalone container passes liveness checks | Readiness semantics (a 503 when deps down) |

### Future Gate Conditions
- App hardened (vulns fixed) → flip `security` job to blocking (`continue-on-error: false`).
- Deploy to an orchestrator (Kubernetes) → split liveness/readiness probes.

> ⚠️ Image size in Exercise 2 is an estimate — confirm with `docker images` on your build.

---

## 🚀 Ready for Lesson 02?

Next up: **The AI Reviewer** — how `ai-skill-review.yml` calls an LLM to review PRs
and where prompt-injection risk hides. Get ready to trace untrusted input through a
model call!

**Optional deeper dive:** read the Docker docs on `HEALTHCHECK` and compose
`depends_on` conditions — https://docs.docker.com/reference/dockerfile/#healthcheck

**Modification challenge:** add a `timeout-minutes` and an image-scan step to the
`security` job, or split `/health` into `/livez` and `/readyz`. Expected behavior:
`/livez` returns 200 with no DB call; `/readyz` returns 503 when a dependency is down.

*Remember: a pipeline that doesn't gate, and an image that ships its toolchain, are both just theater — the controls only count when they actually stop something.* 🛡️
