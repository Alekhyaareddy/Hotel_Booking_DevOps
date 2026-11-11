# Local validation record

This record captures checks actually run during project setup on 2026-11-11. These results describe this local development environment; they are not GitHub Actions results.

## Checks that passed

- `ruff check .` — **All checks passed!**
- `docker compose --profile test run --rm tests` — Ruff lint and format checks passed; Pytest reported **9 passed in 0.63s** against the isolated `hotel_booking_test` database, including two simultaneous reservation requests competing for one room.
- `docker compose up --build -d` — API and PostgreSQL reported healthy. Nginx was serving HTTPS; its first health-check implementation was incompatible with BusyBox wget, then the probe was corrected to use a dedicated localhost HTTP endpoint.
- After the Nginx probe fix, `docker compose ps` showed PostgreSQL, API, and Nginx all **healthy**. `nginx -t` inside the container reported syntax OK and configuration test successful.
- `nginx -t` inside the container — syntax OK and configuration test successful.
- Python HTTPS smoke requests (with certificate verification disabled for the temporary self-signed development certificate): `/health` returned `{"status":"ok","version":"local"}`; `/ready` returned `{"database":"available","status":"ready"}`.
- Availability over HTTPS returned the three seeded standard rooms before the smoke reservation.
- A synthetic reservation was created over HTTPS. After restarting the API container, readiness remained available and the same stay showed two available standard rooms, confirming reservation persistence in PostgreSQL.
- Backup restore: a custom-format archive was copied into a separate `hotel_booking_restore_test` database. Queries returned `rooms=6` and `reservations=0`, matching the source database at backup time. SHA-256: `FBCE894386F5D974E3A12E6D395E93A97D69A9C10D17A2E9505028DEFCEBFBBE`.
- After the restart demonstration, the same verified archive was restored to the local demo database to remove the synthetic reservation. Final database counts are `rooms=6`, `reservations=0`; API health and readiness both returned OK afterward.
- Trivy 0.64.1 first found 54 fixed HIGH/CRITICAL Debian package vulnerabilities in the original base layer. The Dockerfile now applies Debian security updates. The final Trivy 0.70.0 scan ran with `--severity HIGH,CRITICAL --ignore-unfixed --exit-code 1` against the digest-pinned image on Debian 12.15 and exited **0** with **0 matching findings**. See [the scan record](trivy-summary.md).

## Checks still requiring a GitHub repository or a recording step

- The GitHub Actions workflow has not been run because no remote repository push or tag was made during this local build. Trigger it after pushing to GitHub and save its actual run URL or screenshot here.
- GHCR publication has not been attempted; it happens on a branch or version-tag push and requires the repository package permission described in the README.
- Save the final 3–5 minute screen recording here or add its share link after recording with the steps in `docs/demo-script.md`.

The Trivy scan is run separately and must be recorded with its actual result; a scan result is not considered passing merely because the workflow is configured.
