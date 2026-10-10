package mz.xp.battery

import android.content.Context
import org.json.JSONArray
import org.json.JSONObject
import java.io.BufferedReader
import java.io.InputStreamReader
import java.net.Inet4Address
import java.net.NetworkInterface
import java.net.ServerSocket
import java.net.Socket
import java.util.Collections
import java.util.concurrent.Executors
import java.util.concurrent.atomic.AtomicBoolean

/** Small same-origin HTTP API for a trusted local Wi-Fi network. */
class LocalAdminServer(
    private val context: Context,
    private val db: BatteryDatabase,
    private val accessToken: String,
    private val onReadNow: () -> Unit,
    private val onConfigChanged: (Boolean, Int) -> Unit
) {
    companion object { const val PORT = 8765 }
    private val running = AtomicBoolean(false)
    private val executor = Executors.newCachedThreadPool()
    @Volatile private var socket: ServerSocket? = null

    fun start(): Boolean {
        if (!running.compareAndSet(false, true)) return true
        return try {
            socket = ServerSocket(PORT, 20, java.net.InetAddress.getByName("0.0.0.0"))
            executor.execute {
                while (running.get()) {
                    try {
                        val client = socket?.accept() ?: break
                        executor.execute { handle(client) }
                    } catch (_: Exception) {
                        if (running.get()) stop()
                    }
                }
            }
            true
        } catch (_: Exception) {
            running.set(false)
            false
        }
    }

    fun stop() {
        running.set(false)
        try { socket?.close() } catch (_: Exception) {}
        socket = null
    }

    fun isRunning(): Boolean = running.get()

    fun localUrls(): List<String> = try {
        Collections.list(NetworkInterface.getNetworkInterfaces()).flatMap { network ->
            Collections.list(network.inetAddresses).filterIsInstance<Inet4Address>()
                .filter { !it.isLoopbackAddress && it.isSiteLocalAddress }
                .map { "http://" + it.hostAddress + ":" + PORT + "/" }
        }.distinct()
    } catch (_: Exception) { emptyList() }

    private fun handle(client: Socket) {
        client.use { s ->
            try {
                s.soTimeout = 5000
                val reader = BufferedReader(InputStreamReader(s.getInputStream(), Charsets.UTF_8))
                val requestLine = reader.readLine() ?: return
                val parts = requestLine.split(" ")
                if (parts.size < 2) { send(s, 400, "application/json", "{\"error\":\"Pedido inválido\"}"); return }
                val method = parts[0]
                val path = parts[1].substringBefore("?")
                val headers = mutableMapOf<String, String>()
                while (true) {
                    val line = reader.readLine() ?: break
                    if (line.isEmpty()) break
                    val colon = line.indexOf(':')
                    if (colon > 0) headers[line.substring(0, colon).trim().lowercase()] = line.substring(colon + 1).trim()
                }
                val length = (headers["content-length"]?.toIntOrNull() ?: 0).coerceIn(0, 8192)
                val body = CharArray(length)
                var count = 0
                while (count < length) {
                    val n = reader.read(body, count, length - count)
                    if (n <= 0) break
                    count += n
                }
                val payload = String(body, 0, count)

                if (method == "GET" && path == "/") {
                    send(s, 200, "text/html; charset=utf-8", page)
                    return
                }
                if (headers["authorization"] != "Bearer " + accessToken) {
                    send(s, 401, "application/json; charset=utf-8", "{\"error\":\"Código de acesso inválido\"}")
                    return
                }
                when {
                    method == "GET" && path == "/api/status" -> send(s, 200, "application/json; charset=utf-8", status().toString())
                    method == "GET" && path == "/api/config" -> {
                        val (enabled, interval) = db.settings()
                        send(s, 200, "application/json; charset=utf-8", JSONObject().put("enabled", enabled).put("intervalMinutes", interval).toString())
                    }
                    method == "GET" && path == "/api/history" -> {
                        val rows = JSONArray()
                        db.history(50).forEach { rows.put(snapshotJson(it)) }
                        send(s, 200, "application/json; charset=utf-8", rows.toString())
                    }
                    method == "POST" && path == "/api/config" -> {
                        try {
                            val obj = JSONObject(payload)
                            val interval = obj.optInt("intervalMinutes", 15)
                            if (interval !in listOf(15, 30, 60, 180, 360, 720, 1440)) {
                                send(s, 400, "application/json; charset=utf-8", "{\"error\":\"Intervalo inválido\"}")
                            } else {
                                val enabled = obj.optBoolean("enabled", false)
                                db.updateSettings(enabled, interval)
                                onConfigChanged(enabled, interval)
                                send(s, 200, "application/json; charset=utf-8", "{\"ok\":true}")
                            }
                        } catch (_: Exception) {
                            send(s, 400, "application/json; charset=utf-8", "{\"error\":\"Configuração inválida\"}")
                        }
                    }
                    method == "POST" && path == "/api/read-now" -> {
                        onReadNow()
                        send(s, 202, "application/json; charset=utf-8", "{\"ok\":true}")
                    }
                    else -> send(s, 404, "application/json; charset=utf-8", "{\"error\":\"Não encontrado\"}")
                }
            } catch (_: Exception) {
                try { send(s, 400, "application/json; charset=utf-8", "{\"error\":\"Pedido inválido\"}") } catch (_: Exception) {}
            }
        }
    }

    private fun status(): JSONObject {
        val latest = db.latest()
        val (enabled, interval) = db.settings()
        return JSONObject()
            .put("connected", true)
            .put("enabled", enabled)
            .put("intervalMinutes", interval)
            .put("battery", latest?.let { snapshotJson(it) } ?: JSONObject.NULL)
    }

    private fun snapshotJson(item: BatterySnapshot) = JSONObject()
        .put("percent", item.percent)
        .put("charging", item.charging)
        .put("updatedAt", item.updatedAt)

    private fun send(client: Socket, code: Int, type: String, body: String) {
        val bytes = body.toByteArray(Charsets.UTF_8)
        val reason = when (code) { 200 -> "OK"; 202 -> "Accepted"; 400 -> "Bad Request"; 401 -> "Unauthorized"; 404 -> "Not Found"; else -> "Error" }
        val headers = "HTTP/1.1 " + code + " " + reason + "\r\n" +
            "Content-Type: " + type + "\r\n" +
            "Content-Length: " + bytes.size + "\r\n" +
            "Cache-Control: no-store\r\nConnection: close\r\n\r\n"
        client.getOutputStream().apply {
            write(headers.toByteArray(Charsets.ISO_8859_1))
            write(bytes)
            flush()
        }
    }

    private val page = """
<!doctype html><html lang="pt"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>XP Admin</title>
<style>
:root{color-scheme:dark;--bg:#0b1220;--panel:#121c2e;--line:#27364d;--text:#eef4ff;--muted:#9baec8;--accent:#60a5fa;--green:#34d399}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:16px system-ui,sans-serif}main{max-width:760px;margin:auto;padding:24px 16px}h1{margin:0}p{color:var(--muted)}.card{background:var(--panel);border:1px solid var(--line);border-radius:18px;padding:18px;margin:14px 0}label{display:block;color:var(--muted);margin:14px 0 7px}input,select,button{font:inherit;border-radius:10px;padding:12px;border:1px solid var(--line);width:100%;background:#0d1727;color:var(--text)}button{cursor:pointer;background:var(--accent);color:#071323;font-weight:700;margin-top:12px;border:0}.big{font-size:2.8rem;font-weight:800}.notice{border-left:3px solid var(--accent);padding:10px;background:#10223a;border-radius:8px}.muted{color:var(--muted);font-size:.9rem;white-space:pre-line}
</style></head><body><main><h1>XP Admin</h1><p>Administração local da bateria</p>
<section class="card"><h2>Bateria do dispositivo</h2><div class="big" id="percent">—%</div><p id="charging">A obter dados…</p><p id="updated" class="muted">Última atualização: —</p></section>
<section class="card"><h2>Recolha de bateria</h2><label for="token">Código de acesso mostrado no XP Battery</label><input id="token" type="password" autocomplete="current-password" placeholder="Código de acesso"><label for="enabled">Recolha automática</label><select id="enabled"><option value="false">OFF — parar recolha</option><option value="true">ON — recolher bateria</option></select><label for="interval">Intervalo de recolha</label><select id="interval"><option value="15">15 minutos</option><option value="30">30 minutos</option><option value="60">1 hora</option><option value="180">3 horas</option><option value="360">6 horas</option><option value="720">12 horas</option><option value="1440">24 horas</option></select><button id="save">Guardar configurações</button><button id="now">Solicitar leitura agora</button><p class="notice" id="message">Introduz o código para ligar ao telefone.</p><p class="muted">Utiliza apenas numa rede Wi-Fi de confiança. O HTTP local não cifra o tráfego.</p></section>
<section class="card"><h2>Histórico recente</h2><div id="history" class="muted">Sem dados ainda.</div></section></main>
<script>
const el=id=>document.getElementById(id);const token=el('token');token.value=sessionStorage.getItem('xpAdminToken')||'';
function headers(){return {'Authorization':'Bearer '+token.value,'Content-Type':'application/json'};}
async function api(path,options={}){const response=await fetch(path,{...options,headers:headers()});if(!response.ok)throw new Error(response.status===401?'Código incorreto':'Falha na ligação ('+response.status+')');return response.json();}
async function refresh(){if(!token.value)return;try{sessionStorage.setItem('xpAdminToken',token.value);const d=await api('/api/status');if(d.battery){el('percent').textContent=d.battery.percent+'%';el('charging').textContent=d.battery.charging?'A carregar':'Não está a carregar';el('updated').textContent='Última atualização: '+new Date(d.battery.updatedAt).toLocaleString();}else{el('percent').textContent='—%';el('charging').textContent='Ainda não há leituras guardadas';}el('message').textContent='Ligação ativa ao telefone.';const c=await api('/api/config');el('enabled').value=String(c.enabled);el('interval').value=String(c.intervalMinutes);const h=await api('/api/history');el('history').textContent=h.length?h.slice(0,10).map(x=>new Date(x.updatedAt).toLocaleString()+' — '+x.percent+'%'+(x.charging?' (a carregar)':'')).join('\n'):'Sem dados ainda.';}catch(e){el('message').textContent=e.message;}}
token.addEventListener('change',refresh);el('save').onclick=async()=>{try{await api('/api/config',{method:'POST',body:JSON.stringify({enabled:el('enabled').value==='true',intervalMinutes:Number(el('interval').value)})});el('message').textContent='Configuração guardada no telefone.';}catch(e){el('message').textContent=e.message;}};
el('now').onclick=async()=>{try{await api('/api/read-now',{method:'POST',body:'{}'});el('message').textContent='Pedido de leitura recebido.';}catch(e){el('message').textContent=e.message;}};
refresh();setInterval(refresh,15000);
</script></body></html>
""".trimIndent()
}
