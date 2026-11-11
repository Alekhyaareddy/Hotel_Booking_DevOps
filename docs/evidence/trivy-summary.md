# Trivy image scan record

Local scans run on 2026-11-11 against `hotel-booking-api:local`. The initial scan used Trivy 0.64.1; the final scan used Trivy 0.70.0, matching the version in the selected GitHub Action release.

- Scanner: vulnerability scanner (`--scanners vuln`)
- Severity filter: HIGH and CRITICAL
- Unfixed findings: ignored (`--ignore-unfixed`)
- Before OS package updates, Trivy 0.64.1 found 54 fixed HIGH/CRITICAL findings, all in the Debian base image packages.
- After updating Debian packages in the Docker build, Trivy 0.70.0 found **0 matching findings** in the final local scan report (Debian 12.15); the strict exit-code-1 gate exited 0.

The 54 initial findings prompted the Dockerfile change. The initial scan result is retained in `scan-output/report.json` locally and is excluded from Git; the final scan report showed the clean result. Do not commit generated full scan data unless the assessor asks for it.

The scan ran against the locally built image. It is not a GitHub Actions run. CI uses the same HIGH/CRITICAL and ignore-unfixed settings and will scan each future build with its current Trivy vulnerability database.
