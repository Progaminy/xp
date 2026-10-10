# XP Battery (Android / Kotlin)

The Android app stores battery readings locally in SQLite. No Firebase project or cloud database is required.

## Current development implementation
- Shows battery percentage and charging state.
- Stores readings in `xp_battery.db`, private to the application.
- Stores the reporting toggle and interval locally.
- Runs a WorkManager periodic task when collection is enabled (Android minimum: 15 minutes; execution may be delayed by system battery policies).
- Starts the XP Admin local web panel/API on port 8765 while the app process is active.
- Displays the local network URL and an access code to enter in the browser on another phone.

## How to test
1. Build and install the debug APK.
2. Connect the Android phone to a trusted Wi-Fi network.
3. Open XP Battery and keep it running.
4. Note the local URL and access code shown in the app.
5. On another device on the same Wi-Fi, open that URL and enter the code.
6. Test reading the battery, changing the collection interval, and turning collection ON/OFF.

## Important limitations
- The LAN panel is a development implementation. HTTP traffic is not encrypted; use only on a trusted private network and never expose port 8765 to the public Internet.
- The server currently runs only while the app process is active.
- “Read now” is not guaranteed if Android has terminated the process.
- Verify the generated APK and test on a physical device before relying on it.

See `../docs/ARCHITECTURE.md` for architecture and limitations.
