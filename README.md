# HealthTrack API — Teaching Project

**Claude Code Mastery · Week 5 · Sessions 9 & 10**

A patient vital-signs REST API used across both sessions as the hands-on teaching project.

---

## Project Structure

```
healthtrack-api/
├── CLAUDE.md                        ← Always pass this to every agent session
├── README.md
├── requirements.txt
│
├── app/                             ← Flask application (intentional issues for teaching)
│   ├── vitals.py                    ← Primary teaching target — SQL injection, hardcoded creds
│   ├── auth.py                      ← MD5 passwords, no token expiry, logs plaintext passwords
│   ├── alerts.py                    ← No ward-boundary check, PII in SMS body
│   └── routes.py                    ← Thin Flask wrappers
│
├── tests/
│   └── test_vitals.py               ← Intentionally sparse — gives agents real gaps to find
│
├── skills/                          ← Session 10: Skill library
│   ├── README.md                    ← Skill index + governance rules
│   ├── SKILL_TEMPLATE.md            ← Copy to start a new Skill
│   ├── REVIEW_TEMPLATE.md           ← Peer review checklist (100-point rubric)
│   ├── pr-review/SKILL.md           ← v1.2.0  PR Code Review Skill
│   ├── security-audit/SKILL.md      ← v1.1.0  Security Audit Skill
│   └── test-coverage/SKILL.md       ← v2.0.1  Test Coverage Report Skill
│
├── plugins/
│   ├── README.md                    ← How to use the plugin runner
│   └── run_skill.py                 ← Run any Skill from the command line
│
└── .github/workflows/
    └── ai-skill-review.yml          ← GitHub Actions: Skills in CI/CD pipeline
```

---

## Quick Start

```bash
pip install flask anthropic pytest
export ANTHROPIC_API_KEY="sk-ant-..."

# Run existing (sparse) tests
pytest tests/ -v

# List available Skills
python plugins/run_skill.py --list

# Run Security Audit Skill on the vitals module
python plugins/run_skill.py security-audit \
  --scope app/vitals.py \
  --context CLAUDE.md
```

---

## Session Guide

| Session | What you build | Primary file |
|---|---|---|
| Session 9 | 3-agent pipeline (Architect → Security → Test → Consolidate) | `app/vitals.py` |
| Session 10 | Skills library — package those agents as reusable SKILL.md files | `skills/` |

Always pass `CLAUDE.md` to every agent session — it is the project context.

---

## Intentional Issues (Teaching Targets)

All issues are deliberate. Do not fix them before the session.

| Module | Issues |
|---|---|
| `app/vitals.py` | SQL injection via f-strings, hardcoded `DB_PASSWORD`, no input validation, PII over-exposure |
| `app/auth.py` | MD5 password hashing, no token expiry, logs plaintext password on failed login |
| `app/alerts.py` | No ward-boundary authorisation, PII in SMS escalation body, no pagination |

---

## Week 6 — CI/CD Pipeline & Docker

Week 6 adds a CI/CD pipeline and containerisation. See
[`docs/WEEK6_BRIEF.md`](docs/WEEK6_BRIEF.md) for the assignment and
[`SECURITY.md`](SECURITY.md) + [`docs/threat-models/THREAT_MODEL_week6_cicd_docker.md`](docs/threat-models/THREAT_MODEL_week6_cicd_docker.md)
for the security posture of these additions.

### Run the full stack (api + postgres + redis)

```bash
cp .env.example .env        # then edit .env with local values
docker compose up -d        # build + start all three services
curl http://localhost:5000/health
# -> {"status":"ok","database":"ok","cache":"ok"}
```

### Build and run just the image

```bash
docker build -t healthtrack:local .
docker run -p 5000:5000 healthtrack:local
curl http://localhost:5000/health   # 200 (status "degraded" without db/redis)
```

### Run tests with the coverage gate

```bash
pip install -r requirements-dev.txt
pytest --cov=app --cov-fail-under=90
```

### Validate all Week 6 deliverables

```bash
python scripts/validate_ci.py        # all checks must pass
# On Windows, force UTF-8 so the ✓ marks render:
#   set PYTHONUTF8=1 && python scripts/validate_ci.py
```

### CI pipeline (`.github/workflows/ci.yml`)

| Job | Does | Blocking? |
|-----|------|-----------|
| `lint` | `ruff` correctness checks | Yes |
| `test` | `pytest` + ≥90% coverage gate (runs after `lint`) | Yes |
| `security` | `bandit` + `pip-audit` (runs after `lint`) | **Advisory** — app ships intentional teaching vulns |

A separate workflow, `.github/workflows/ai-skill-review.yml`, runs the AI
PR-review / security-audit / coverage Skills on pull requests.
