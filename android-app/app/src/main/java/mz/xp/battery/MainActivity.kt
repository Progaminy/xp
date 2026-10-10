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
import java.util.UUID
import java.util.concurrent.TimeUnit

class MainActivity : Activity() {
    private lateinit var status: TextView
    private lateinit var optimizationStatus: TextView
    private lateinit var serverInfo: TextView
    private lateinit var sharing: Switch
    private val prefs by lazy { getPreferences(Context.MODE_PRIVATE) }
    private val adminPrefs by lazy { getSharedPreferences("xp_admin", Context.MODE_PRIVATE) }
    private val database by lazy { BatteryDatabase(this) }
    private var adminServer: LocalAdminServer? = null

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
        layout.addView(text("O Android apresentará o ecrã oficial do sistema. O sistema pode limitar tarefas em segundo plano.", 14f))

        sharing = Switch(this).apply {
            text = "Ativar recolha periódica local"
            setTextColor(Color.WHITE)
            setPadding(0, 20, 0, 20)
            isChecked = database.settings().first
        }
        layout.addView(sharing)
        serverInfo = text("A iniciar servidor local…", 14f)
        layout.addView(serverInfo)
        layout.addView(text("Mantém esta aplicação aberta para disponibilizar o painel na rede local. Usa apenas uma rede Wi-Fi de confiança.", 13f))
        setContentView(layout)

        refreshBattery()
        refreshOptimizationStatus()
        startAdminServer()

        sharing.setOnCheckedChangeListener { _, enabled ->
            database.updateSettings(enabled, database.settings().second)
            prefs.edit().putBoolean("sharing_enabled", enabled).apply()
            applySchedule(enabled, database.settings().second)
        }
    }

    private fun startAdminServer() {
        val token = adminPrefs.getString("access_token", null) ?: UUID.randomUUID().toString().replace("-", "").also {
            adminPrefs.edit().putString("access_token", it).apply()
        }
        adminServer = LocalAdminServer(
            this,
            database,
            token,
            onReadNow = { runOnUiThread { refreshBattery() } },
            onConfigChanged = { enabled, interval -> runOnUiThread {
                if (sharing.isChecked != enabled) {
                    sharing.setOnCheckedChangeListener(null)
                    sharing.isChecked = enabled
                    sharing.setOnCheckedChangeListener { _, value ->
                        database.updateSettings(value, database.settings().second)
                        applySchedule(value, database.settings().second)
                    }
                }
                applySchedule(enabled, interval)
            } }
        )
        val started = adminServer?.start() == true
        val urls = adminServer?.localUrls().orEmpty()
        serverInfo.text = if (started && urls.isNotEmpty()) {
            "Painel XP Admin (mesma rede Wi-Fi):\n" + urls.joinToString("\n") +
                "\n\nCódigo de acesso (introduz no navegador):\n" + token
        } else if (started) {
            "Servidor ativo na porta 8765. Liga o telefone a uma rede Wi-Fi para ver o endereço local.\nCódigo de acesso: " + token
        } else {
            "Não foi possível iniciar o servidor local na porta 8765. Fecha outra aplicação que possa estar a usar essa porta."
        }
    }

    private fun applySchedule(enabled: Boolean, intervalMinutes: Int) {
        val wm = WorkManager.getInstance(this)
        if (enabled) {
            val minutes = intervalMinutes.coerceIn(15, 1440).toLong()
            val request = PeriodicWorkRequestBuilder<BatteryWorker>(minutes, TimeUnit.MINUTES).build()
            wm.enqueueUniquePeriodicWork("xp_battery_sync", ExistingPeriodicWorkPolicy.UPDATE, request)
        } else {
            wm.cancelUniqueWork("xp_battery_sync")
        }
    }

    override fun onResume() {
        super.onResume()
        if (::status.isInitialized) {
            refreshBattery()
            refreshOptimizationStatus()
        }
    }

    override fun onDestroy() {
        adminServer?.stop()
        database.close()
        super.onDestroy()
    }

    private fun requestUnrestrictedBattery() {
        val powerManager = getSystemService(POWER_SERVICE) as PowerManager
        if (powerManager.isIgnoringBatteryOptimizations(packageName)) {
            refreshOptimizationStatus()
            return
        }
        try {
            startActivity(Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS).apply {
                data = Uri.parse("package:$packageName")
            })
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
        if (level in 0..100) {
            database.saveSnapshot(level, charging)
            status.text = "$level%\n" + if (charging) "A carregar" else "Não está a carregar"
        } else {
            status.text = "Dados indisponíveis"
        }
    }
}
