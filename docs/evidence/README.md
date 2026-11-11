# Assessment evidence checklist

This directory contains a written record of local implementation checks. It does not contain a fabricated screenshot, GitHub Actions run, or demonstration video.

See [local validation results](local-validation.md) for the checks actually run during implementation, including their environment and limits.

- [x] Pytest output from the actual PostgreSQL-backed run
- [x] `docker compose ps` showing service health
- [ ] Screenshots or saved HTTP responses for health, availability, success, invalid date, and conflict
- [ ] GitHub Actions run showing lint, tests, build, and Trivy result
- [ ] GHCR page showing a SHA or semantic-version image tag
- [x] Backup command output and restore result
- [x] Restart proof showing database persistence
- [x] Local Trivy scan result
- [ ] 3–5 minute screen recording (MP4 or unlisted link) following `docs/demo-script.md`

Redact passwords, tokens, and personal information before capturing or sharing evidence.
