# XP Battery API — Cloudflare Worker + D1

The API source and a GitHub Actions deployment workflow are included here. Deployment is not live until the owner supplies Cloudflare credentials and runs the workflow. Android SQLite remains the local history/cache; D1 is the remote store for cross-network admin access. No Firebase is used.

## One-time deployment (no command line needed)
1. In GitHub, open the Progaminy/xp repository, then Settings → Secrets and variables → Actions → New repository secret.
2. Add four secrets:
   - CLOUDFLARE_API_TOKEN: a Cloudflare API token allowed to manage Workers and D1 for this account.
   - CLOUDFLARE_ACCOUNT_ID: the Cloudflare account ID.
   - XP_ADMIN_KEY: a long, random admin password/key.
   - XP_DEVICE_KEY: a different long, random device key.
3. Open Actions → Deploy XP remote API → Run workflow on branch rewrite/kotlin-battery-v1.
4. When it finishes, copy the actual workers.dev API URL printed in the workflow log. Check that URL plus /health returns JSON with ok:true.

The workflow creates/reuses the D1 database, applies schema.sql, configures Worker secrets, and deploys the API. Never put real keys in repository files or screenshots.

## Connect the devices
1. Install XP Battery APK, enter the API URL and XP_DEVICE_KEY, then save. The app registers the device on its first sync.
2. Open https://progaminy.github.io/xp/ and enter the same API URL and XP_ADMIN_KEY.
3. Enable collection from the Admin. The Android app polls commands in the background (minimum interval 15 minutes) and uploads readings only when collection is enabled or a one-time reading is requested.

The app sends battery percentage/charging, manufacturer/model, Android version and internal storage totals. The Android operating system can delay background work. GitHub Pages alone cannot host the API or access the phone's private SQLite file.
