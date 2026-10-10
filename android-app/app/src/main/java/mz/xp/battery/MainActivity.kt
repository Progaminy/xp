package mz.xp.battery

import android.app.Activity
import android.os.BatteryManager
import android.os.Bundle
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.PowerManager
import android.provider.Settings
import android.graphics.Color
import android.view.Gravity
import android.widget.Button
import android.widget.LinearLayout
import android.widget.Switch
import android.widget.TextView
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import java.util.concurrent.TimeUnit

class MainActivity : Activity() {
    private lateinit var status: TextView
    private lateinit var optimizationStatus: TextView
    private lateinit var sharing: Switch
    private val prefs by lazy { getPreferences(Context.MODE_PRIVATE) }

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
        layout.addView(text("Estado da bateria", 17f))
        status = text("", 22f)
        layout.addView(status)

        optimizationStatus = text("", 15f)
        layout.addView(optimizationStatus)
        layout.addView(Button(this).apply {
            text = "Ativar acesso sem restrições à bateria"
            setOnClickListener { requestUnrestrictedBattery() }
        })
        layout.addView(text("O Android apresentará o ecrã oficial do sistema. Confirme a opção para permitir que o XP Battery funcione com menos restrições em segundo plano.", 14f))

        sharing = Switch(this).apply {
            text = "Ativar tarefa periódica local"
            setTextColor(Color.WHITE)
            setPadding(0, 20, 0, 20)
            isChecked = prefs.getBoolean("sharing_enabled", false)
        }
        layout.addView(sharing)
        layout.addView(text("A ligação ao painel web/servidor ainda não está configurada nesta versão.", 14f))
        setContentView(layout)

        refreshBattery()
        refreshOptimizationStatus()
        sharing.setOnCheckedChangeListener { _, enabled ->
            prefs.edit().putBoolean("sharing_enabled", enabled).apply()
            val wm = WorkManager.getInstance(this)
            if (enabled) {
                val request = PeriodicWorkRequestBuilder<BatteryWorker>(15, TimeUnit.MINUTES).build()
                wm.enqueueUniquePeriodicWork("xp_battery_sync", ExistingPeriodicWorkPolicy.UPDATE, request)
            } else {
                wm.cancelUniqueWork("xp_battery_sync")
            }
        }
    }

    override fun onResume() {
        super.onResume()
        if (::status.isInitialized) {
            refreshBattery()
            refreshOptimizationStatus()
        }
    }

    private fun requestUnrestrictedBattery() {
        val powerManager = getSystemService(POWER_SERVICE) as PowerManager
        if (powerManager.isIgnoringBatteryOptimizations(packageName)) {
            refreshOptimizationStatus()
            return
        }
        try {
            startActivity(
                Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS).apply {
                    data = Uri.parse("package:$packageName")
                }
            )
        } catch (_: Exception) {
            startActivity(Intent(Settings.ACTION_IGNORE_BATTERY_OPTIMIZATION_SETTINGS))
        }
    }

    private fun refreshOptimizationStatus() {
        val powerManager = getSystemService(POWER_SERVICE) as PowerManager
        optimizationStatus.text = if (powerManager.isIgnoringBatteryOptimizations(packageName)) {
            "Acesso sem restrições à bateria: ATIVADO"
        } else {
            "Acesso sem restrições à bateria: ainda não autorizado"
        }
    }

    private fun refreshBattery() {
        val manager = getSystemService(BATTERY_SERVICE) as BatteryManager
        val level = manager.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY)
        val charging = manager.isCharging
        status.text = if (level in 0..100) "$level%\n" + if (charging) "A carregar" else "Não está a carregar" else "Dados indisponíveis"
    }
}
