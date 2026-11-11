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

## Assessment completion run (2026-11-11, IST)

These checks were performed after the original setup record above. The API change for unknown room types and test updates were built and exercised locally; the checked-out Git commit shown at the time was `6821308fb4a0f4872a8667a6e4cc073b7bce5d3d`.

- Ruff: `ruff check .` passed and `ruff format --check .` reported **8 files already formatted**.
- Isolated Compose test profile: formatting and lint passed; Pytest reported **10 passed in 1.01s** against `hotel_booking_test`. Complete command output is saved in [api-tests.txt](api-tests.txt). The suite includes invalid reversed dates, unknown room types, direct PostgreSQL overlap rejection, and simultaneous requests with exactly one 201 and one 409.
- `docker compose build` succeeded after the API validation change. The final local image ID and live runtime responses are in [runtime-validation.txt](runtime-validation.txt).
- API, PostgreSQL, and Nginx were all healthy after build/recreation. HTTPS `/health`, `/ready`, standard-room availability, and HTTP 400 for unknown room type were captured.
- API restart persistence check: before and after counts were `rooms=6, reservations=1`; readiness returned 200. See [persistence-validation.txt](persistence-validation.txt).
- Failure/recovery: stopping API produced a proxy HTTP 502; starting it restored readiness. Stopping PostgreSQL made readiness return 503 / `not_ready`; starting it restored all three healthy containers and readiness HTTP 200. See [recovery-validation.txt](recovery-validation.txt) and [database-recovery-validation.txt](database-recovery-validation.txt).
- Backup/restore drill: `backups/hotel_booking_audit.dump` (7,564 bytes), SHA-256 `F58270FFB5D826F02879130E527F96615D86558281EC6E5848DCA4F03528DBF8`. Restored successfully into the separate `hotel_booking_restore_audit_20261111` database. It contains two expected tables, six rooms, one reservation, and the exclusion constraint; the API readiness and lookup returned 200 when connected to it. Details are in [backup-restore.txt](backup-restore.txt). The archive is in the ignored `backups/` directory and is not committed.
- The existing local Trivy record in [trivy-summary.md](trivy-summary.md) describes an earlier image scan. Trivy is not installed in this shell, so the newly rebuilt image was not rescanned here; CI scanning remains to be verified.

## Still requiring remote access or the user's recording

- No GitHub Actions run was triggered or verified, and no image was pushed to GHCR. Push only after reviewing the final local changes and confirm package write permissions in repository Actions settings.
- No GitHub Actions run URL or remote image digest is available in this local audit.
- The user will record the 3�5 minute demo separately, as requested.

## Assessment completion run (2026-11-11, IST)

These checks were performed after the original setup record above. The API change for unknown room types and test updates were built and exercised locally; the checked-out Git commit shown at the time was `6821308fb4a0f4872a8667a6e4cc073b7bce5d3d`.

- Ruff: `ruff check .` passed and `ruff format --check .` reported **8 files already formatted**.
- Isolated Compose test profile: formatting and lint passed; Pytest reported **10 passed in 1.01s** against `hotel_booking_test`. Complete command output is saved in [api-tests.txt](api-tests.txt). The suite includes invalid reversed dates, unknown room types, direct PostgreSQL overlap rejection, and simultaneous requests with exactly one 201 and one 409.
- `docker compose build` succeeded after the API validation change. The final local image ID and live runtime responses are in [runtime-validation.txt](runtime-validation.txt).
- API, PostgreSQL, and Nginx were all healthy after build/recreation. HTTPS `/health`, `/ready`, standard-room availability, and HTTP 400 for unknown room type were captured.
- The idempotent seed command ran twice; each run added zero duplicate rooms. See [seed-validation.txt](seed-validation.txt).
- API restart persistence check: before and after counts were `rooms=6, reservations=1`; readiness returned 200. See [persistence-validation.txt](persistence-validation.txt).
- Failure/recovery: stopping API produced proxy HTTP 502; starting it restored readiness. Stopping PostgreSQL made readiness return 503 / `not_ready`; starting it restored all three healthy containers and readiness HTTP 200. See [recovery-validation.txt](recovery-validation.txt) and [database-recovery-validation.txt](database-recovery-validation.txt).
- Backup/restore drill: `backups/hotel_booking_audit.dump` (7,564 bytes), SHA-256 `F58270FFB5D826F02879130E527F96615D86558281EC6E5848DCA4F03528DBF8`. Restored successfully into the separate `hotel_booking_restore_audit_20261111` database. It contains two expected tables, six rooms, one reservation, and the exclusion constraint; API readiness and lookup returned 200 when connected to it. See [backup-restore.txt](backup-restore.txt). The archive is in ignored `backups/` and is not committed.
- The existing local Trivy record in [trivy-summary.md](trivy-summary.md) describes an earlier image scan. Trivy is not installed in this shell, so the newly rebuilt image was not rescanned here; CI scanning remains to be verified.

## Still requiring remote access or the user's recording

- No GitHub Actions run was triggered or verified, and no image was pushed to GHCR. Push only after reviewing the final local changes and confirm package write permissions in repository Actions settings.
- No GitHub Actions run URL or remote image digest is available in this local audit.
- The user will record the 3–5 minute demo separately, as requested.
