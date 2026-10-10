const json=(data,status=200)=>new Response(JSON.stringify(data),{status,headers:{"content-type":"application/json; charset=utf-8","cache-control":"no-store","access-control-allow-origin":"https://progaminy.github.io","access-control-allow-headers":"authorization,content-type,x-device-key","access-control-allow-methods":"GET,POST,OPTIONS"}});
const unauthorized=()=>json({error:"Acesso não autorizado"},401);
const bearer=req=>(req.headers.get("authorization")||"").replace(/^Bearer\\s+/i,"");
export default { async fetch(req,env) {
 const url=new URL(req.url);
 if(req.method==="OPTIONS")return new Response(null,{headers:{"access-control-allow-origin":"https://progaminy.github.io","access-control-allow-headers":"authorization,content-type,x-device-key","access-control-allow-methods":"GET,POST,OPTIONS"}});
 if(url.pathname==="/health")return json({ok:true,service:"XP Battery API"});
 if(url.pathname.startsWith("/device/")) {
  if(!env.DEVICE_KEY||req.headers.get("x-device-key")!==env.DEVICE_KEY)return unauthorized();
  if(url.pathname==="/device/poll"&&req.method==="POST") {
   let b;try{b=await req.json()}catch{return json({error:"JSON inválido"},400)}
   if(!b.deviceId)return json({error:"deviceId obrigatório"},400);
   const d=await env.DB.prepare("SELECT collection_enabled,interval_minutes,read_now_requested FROM devices WHERE id=?").bind(String(b.deviceId)).first();
   if(!d)return json({collectionEnabled:false,intervalMinutes:15,readNowRequested:false,registered:false});
   return json({collectionEnabled:!!d.collection_enabled,intervalMinutes:d.interval_minutes,readNowRequested:!!d.read_now_requested,registered:true});
  }
  if(url.pathname==="/device/snapshot"&&req.method==="POST") {
   let b;try{b=await req.json()}catch{return json({error:"JSON inválido"},400)}
   if(!b.deviceId||!Number.isInteger(b.batteryPercent)||b.batteryPercent<0||b.batteryPercent>100)return json({error:"Dados inválidos"},400);
   const now=Date.now();
   await env.DB.prepare("INSERT INTO devices(id,device_name,manufacturer,model,android_version,battery_percent,charging,storage_total_bytes,storage_used_bytes,storage_free_bytes,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET device_name=excluded.device_name,manufacturer=excluded.manufacturer,model=excluded.model,android_version=excluded.android_version,battery_percent=excluded.battery_percent,charging=excluded.charging,storage_total_bytes=excluded.storage_total_bytes,storage_used_bytes=excluded.storage_used_bytes,storage_free_bytes=excluded.storage_free_bytes,updated_at=excluded.updated_at").bind(String(b.deviceId),String(b.deviceName||"Android"),String(b.manufacturer||""),String(b.model||""),String(b.androidVersion||""),b.batteryPercent,b.charging?1:0,Number(b.storageTotalBytes||0),Number(b.storageUsedBytes||0),Number(b.storageFreeBytes||0),now).run();
   await env.DB.prepare("INSERT INTO battery_history(device_id,percent,charging,recorded_at) VALUES(?,?,?,?)").bind(String(b.deviceId),b.batteryPercent,b.charging?1:0,now).run();
   const d=await env.DB.prepare("SELECT collection_enabled,interval_minutes,read_now_requested FROM devices WHERE id=?").bind(String(b.deviceId)).first();
   return json({ok:true,collectionEnabled:!!d.collection_enabled,intervalMinutes:d.interval_minutes,readNowRequested:!!d.read_now_requested});
  }
  return json({error:"Não encontrado"},404);
 }
 if(!env.ADMIN_KEY||bearer(req)!==env.ADMIN_KEY)return unauthorized();
 if(url.pathname==="/admin/devices"&&req.method==="GET")return json((await env.DB.prepare("SELECT * FROM devices ORDER BY updated_at DESC").all()).results);
 if(url.pathname.startsWith("/admin/devices/")) {
  const id=decodeURIComponent(url.pathname.split("/")[3]||"");
  if(req.method==="GET"){const device=await env.DB.prepare("SELECT * FROM devices WHERE id=?").bind(id).first();if(!device)return json({error:"Dispositivo não encontrado"},404);const history=await env.DB.prepare("SELECT percent,charging,recorded_at FROM battery_history WHERE device_id=? ORDER BY recorded_at DESC LIMIT 100").bind(id).all();return json({device,history:history.results})}
  if(req.method==="POST"){let b;try{b=await req.json()}catch{return json({error:"JSON inválido"},400)}if(typeof b.enabled!=="boolean"||![15,30,60,180,360,720,1440].includes(Number(b.intervalMinutes)))return json({error:"Configuração inválida"},400);const r=await env.DB.prepare("UPDATE devices SET collection_enabled=?,interval_minutes=?,read_now_requested=? WHERE id=?").bind(b.enabled?1:0,Number(b.intervalMinutes),b.readNow?1:0,id).run();return json({ok:r.meta.changes>0})}
 }
 return json({error:"Não encontrado"},404);
}};