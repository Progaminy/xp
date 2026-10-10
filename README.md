# XP — Android + Website Admin

Project rebuild in progress. The first feature is battery status only.

## Architecture
- `android-app/`: Android application written in Kotlin. The device owner grants permissions and chooses what the app may share.
- `web-admin/`: browser-based administration panel.
- Firebase Authentication + Cloud Firestore: authenticated admin access and per-device settings/status.
- Firebase Cloud Messaging (FCM): wake-up signal for a requested immediate battery read; periodic updates use Android WorkManager (Android limits periodic work to intervals of at least 15 minutes).

## Privacy and safety
- The app sends only battery fields that the device owner has allowed.
- Admin can enable/disable battery reporting, set an interval, and request a one-time reading.
- No GPS, SMS, contacts, call logs, arbitrary shell commands, or other features in this first version.
- Never commit service-account keys, passwords, signing keys, or real device tokens.
- Android background delivery is best-effort and can be delayed by battery optimization or network conditions.

## Setup status
This is a clean rebuild branch. Firebase project credentials/configuration have not yet been supplied, so the app and website cannot connect to a live backend until Firebase is configured. See `docs/ARCHITECTURE.md`.

The previous Python project is intentionally left untouched on `main` until the replacement is tested.