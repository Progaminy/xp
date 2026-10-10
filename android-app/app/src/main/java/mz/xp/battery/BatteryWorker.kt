package mz.xp.battery

import android.content.Context
import android.os.BatteryManager
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters

/** Periodically stores only the explicitly scoped battery state on this device. */
class BatteryWorker(context: Context, params: WorkerParameters) : CoroutineWorker(context, params) {
    override suspend fun doWork(): Result {
        val database = BatteryDatabase(applicationContext)
        return try {
            val (enabled, _) = database.settings()
            if (!enabled) return Result.success()
            val manager = applicationContext.getSystemService(Context.BATTERY_SERVICE) as BatteryManager
            val level = manager.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY)
            if (level !in 0..100) return Result.retry()
            database.saveSnapshot(level, manager.isCharging)
            Result.success()
        } catch (_: Exception) {
            Result.retry()
        } finally {
            database.close()
        }
    }
}
