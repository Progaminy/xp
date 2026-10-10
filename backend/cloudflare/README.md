# XP Battery API — Cloudflare Worker + D1

This is a deployment template, not a live service. Android SQLite remains the local history/cache. D1 stores the copy required by the GitHub Pages admin across networks. No Firebase is used.

## Deployment
1. Create a Cloudflare D1 database named xp-battery-db.
2. Run: npx wrangler d1 execute xp-battery-db --file=schema.sql (from this directory).
3. Copy the database ID into wrangler.toml.
4. Set secrets with npx wrangler secret put ADMIN_KEY and npx wrangler secret put DEVICE_KEY. Use two different long random secrets; never commit them.
5. Run npx wrangler deploy and keep the HTTPS URL.
6. The Android client and web admin must be configured with the deployed URL and their respective secrets before remote data/control works.

The API has a health endpoint at /health, device uploads at POST /device/snapshot, and admin endpoints at GET /admin/devices and GET/POST /admin/devices/{id}. This API template alone does not mean remote syncing is already active in the APK.
