# 3–5 minute assessment demonstration script

Use this as a recording checklist after the project has been run successfully. Capture your actual terminal and GitHub Actions run; do not claim an output you did not observe.

1. **0:00–0:30 — Scope and architecture.** Say this is a small reservation API. Show `docs/architecture.md`; point out Nginx, Flask, SQLAlchemy, PostgreSQL, and CI.
2. **0:30–1:15 — Health and availability.** Run `/health`, `/ready`, and one availability request over HTTPS. Explain that check-out is excluded from a stay.
3. **1:15–2:10 — Create a reservation and validate conflicts.** Create a booking, show the booking reference, then make requests until inventory returns HTTP 409. Show a bad date returning HTTP 400.
4. **2:10–2:55 — Explain the race protection.** Show the PostgreSQL exclusion constraint in `app/models.py` and its test. Explain why the database constraint protects concurrent API workers after the preliminary availability query.
5. **2:55–3:40 — CI and container security.** Show a real GitHub Actions run with lint, tests, image build, and Trivy output; show the published SHA/release tag if the workflow has published it.
6. **3:40–4:30 — Operations.** Show the Compose volume and health status. Briefly explain backup/restore and code rollback from the runbook. If time allows, restart the API and confirm readiness.

Keep the final video between three and five minutes. Upload or save the recording, then add its path or link to the evidence checklist.
