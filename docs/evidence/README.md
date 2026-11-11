# Assessment evidence checklist

This directory records observed local checks. It contains no fabricated screenshot, GitHub Actions run, registry publication, or demo recording.

- [x] Isolated PostgreSQL API test output: [api-tests.txt](api-tests.txt) (10 passed; includes the concurrent one-success/one-conflict case).
- [x] Local Docker build and HTTPS health/availability responses: [runtime-validation.txt](runtime-validation.txt).
- [x] API and PostgreSQL stop/restart recovery: [recovery-validation.txt](recovery-validation.txt), [database-recovery-validation.txt](database-recovery-validation.txt).
- [x] Reservation persistence across API restart: [persistence-validation.txt](persistence-validation.txt).
- [x] Repeatable seed command run twice: [seed-validation.txt](seed-validation.txt); both runs added zero duplicate rooms.
- [x] Backup checksum, separate database restore, expected rows/constraint, and restored-data API lookup: [backup-restore.txt](backup-restore.txt). The archive itself is in ignored `backups/` and is not committed.
- [x] Local Trivy scan record from the previously built image: [trivy-summary.md](trivy-summary.md). The latest image was not rescanned during this run because Trivy was unavailable.
- [ ] Successful GitHub Actions run URL and screenshot.
- [ ] GHCR SHA/version tag and immutable digest.
- [ ] 3–5 minute screen recording (the user will record it separately).

The latest local test and runtime records include timestamps and the checked-out commit at the time of the run. Capture the final commit and remote CI data after pushing.
