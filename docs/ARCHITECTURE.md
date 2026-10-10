# XP Battery v1 — architecture and setup

## Data flow
1. The owner installs the Android app, opens it, and explicitly approves battery sharing.
2. The app registers the device with Firebase Authentication and Firestore.
3. The admin signs in to the website with an administrator account.
4. Admin settings per device: battery sharing ON/OFF and reporting interval.
5. ON schedules WorkManager periodic sync (Android minimum is 15 minutes). OFF cancels scheduled sync.
6. “Read now” creates a one-time command. FCM can notify the app to run a one-time battery read; delivery is not guaranteed if the OS force-stops the app or the device is offline.
7. The app uploads only battery level, charging state, battery health/status if available, and timestamp.

## Suggested Firestore shape
- `devices/{deviceId}`: ownerUid, displayName, sharingAllowed, lastSeenAt, batteryPercent, isCharging, batteryStatus, batteryUpdatedAt.
- `devices/{deviceId}/private/settings`: reportingEnabled, intervalMinutes, requestNowAt.
- Admin accounts are granted through Firebase Authentication and an admin allow-list/custom claim. Do not trust a role sent by the browser.

## Required configuration before live use
- Create a Firebase project.
- Enable Email/Password Authentication for admin accounts.
- Enable Firestore and Firebase Cloud Messaging.
- Add the Android app package ID and download `google-services.json` into `android-app/app/` locally; do not commit it if the project policy requires it.
- Configure Firebase web app settings in the website environment/config file.
- Apply restrictive Firestore security rules so only an authorized admin can change settings and only the paired device can write its own status.
- For production, use Firebase App Check and admin role claims.

## Android background behavior
WorkManager periodic jobs have a 15-minute minimum interval and may run later under Doze/battery restrictions. The “Read now” action uses FCM as a wake-up signal, but Android does not guarantee instant delivery in every condition. The device owner can disable sharing at any time.

## Security boundaries
This first version intentionally exposes battery information only. It does not provide remote shell execution or remote access to unrelated phone data.
