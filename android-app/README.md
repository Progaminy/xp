# XP Android app (Kotlin)

This directory is reserved for the native Android app. The website prototype is in `../web-admin`.

Planned first screen:
- Pair this device with the admin account.
- Clear permission/consent for battery reporting.
- Local switch to pause or stop sharing.
- Current battery percentage and charging status.

Background:
- WorkManager for periodic battery updates (15-minute minimum).
- Firebase Cloud Messaging for one-time “Read now” requests.
- Android may defer background work; force-stop disables delivery until the user opens the app again.

Before building, configure the package ID and Firebase app config as described in `../docs/ARCHITECTURE.md`.