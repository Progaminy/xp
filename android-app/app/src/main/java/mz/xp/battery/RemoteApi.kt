package mz.xp.battery

import android.content.Context
import android.os.BatteryManager
import android.os.Environment
import android.os.StatFs
import android.os.Build
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import java.util.UUID

data class RemoteSettings(val enabled: Boolean, val intervalMinutes: Int, val readNow: Boolean, val registered: Boolean = true)

class RemoteApi(private val context: Context) {
    private val prefs = context.getSharedPreferences("xp_remote", Context.MODE_PRIVATE)
    fun configured() = baseUrl().isNotBlank() && deviceKey().isNotBlank()
    fun baseUrl() = prefs.getString("base_url", "")?.trim()?.trimEnd('/') ?: ""
    fun deviceKey() = prefs.getString("device_key", "") ?: ""
    fun save(base: String, key: String) {
        prefs.edit().putString("base_url", base.trim().trimEnd('/')).putString("device_key", key.trim()).apply()
    }
    fun poll(deviceId: String): RemoteSettings {
        val response = call("/device/poll", JSONObject().put("deviceId", deviceId))
        return RemoteSettings(response.optBoolean("collectionEnabled", false),
            response.optInt("intervalMinutes", 15).coerceIn(15, 1440),
            response.optBoolean("readNowRequested", false), response.optBoolean("registered", true))
    }
    fun upload(deviceId: String): RemoteSettings {
        val manager = context.getSystemService(Context.BATTERY_SERVICE) as BatteryManager
        val percent = manager.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY)
        require(percent in 0..100) { "Nível da bateria indisponível" }
        val stat = StatFs(Environment.getDataDirectory().absolutePath)
        val total = stat.totalBytes
        val free = stat.availableBytes
        val used = (total - free).coerceAtLeast(0)
        val payload = JSONObject()
            .put("deviceId", deviceId)
            .put("deviceName", Build.MODEL.ifBlank { "Android" })
            .put("manufacturer", Build.MANUFACTURER)
            .put("model", Build.MODEL)
            .put("androidVersion", Build.VERSION.RELEASE ?: Build.VERSION.SDK_INT.toString())
            .put("batteryPercent", percent)
            .put("charging", manager.isCharging)
            .put("storageTotalBytes", total)
            .put("storageUsedBytes", used)
            .put("storageFreeBytes", free)
        val response = call("/device/snapshot", payload)
        return RemoteSettings(response.optBoolean("collectionEnabled", false),
            response.optInt("intervalMinutes", 15).coerceIn(15, 1440),
            response.optBoolean("readNowRequested", false))
    }
    private fun call(path: String, payload: JSONObject): JSONObject {
        val base = baseUrl()
        require(base.startsWith("https://")) { "O endereço da API deve usar HTTPS" }
        val connection = (URL(base + path).openConnection() as HttpURLConnection).apply {
            requestMethod = "POST"
            connectTimeout = 10000
            readTimeout = 10000
            doOutput = true
            setRequestProperty("Content-Type", "application/json; charset=utf-8")
            setRequestProperty("X-Device-Key", deviceKey())
        }
        try {
            connection.outputStream.use { it.write(payload.toString().toByteArray(Charsets.UTF_8)) }
            val code = connection.responseCode
            val stream = if (code in 200..299) connection.inputStream else connection.errorStream
            val body = stream?.bufferedReader()?.use { it.readText() }.orEmpty()
            if (code !in 200..299) throw IllegalStateException("API respondeu HTTP $code: $body")
            return JSONObject(body)
        } finally { connection.disconnect() }
    }
    companion object {
        fun deviceId(context: Context): String {
            val p = context.getSharedPreferences("xp_remote", Context.MODE_PRIVATE)
            return p.getString("device_id", null) ?: UUID.randomUUID().toString().also {
                p.edit().putString("device_id", it).apply()
            }
        }
    }
}
