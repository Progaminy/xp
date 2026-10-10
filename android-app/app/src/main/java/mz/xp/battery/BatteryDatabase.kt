package mz.xp.battery

import android.content.ContentValues
import android.content.Context
import android.database.sqlite.SQLiteDatabase
import android.database.sqlite.SQLiteOpenHelper

data class BatterySnapshot(
    val percent: Int,
    val charging: Boolean,
    val updatedAt: Long
)

/** Private, on-device SQLite storage for battery readings and admin settings. */
class BatteryDatabase(context: Context) : SQLiteOpenHelper(context, "xp_battery.db", null, 1) {
    override fun onCreate(db: SQLiteDatabase) {
        db.execSQL("""
            CREATE TABLE battery_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                percent INTEGER NOT NULL CHECK(percent BETWEEN 0 AND 100),
                charging INTEGER NOT NULL,
                recorded_at INTEGER NOT NULL
            )
        """.trimIndent())
        db.execSQL("""
            CREATE TABLE settings (
                id INTEGER PRIMARY KEY CHECK(id = 1),
                sharing_enabled INTEGER NOT NULL DEFAULT 0,
                interval_minutes INTEGER NOT NULL DEFAULT 15
            )
        """.trimIndent())
        db.execSQL("INSERT INTO settings(id, sharing_enabled, interval_minutes) VALUES(1, 0, 15)")
    }

    override fun onUpgrade(db: SQLiteDatabase, oldVersion: Int, newVersion: Int) = Unit

    @Synchronized
    fun saveSnapshot(percent: Int, charging: Boolean, at: Long = System.currentTimeMillis()) {
        if (percent !in 0..100) return
        writableDatabase.insert("battery_history", null, ContentValues().apply {
            put("percent", percent)
            put("charging", if (charging) 1 else 0)
            put("recorded_at", at)
        })
        writableDatabase.execSQL("""
            DELETE FROM battery_history WHERE id NOT IN
            (SELECT id FROM battery_history ORDER BY recorded_at DESC LIMIT 2000)
        """.trimIndent())
    }

    @Synchronized
    fun latest(): BatterySnapshot? = readableDatabase.rawQuery(
        "SELECT percent, charging, recorded_at FROM battery_history ORDER BY recorded_at DESC LIMIT 1", null
    ).use { cursor ->
        if (!cursor.moveToFirst()) null
        else BatterySnapshot(cursor.getInt(0), cursor.getInt(1) == 1, cursor.getLong(2))
    }

    @Synchronized
    fun settings(): Pair<Boolean, Int> = readableDatabase.rawQuery(
        "SELECT sharing_enabled, interval_minutes FROM settings WHERE id=1", null
    ).use { cursor ->
        if (!cursor.moveToFirst()) false to 15
        else (cursor.getInt(0) == 1) to cursor.getInt(1)
    }

    @Synchronized
    fun updateSettings(enabled: Boolean, intervalMinutes: Int) {
        val allowed = setOf(15, 30, 60, 180, 360, 720, 1440)
        val interval = if (intervalMinutes in allowed) intervalMinutes else 15
        writableDatabase.update("settings", ContentValues().apply {
            put("sharing_enabled", if (enabled) 1 else 0)
            put("interval_minutes", interval)
        }, "id=1", null)
    }

    @Synchronized
    fun history(limit: Int = 50): List<BatterySnapshot> {
        val rows = mutableListOf<BatterySnapshot>()
        readableDatabase.rawQuery(
            "SELECT percent, charging, recorded_at FROM battery_history ORDER BY recorded_at DESC LIMIT ?",
            arrayOf(limit.coerceIn(1, 200).toString())
        ).use { cursor ->
            while (cursor.moveToNext()) {
                rows += BatterySnapshot(cursor.getInt(0), cursor.getInt(1) == 1, cursor.getLong(2))
            }
        }
        return rows
    }
}
