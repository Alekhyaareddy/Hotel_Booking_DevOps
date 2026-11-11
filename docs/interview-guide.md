# Interview guide: explain this project

Use the answers as a starting point and put them in your own words. The best demonstration is to show the actual API, tests, and database constraint while explaining the choices.

## What did you build?

I built a small Flask JSON API for hotel room availability and reservations. Nginx handles HTTPS in front of the Flask API. Flask uses SQLAlchemy to store rooms and reservations in PostgreSQL. Docker Compose runs the API, database, and proxy together. GitHub Actions runs lint, tests, image build, and Trivy scanning.

## How does a reservation request work?

1. Flask checks that the body is JSON and all required guest and room fields exist.
2. It parses check-in and check-out as calendar dates and rejects past check-in dates or a check-out that is not later.
3. SQLAlchemy searches for an unoccupied room of the requested type.
4. It inserts a reservation inside a database transaction.
5. PostgreSQL enforces the no-overlap rule and Flask returns a booking reference.

The availability query gives a useful response, but the database rule is the final protection. Two separate API workers can both query at nearly the same time.

## Why use a PostgreSQL exclusion constraint?

An application-only “check then insert” has a race: both requests can see a room as available before either inserts. PostgreSQL's GiST exclusion constraint compares the room ID and each reservation's date range. It prevents two confirmed rows from using the same room on overlapping dates, even when inserts race. The API maps that database conflict to HTTP `409`.

Date ranges are half-open: `[check_in, check_out)`. A stay includes the arrival day but excludes the departure day, so a guest can leave on the same date the next guest arrives.

## Why do the tests use PostgreSQL?

The key concurrency protection is a PostgreSQL feature, so SQLite would not exercise the same production rule. Pytest uses an isolated `hotel_booking_test` database. One test submits two reservation requests at the same time for the only matching room; one request succeeds and one receives a conflict. Another test verifies PostgreSQL rejects an overlapping insert directly.

## What do the health checks mean?

- `/health` shows that the Flask process answers requests.
- `/ready` also queries PostgreSQL, so it reports whether the application can serve database-backed work.
- Compose waits for PostgreSQL before starting the API and waits for the API before starting Nginx.
- PostgreSQL data lives in a named volume, so replacing or restarting containers does not remove reservations.

## Why put Nginx in front?

Nginx listens on ports 80 and 443. It redirects HTTP to HTTPS and proxies requests to Flask on Compose's private network. In local development, `mkcert` can create a certificate trusted by the local machine. The repository ignores certificate files and never stores private keys in Git.

## What happens in CI?

GitHub Actions installs the pinned Python dependencies, runs Ruff checks and the PostgreSQL-backed tests, then builds a Docker image. Trivy blocks the workflow when fixed HIGH or CRITICAL vulnerabilities are found. On a push, the workflow tags and publishes that same scanned image to GHCR using its commit SHA and release version. The SHA tag gives operations a specific version to deploy or roll back to.

## How did you handle the Trivy findings?

The first local scan found outdated Debian packages in the base image. I kept the Python base pinned by digest and added an OS security-update step to the Dockerfile. The rebuilt image passed the configured HIGH/CRITICAL scan with zero matching findings. Explain that a clean scan is specific to the scan date and database; the CI scan runs again on each build.

## What would you improve for production?

I would add reviewed Alembic schema migrations, authentication and authorization, request rate limits, reservation cancellation, a managed secrets store, external backup storage and restore drills, monitoring, and a deployment environment with multiple API instances. This assessment's local setup is a learning deployment, not a public hotel service.

## Suggested commands to show live

```powershell
docker compose ps
Invoke-RestMethod https://localhost/health
Invoke-RestMethod https://localhost/ready
docker compose --profile test run --rm tests
```

For more detailed operations and demo steps, see [the operations runbook](operations-runbook.md) and [the demo script](demo-script.md).
