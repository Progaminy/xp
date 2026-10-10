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
import android.text.InputType
import android.view.Gravity
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.Switch
import android.widget.TextView
import android.widget.Toast
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
 private lateinit var apiUrl: EditText
 private lateinit var deviceKey: EditText
 private val prefs by lazy { getPreferences(Context.MODE_PRIVATE) }
 private val adminPrefs by lazy { getSharedPreferences("xp_admin", Context.MODE_PRIVATE) }
 private val database by lazy { BatteryDatabase(this) }
 private val remote by lazy { RemoteApi(this) }
 private var adminServer: LocalAdminServer? = null

 override fun onCreate(savedInstanceState: Bundle?) {
  super.onCreate(savedInstanceState)
  val pad=(20*resources.displayMetrics.density).toInt()
  val layout=LinearLayout(this).apply { orientation=LinearLayout.VERTICAL;gravity=Gravity.CENTER_VERTICAL;setPadding(pad,pad,pad,pad);setBackgroundColor(Color.rgb(11,18,32)) }
  fun text(value:String,size:Float)=TextView(this).apply { text=value;textSize=size;setTextColor(Color.WHITE);setPadding(0,8,0,8) }
  fun field(hintText:String,value:String="",secret:Boolean=false)=EditText(this).apply { hint=hintText;setText(value);textSize=14f;setSingleLine(true);setTextColor(Color.WHITE);setHintTextColor(Color.LTGRAY);setPadding(18,8,18,8);setBackgroundColor(Color.rgb(23,34,52));if(secret)inputType=InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_VARIATION_PASSWORD }
  layout.addView(text("XP Battery",28f))
  layout.addView(text("Estado da bateria",17f))
  status=text("",22f);layout.addView(status)
  optimizationStatus=text("",14f);layout.addView(optimizationStatus)
  layout.addView(Button(this).apply { text="Ativar acesso sem restrições à bateria";setOnClickListener { requestUnrestrictedBattery() } })
  layout.addView(text("A autorização é feita no ecrã oficial do Android.",13f))
  layout.addView(text("Ligação ao XP Admin pela Internet",19f))
  layout.addView(text("Introduz o URL HTTPS da API e a chave de dispositivo configurada no servidor.",13f))
  apiUrl=field("URL HTTPS da API",remote.baseUrl().ifBlank { "https://xp-battery-api.pensadorsemfronteiras0.workers.dev" });layout.addView(apiUrl)
  deviceKey=field("Chave do dispositivo (DEVICE_KEY)",remote.deviceKey(),true);layout.addView(deviceKey)
  layout.addView(Button(this).apply {
   text="Guardar ligação e ativar sincronização"
   setOnClickListener {
    val base=apiUrl.text.toString().trim().trimEnd('/');val key=deviceKey.text.toString().trim()
    if(!base.startsWith("https://")||key.isBlank()) Toast.makeText(this@MainActivity,"Indica um URL HTTPS e a chave do dispositivo.",Toast.LENGTH_LONG).show()
    else { remote.save(base,key);scheduleRemote();Toast.makeText(this@MainActivity,"Ligação guardada. O telefone será registado na próxima sincronização.",Toast.LENGTH_LONG).show();serverInfo.text="Sincronização remota agendada. No XP Admin usa a chave ADMIN_KEY." }
   }
  })
  sharing=Switch(this).apply { text="Ativar recolha local se não houver API remota";setTextColor(Color.WHITE);setPadding(0,12,0,12);isChecked=database.settings().first };layout.addView(sharing)
  serverInfo=text("O estado da ligação será mostrado aqui.",13f);layout.addView(serverInfo)
  layout.addView(text("Dados enviados: bateria, carregamento, fabricante/modelo, Android e armazenamento. A recolha remota é controlada pelo XP Admin.",13f))
  setContentView(ScrollView(this).apply { addView(layout) })
  refreshBattery();refreshOptimizationStatus();startAdminServer()
  if(remote.configured()){scheduleRemote();serverInfo.text="API configurada: "+remote.baseUrl()+"\nSincronização em segundo plano ativa."}
  sharing.setOnCheckedChangeListener { _,enabled -> database.updateSettings(enabled,database.settings().second);prefs.edit().putBoolean("sharing_enabled",enabled).apply();applySchedule(enabled,database.settings().second) }
 }
 private fun startAdminServer() {
  val token=adminPrefs.getString("access_token",null)?:UUID.randomUUID().toString().replace("-","").also{adminPrefs.edit().putString("access_token",it).apply()}
  adminServer=LocalAdminServer(this,database,token,onReadNow={runOnUiThread{refreshBattery()}},onConfigChanged={enabled,interval->runOnUiThread{
   if(sharing.isChecked!=enabled){sharing.setOnCheckedChangeListener(null);sharing.isChecked=enabled;sharing.setOnCheckedChangeListener{_,value->database.updateSettings(value,database.settings().second);applySchedule(value,database.settings().second)}}
   applySchedule(enabled,interval)
  }})
  val started=adminServer?.start()==true;val urls=adminServer?.localUrls().orEmpty()
  serverInfo.text=if(started&&urls.isNotEmpty())"Servidor local (opcional):\n"+urls.joinToString("\n")+"\nCódigo local: "+token else if(started)"Servidor local ativo na porta 8765. Código local: "+token else "Servidor local indisponível; a ligação remota usa a API HTTPS."
 }
 private fun scheduleRemote(){val req=PeriodicWorkRequestBuilder<BatteryWorker>(15,TimeUnit.MINUTES).build();WorkManager.getInstance(this).enqueueUniquePeriodicWork("xp_battery_sync",ExistingPeriodicWorkPolicy.UPDATE,req)}
 private fun applySchedule(enabled:Boolean,intervalMinutes:Int){
  if(remote.configured()){scheduleRemote();return}
  val wm=WorkManager.getInstance(this)
  if(enabled){val req=PeriodicWorkRequestBuilder<BatteryWorker>(intervalMinutes.coerceIn(15,1440).toLong(),TimeUnit.MINUTES).build();wm.enqueueUniquePeriodicWork("xp_battery_sync",ExistingPeriodicWorkPolicy.UPDATE,req)}else wm.cancelUniqueWork("xp_battery_sync")
 }
 override fun onResume(){super.onResume();if(::status.isInitialized){refreshBattery();refreshOptimizationStatus()}}
 override fun onDestroy(){adminServer?.stop();database.close();super.onDestroy()}
 private fun requestUnrestrictedBattery(){
  val pm=getSystemService(POWER_SERVICE) as PowerManager
  if(pm.isIgnoringBatteryOptimizations(packageName)){refreshOptimizationStatus();return}
  try{startActivity(Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS).apply{data=Uri.parse("package:$packageName")})}catch(_:Exception){startActivity(Intent(Settings.ACTION_IGNORE_BATTERY_OPTIMIZATION_SETTINGS))}
 }
 private fun refreshOptimizationStatus(){val pm=getSystemService(POWER_SERVICE) as PowerManager;optimizationStatus.text=if(pm.isIgnoringBatteryOptimizations(packageName))"Acesso sem restrições à bateria: ATIVADO" else "Acesso sem restrições à bateria: ainda não autorizado"}
 private fun refreshBattery(){
  val manager=getSystemService(BATTERY_SERVICE) as BatteryManager;val level=manager.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY);val charging=manager.isCharging
  if(level in 0..100){database.saveSnapshot(level,charging);status.text="$level%\n"+if(charging)"A carregar" else "Não está a carregar"}else status.text="Dados indisponíveis"
 }
}
