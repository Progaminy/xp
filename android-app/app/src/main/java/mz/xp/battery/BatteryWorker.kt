package mz.xp.battery

import android.content.Context
import android.os.BatteryManager
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters

/**
 * Background worker scaffold. Remote upload is intentionally not enabled until
 * the authenticated backend and per-device consent rules are configured.
 */
class BatteryWorker(context: Context, params: WorkerParameters) : CoroutineWorker(context, params) {
    override suspend fun doWork(): Result {
        val enabled = applicationContext
            .getSharedPreferences("MainActivity", Context.MODE_PRIVATE)
            .getBoolean("sharing_enabled", false)
        if (!enabled) return Result.success()

        val manager = applicationContext.getSystemService(Context.BATTERY_SERVICE) as BatteryManager
        val level = manager.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY)
        // Next implementation step: upload only approved battery fields over HTTPS.
        // Never add location, messages, or other data without explicit opt-in.
        return if (level in 0..100) Result.success() else Result.retry()
    }
}
