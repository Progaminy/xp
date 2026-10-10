package mz.xp.battery

import android.app.Activity
import android.os.BatteryManager
import android.os.Bundle
import android.content.Context
import android.graphics.Color
import android.view.Gravity
import android.widget.LinearLayout
import android.widget.Switch
import android.widget.TextView
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import java.util.concurrent.TimeUnit

class MainActivity : Activity() {
    private lateinit var status: TextView
    private lateinit var sharing: Switch

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val pad = (24 * resources.displayMetrics.density).toInt()
        val layout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER_VERTICAL
            setPadding(pad, pad, pad, pad)
            setBackgroundColor(Color.rgb(11, 18, 32))
        }
        fun text(value: String, size: Float) = TextView(this).apply {
            text = value
            textSize = size
            setTextColor(Color.WHITE)
            setPadding(0, 12, 0, 12)
        }
        layout.addView(text("XP Battery", 28f))
        layout.addView(text("Estado atual do aparelho", 17f))
        status = text("", 22f)
        layout.addView(status)
        sharing = Switch(this).apply {
            text = "Permitir partilha periódica da bateria"
            setTextColor(Color.WHITE)
            setPadding(0, 20, 0, 20)
            isChecked = getPreferences(Context.MODE_PRIVATE).getBoolean("sharing_enabled", false)
        }
        layout.addView(sharing)
        layout.addView(text("A partilha remota será ativada depois de configurar o servidor seguro. Este controlo guarda apenas a preferência local nesta versão.", 14f))
        setContentView(layout)
        refreshBattery()
        sharing.setOnCheckedChangeListener { _, enabled ->
            getPreferences(Context.MODE_PRIVATE).edit().putBoolean("sharing_enabled", enabled).apply()
            val wm = WorkManager.getInstance(this)
            if (enabled) {
                val request = PeriodicWorkRequestBuilder<BatteryWorker>(15, TimeUnit.MINUTES).build()
                wm.enqueueUniquePeriodicWork("xp_battery_sync", ExistingPeriodicWorkPolicy.UPDATE, request)
            } else {
                wm.cancelUniqueWork("xp_battery_sync")
            }
        }
    }

    private fun refreshBattery() {
        val manager = getSystemService(BATTERY_SERVICE) as BatteryManager
        val level = manager.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY)
        val charging = manager.isCharging
        status.text = if (level in 0..100) "$level%\n" + if (charging) "A carregar" else "Não está a carregar" else "Dados indisponíveis"
    }
}
