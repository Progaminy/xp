# XP Battery / XP Admin architecture

- Android app: Kotlin, WorkManager and local SQLite for local battery history.
- Remote API: Cloudflare Worker over HTTPS. Device requests authenticate with DEVICE_KEY; browser admin requests authenticate with ADMIN_KEY.
- Remote database: Cloudflare D1 stores registered devices, current device information, collection settings and battery history.
- Admin: static GitHub Pages site; API URL and admin key are entered by the operator in the browser.

GitHub Pages cannot directly read the private SQLite database inside a phone or execute a server. The remote API and D1 database must be deployed separately. See backend/cloudflare/README.md. Never commit actual keys or a real D1 database ID.

Collection is explicitly configured by the phone owner. Data fields are battery percentage/charging, manufacturer/model, Android version and storage totals. Remote controls take effect when the app next polls the API; periodic Android jobs can be delayed by system power management.