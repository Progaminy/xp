package mz.xp.battery

import android.content.Context
import android.os.BatteryManager
import androidx.work.CoroutineWorker
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import java.util.concurrent.TimeUnit

/** Saves readings locally and synchronizes only when the paired remote admin has enabled collection. */
class BatteryWorker(context: Context, params: WorkerParameters) : CoroutineWorker(context, params) {
    override suspend fun doWork(): Result {
        val db = BatteryDatabase(applicationContext)
        return try {
            val remote = RemoteApi(applicationContext)
            val manager = applicationContext.getSystemService(Context.BATTERY_SERVICE) as BatteryManager
            if (remote.configured()) {
                val id = RemoteApi.deviceId(applicationContext)
                val settings = remote.poll(id)
                val schedulePrefs = applicationContext.getSharedPreferences("xp_remote", Context.MODE_PRIVATE)
                val savedInterval = schedulePrefs.getInt("scheduled_interval", 15)
                if (savedInterval != settings.intervalMinutes) {
                    val schedule = PeriodicWorkRequestBuilder<BatteryWorker>(
                        settings.intervalMinutes.toLong(), TimeUnit.MINUTES
                    ).build()
                    WorkManager.getInstance(applicationContext).enqueueUniquePeriodicWork(
                        "xp_battery_sync", ExistingPeriodicWorkPolicy.UPDATE, schedule
                    )
                    schedulePrefs.edit().putInt("scheduled_interval", settings.intervalMinutes).apply()
                }
                if (!settings.registered || settings.enabled || settings.readNow) {
                    val level = manager.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY)
                    if (level !in 0..100) return Result.retry()
                    db.saveSnapshot(level, manager.isCharging)
                    remote.upload(id)
                }
                Result.success()
            } else {
                val (enabled, _) = db.settings()
                if (!enabled) return Result.success()
                val level = manager.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY)
                if (level !in 0..100) return Result.retry()
                db.saveSnapshot(level, manager.isCharging)
                Result.success()
            }
        } catch (_: Exception) {
            Result.retry()
        } finally {
            db.close()
        }
    }
}
