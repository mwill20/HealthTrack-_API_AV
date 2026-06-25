# Week 6 Mini Project — Brief (Reference Copy)

> Locked-in verbatim copy of the assignment for reference during the build.

---

In this mini project, you will use Claude Code to build a complete CI/CD pipeline for the HealthTrack API, then containerise it with Docker. By the end, a git push will trigger automated linting, testing, security scanning, and PR review — and the app will run in Docker with a single command. The rule for this project

Claude Code generates. You review, understand, and commit.
Never commit generated code you cannot explain. If Claude generates something you don't understand — ask it to explain line by line before committing.
The goal is not just a working pipeline. It is understanding why every line is there.
All the best!

## Submission Instructions

### PART 1

Build the Full CI Pipeline (45 min)

- Open Claude Code in healthtrack-api/
- Use the prompt below to generate .github/workflows/ci.yml
- Read every line before committing — ask Claude to explain anything unclear
- Push to GitHub and verify the Actions tab shows your workflow
- Screenshot your first passing CI run for submission

### PART 2

Build the Production Dockerfile (60 min)

- Use Claude Code to generate a multi-stage Dockerfile
- Build it locally and verify the image size
- Test it: docker run -p 5000:5000 healthtrack:local
- Verify curl http://localhost:5000/health returns 200
- Run python scripts/validate_ci.py to check all Dockerfile requirements

### PART 3

Build the Full Service Stack (45 min)

- Generate docker-compose.yml with api + postgres + redis
- Generate .env.example (commit) and .env (gitignored, fill locally)
- Run docker compose up -d and verify all services are healthy
- Run the health check — it should show database: ok and cache: ok
- Run pytest against the running container

### PART 4

End-to-End Test & Final Validation (30 min)

- Make a small code change (add a comment to app/vitals.py)
- Open a PR — the CI pipeline should trigger automatically
- Verify each job runs and passes in the Actions tab
- Run python scripts/validate_ci.py locally — all checks must pass
- Document one thing that went wrong and how Claude helped fix it

## 4.3 Submission Notes (fill in before submitting)

Write 3–5 sentences answering:

- What was the hardest part of setting up the CI pipeline?
- What did the Docker health check catch that curl on the host didn't?
- One specific thing Claude generated that you changed — and why.
- What would you add to the pipeline if you had another hour?

**Total: 100 points · Bonus: +5 for PR template · +5 for health check screenshot**
