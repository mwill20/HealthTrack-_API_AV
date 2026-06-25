# Week 6 Mini Project — Completion Checklist

Status of every deliverable, bonus, and standards item. Brief: [docs/WEEK6_BRIEF.md](docs/WEEK6_BRIEF.md).
Legend: ✅ done & verified · 🟡 needs a manual/owner action · ⬜ not started.

## Part 1 — CI Pipeline (`.github/workflows/ci.yml`)
- ✅ Triggers on `push` (main) and `pull_request`
- ✅ `lint` job (ruff) — correctness rules
- ✅ `test` job with `needs: [lint]` and ≥90% coverage gate (`--cov-fail-under=90`)
- ✅ `security` job (bandit + pip-audit), advisory/non-blocking
- ✅ Uses `${{ secrets.ANTHROPIC_API_KEY }}` (no hardcoded keys)
- ✅ `actions/checkout` + `actions/setup-python`
- ✅ Pushed to GitHub; CI run **green** on `main` (all 3 jobs ✅)
- 🟡 Screenshot the first passing CI run for submission

## Part 2 — Production Dockerfile
- ✅ Multi-stage (`builder` + `runtime`)
- ✅ Slim base (`python:3.11-slim`), non-root `appuser`, `HEALTHCHECK`, `EXPOSE`, Python env vars
- ✅ Built locally — image **244MB** (58.4MB content)
- ✅ `docker run -p 5000:5000 healthtrack:local` → `curl /health` returns **200**
- ✅ `python scripts/validate_ci.py` — Dockerfile checks pass
- 🟡 Screenshot image size / `/health` 200 for submission

## Part 3 — Full Service Stack (`docker-compose.yml`)
- ✅ `api` + `postgres` + `redis` services
- ✅ `.env.example` committed; `.env` gitignored
- ✅ `docker compose up -d` → all services **healthy** (healthcheck-gated startup)
- ✅ `/health` shows `database: ok` and `cache: ok`
- ✅ `pytest` passes with the stack running (45 tests, 98% coverage)

## Part 4 — End-to-End Test & Validation
- ✅ Comment added to `app/vitals.py` on a branch
- ✅ PR opened ([#1](https://github.com/mwill20/HealthTrack-_API_AV/pull/1)); CI triggered automatically
- ✅ Graded `ci.yml` jobs **pass** on the PR (lint/test/security all ✅)
- ✅ `python scripts/validate_ci.py` locally — **all checks pass**
- ✅ `ai-skill-review` passes on the PR (secret added) — **all 4 PR checks green**
- 🟡 Document one thing that went wrong + how Claude helped (drafted in submission notes)

## Bonuses
- ✅ PR template present (`.github/pull_request_template.md`) — **+5**
- 🟡 Health-check screenshot — **+5** (capture `/health` healthy)

## Submission notes — [docs/SUBMISSION_NOTES.md](docs/SUBMISSION_NOTES.md)
- 🟡 Review/edit the 4 drafted answers to your own voice

## Standards (brief + lightweight)
- ✅ `SECURITY.md`
- ✅ Threat model — [docs/threat-models/THREAT_MODEL_week6_cicd_docker.md](docs/threat-models/THREAT_MODEL_week6_cicd_docker.md)
- ✅ `LICENSE` (MIT)
- ✅ Tradeoffs log — [docs/TRADEOFFS.md](docs/TRADEOFFS.md)
- ✅ Lesson — [Lessons/Lesson01_CICD_Docker_Pipeline.md](Lessons/Lesson01_CICD_Docker_Pipeline.md)
- ✅ Repo audit — [REPO_AUDIT.md](REPO_AUDIT.md)
- ✅ README updated with Docker/CI usage + logo
- ✅ `docs/ARCHITECTURE.md`, `docs/LIMITATIONS.md`
- ✅ `docs/EVALUATION.md`, `AGENTS.md`
- ⬜ Architecture diagram image (optional; text diagram exists)
- 🟡 Fill the `TODO:` security contact in `SECURITY.md`

## Owner actions still open
1. ✅ Add `ANTHROPIC_API_KEY` repo secret → `ai-skill-review` re-run **green**
2. ✅ Submission screenshots captured — [docs/evidence/](docs/evidence/)
3. 🟡 Edit submission notes to your voice; optionally merge PR #1 (`gh pr merge 1 --squash --delete-branch`)
4. 🟡 Rotate the API key (pasted in plaintext earlier)
5. ⬜ (Optional) SHA-pin actions, hash-pin deps, add image CVE scan (threat-model TODOs)
