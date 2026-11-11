# Operations runbook

Commands below are shown for PowerShell unless marked otherwise. Run them from the repository root. Replace sample values with your own; never commit credentials or backups containing guest data.

## Start and inspect

```powershell
docker compose up --build -d
docker compose ps
docker compose logs --tail 100 api
Invoke-RestMethod https://localhost/ready
```

If Nginx does not start, verify `nginx/certs/localhost.pem` and `localhost-key.pem` exist. If the API does not become healthy, inspect its logs and verify the database URL password matches `POSTGRES_PASSWORD`.

## Repeatable seed

```powershell
docker compose exec api python -m database.seed
```

It inserts only missing room numbers. It does not remove user-created rooms or reservations.

## Create a database backup

The custom-format archive is compressed and can be restored with `pg_restore`. Keep backups outside the repository and copy them to a separate protected location for any real data.

```powershell
New-Item -ItemType Directory -Force backups | Out-Null
docker compose exec db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc -f /tmp/hotel_booking.dump'
docker compose cp db:/tmp/hotel_booking.dump ./backups/hotel_booking.dump
Get-FileHash ./backups/hotel_booking.dump -Algorithm SHA256
```

For repeatable operations, add a date to the backup filename and retain multiple generations. A backup is useful only if you periodically test restoring it.

## Restore a backup (replaces current database contents)

This is a destructive recovery procedure. Stop the API first so it cannot write while restoring. Copy the chosen archive into the database container, then restore it. `--clean` removes objects that exist in the archive before recreating them.

```powershell
docker compose stop api
docker compose cp ./backups/hotel_booking.dump db:/tmp/hotel_booking.dump
docker compose exec -T db pg_restore --clean --if-exists --no-owner --no-privileges --exit-on-error -U hotel_app -d hotel_booking /tmp/hotel_booking.dump
docker compose start api
docker compose ps
Invoke-RestMethod https://localhost/ready
```

Inspect API logs and check known sample data after restore. For a real incident, preserve the failed database volume before attempting recovery, and confirm the archive and target database before running destructive restore commands.

## Restart and recovery demonstration

1. Create a reservation and save its booking reference.
2. Restart the API: `docker compose restart api`.
3. Check health/readiness and create an availability request again.
4. Recreate containers while preserving the named volume: `docker compose down` then `docker compose up -d`.
5. Confirm the reservation is still reflected in availability and that database/API/Nginx report healthy.

Do not use `docker compose down -v` in this demonstration: that deletes the persistent database volume.

## Roll back an application release

CI images are versioned by commit SHA and release tag. Keep the last known good immutable tag available. Set `IMAGE_NAME` and `IMAGE_TAG` in `.env` to the prior GHCR image and tag, then pull and recreate the API. Keep the database volume intact.

```text
IMAGE_NAME=ghcr.io/OWNER/REPOSITORY
IMAGE_TAG=sha-<known-good-commit>
```

Then run:

```powershell
docker compose pull api
docker compose up -d --no-build api nginx
docker compose ps
Invoke-RestMethod https://localhost/ready
```

The application currently initializes a fresh schema with `create_all`, and does not run destructive migrations. If future releases include schema changes, database backup and backward-compatible migration planning must happen before rolling back the code; code rollback alone cannot reverse a schema change.

## Troubleshooting

| Symptom | Checks |
|---|---|
| API stays unhealthy | `docker compose logs api db`; check `DATABASE_URL`, matching credentials, and PostgreSQL health |
| HTTPS connection fails | Check Nginx logs, certificate file names, and whether ports 80/443 are already used |
| Certificate warning | Re-run `mkcert -install`; confirm the certificate was generated for `localhost` |
| Reservation returns 409 | The requested inventory is fully occupied for those dates, or a competing request won the room |
| Test database permission error | Ensure the test database is owned by `hotel_app` and `TEST_DATABASE_URL` points to the test database only |
