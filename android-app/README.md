# XP Battery Android

Kotlin Android app, Android 8+ (minSdk 26), with on-device SQLite history and WorkManager periodic work.

## Remote Admin setup
The app has fields for the HTTPS API URL and DEVICE_KEY. Create/deploy the Cloudflare Worker and D1 database using backend/cloudflare/README.md, then enter the Worker URL and the exact DEVICE_KEY secret in the app. Open the GitHub Pages admin and enter the same Worker URL plus the ADMIN_KEY secret.

On first sync the phone registers itself, after which the Admin can enable/disable collection, select a 15-minute to 24-hour interval, or request an immediate reading. The app sends battery percentage/charging, device manufacturer/model, Android version and storage totals. WorkManager is best-effort; Android may delay background jobs despite battery-optimization exemption.

## Build
GitHub Actions workflow Build XP Battery APK compiles app-debug.apk and publishes artifact xp-battery-apk for 30 days. This is a debug APK, not a Play Store release build.