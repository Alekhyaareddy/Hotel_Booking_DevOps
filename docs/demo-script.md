# 3–5 minute assessment demonstration script

Use this as a recording checklist after the project has been run successfully. Capture your actual terminal and GitHub Actions run; do not claim an output you did not observe.

1. **0:00–0:30 — Scope and architecture.** Open `https://localhost` in Chrome. Explain that Staywell is a local booking demo; property descriptions and sample prices are catalogue content, while availability and reservations use the real API and PostgreSQL. Show `docs/architecture.md` and point out Nginx, Flask, SQLAlchemy, PostgreSQL, and CI.
2. **0:30–1:15 — Search and availability.** Search a destination and dates in the website. Explain that each room count comes from the availability API and that check-out is excluded from a stay.
3. **1:15–2:10 — Create and retrieve a reservation.** Submit the booking form, show the saved booking reference, then use **My bookings** with the same guest email to retrieve it. Explain that the demo takes no payment.
4. **2:10–2:55 — Explain the race protection.** Show the PostgreSQL exclusion constraint in `app/models.py` and its test. Explain why the database constraint protects concurrent API workers after the preliminary availability query.
5. **2:55–3:40 — CI and container security.** Show a real GitHub Actions run with lint, tests, image build, and Trivy output; show the published SHA/release tag if the workflow has published it.
6. **3:40–4:30 — Operations.** Show the Compose volume and health status. Briefly explain backup/restore and code rollback from the runbook. If time allows, restart the API and confirm readiness.

Keep the final video between three and five minutes. Upload or save the recording, then add its path or link to the evidence checklist.
