import express from "express";
import Database from "better-sqlite3";
import fs from "node:fs";
import path from "node:path";

const required = ["XP_ADMIN_KEY", "XP_DEVICE_KEY"];
for (const name of required) {
  if (!process.env[name]) {
    console.error(`Missing required environment variable: ${name}`);
    process.exit(1);
  }
}
const PORT = Number(process.env.PORT || 3000);
const DB_PATH = process.env.XP_DB_PATH || "/data/xp-battery.sqlite";
const ADMIN_ORIGIN = process.env.XP_ADMIN_ORIGIN || "https://progaminy.github.io";
fs.mkdirSync(path.dirname(DB_PATH), { recursive: true });

const db = new Database(DB_PATH);
db.pragma("journal_mode = WAL");
db.pragma("foreign_keys = ON");
db.exec(`
CREATE TABLE IF NOT EXISTS devices (
 id TEXT PRIMARY KEY,
 device_name TEXT NOT NULL DEFAULT 'Android',
 manufacturer TEXT NOT NULL DEFAULT '',
 model TEXT NOT NULL DEFAULT '',
 android_version TEXT NOT NULL DEFAULT '',
 battery_percent INTEGER,
 charging INTEGER NOT NULL DEFAULT 0,
 storage_total_bytes INTEGER NOT NULL DEFAULT 0,
 storage_used_bytes INTEGER NOT NULL DEFAULT 0,
 storage_free_bytes INTEGER NOT NULL DEFAULT 0,
 collection_enabled INTEGER NOT NULL DEFAULT 0,
 interval_minutes INTEGER NOT NULL DEFAULT 15,
 read_now_requested INTEGER NOT NULL DEFAULT 0,
 updated_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS battery_history (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 device_id TEXT NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
 percent INTEGER NOT NULL,
 charging INTEGER NOT NULL DEFAULT 0,
 recorded_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_battery_history_device_time ON battery_history(device_id, recorded_at DESC);
`);

const app = express();
app.disable("x-powered-by");
app.use(express.json({ limit: "32kb" }));
app.use((req, res, next) => {
  const origin = req.get("origin");
  if (origin === ADMIN_ORIGIN) {
    res.set("Access-Control-Allow-Origin", origin);
    res.set("Vary", "Origin");
    res.set("Access-Control-Allow-Headers", "authorization,content-type,x-device-key");
    res.set("Access-Control-Allow-Methods", "GET,POST,OPTIONS");
  }
  if (req.method === "OPTIONS") return res.sendStatus(204);
  next();
});

const jsonError = (res, status, error) => res.status(status).json({ error });
const deviceAuth = (req, res, next) => {
  if (req.get("x-device-key") !== process.env.XP_DEVICE_KEY) return jsonError(res, 401, "Dispositivo não autorizado");
  next();
};
const adminAuth = (req, res, next) => {
  const header = req.get("authorization") || "";
  const key = header.startsWith("Bearer ") ? header.slice(7) : "";
  if (key.length !== process.env.XP_ADMIN_KEY.length || !cryptoSafeEqual(key, process.env.XP_ADMIN_KEY)) {
    return jsonError(res, 401, "Acesso não autorizado");
  }
  next();
};
function cryptoSafeEqual(a, b) {
  // Constant-time comparison for same-length UTF-8 buffers.
  const { timingSafeEqual } = requireCrypto;
  const aa = Buffer.from(a); const bb = Buffer.from(b);
  return aa.length === bb.length && timingSafeEqual(aa, bb);
}
import { timingSafeEqual } from "node:crypto";
const requireCrypto = { timingSafeEqual };

app.get("/health", (_req, res) => res.json({ ok: true, service: "XP Battery API" }));

app.post("/device/poll", deviceAuth, (req, res) => {
  const id = String(req.body?.deviceId || "").trim();
  if (!id || id.length > 128) return jsonError(res, 400, "deviceId inválido");
  const row = db.prepare("SELECT collection_enabled, interval_minutes, read_now_requested FROM devices WHERE id=?").get(id);
  if (!row) return res.json({ collectionEnabled: false, intervalMinutes: 15, readNowRequested: false, registered: false });
  res.json({ collectionEnabled: Boolean(row.collection_enabled), intervalMinutes: row.interval_minutes, readNowRequested: Boolean(row.read_now_requested), registered: true });
});

app.post("/device/snapshot", deviceAuth, (req, res) => {
  const b = req.body || {};
  const id = String(b.deviceId || "").trim();
  const percent = Number(b.batteryPercent);
  if (!id || id.length > 128 || !Number.isInteger(percent) || percent < 0 || percent > 100) {
    return jsonError(res, 400, "Dados do dispositivo inválidos");
  }
  const now = Date.now();
  const save = db.transaction(() => {
    db.prepare(`INSERT INTO devices
      (id,device_name,manufacturer,model,android_version,battery_percent,charging,storage_total_bytes,storage_used_bytes,storage_free_bytes,updated_at)
      VALUES (@id,@device_name,@manufacturer,@model,@android_version,@battery_percent,@charging,@storage_total_bytes,@storage_used_bytes,@storage_free_bytes,@updated_at)
      ON CONFLICT(id) DO UPDATE SET device_name=excluded.device_name,manufacturer=excluded.manufacturer,model=excluded.model,android_version=excluded.android_version,battery_percent=excluded.battery_percent,charging=excluded.charging,storage_total_bytes=excluded.storage_total_bytes,storage_used_bytes=excluded.storage_used_bytes,storage_free_bytes=excluded.storage_free_bytes,updated_at=excluded.updated_at`).run({
      id, device_name: String(b.deviceName || "Android").slice(0,160), manufacturer: String(b.manufacturer || "").slice(0,160),
      model: String(b.model || "").slice(0,160), android_version: String(b.androidVersion || "").slice(0,80),
      battery_percent: percent, charging: b.charging ? 1 : 0,
      storage_total_bytes: safeBytes(b.storageTotalBytes), storage_used_bytes: safeBytes(b.storageUsedBytes),
      storage_free_bytes: safeBytes(b.storageFreeBytes), updated_at: now
    });
    db.prepare("INSERT INTO battery_history(device_id,percent,charging,recorded_at) VALUES(?,?,?,?)").run(id, percent, b.charging ? 1 : 0, now);
    db.prepare("UPDATE devices SET read_now_requested=0 WHERE id=?").run(id);
  });
  save();
  const row = db.prepare("SELECT collection_enabled,interval_minutes,read_now_requested FROM devices WHERE id=?").get(id);
  res.json({ ok: true, collectionEnabled: Boolean(row.collection_enabled), intervalMinutes: row.interval_minutes, readNowRequested: Boolean(row.read_now_requested) });
});
function safeBytes(value) {
  const n = Number(value || 0);
  return Number.isSafeInteger(n) && n >= 0 ? n : 0;
}

app.get("/admin/devices", adminAuth, (_req, res) => {
  res.json(db.prepare("SELECT * FROM devices ORDER BY updated_at DESC").all());
});
app.get("/admin/devices/:id", adminAuth, (req, res) => {
  const device = db.prepare("SELECT * FROM devices WHERE id=?").get(req.params.id);
  if (!device) return jsonError(res, 404, "Dispositivo não encontrado");
  const history = db.prepare("SELECT percent,charging,recorded_at FROM battery_history WHERE device_id=? ORDER BY recorded_at DESC LIMIT 100").all(req.params.id);
  res.json({ device, history });
});
app.post("/admin/devices/:id", adminAuth, (req, res) => {
  const b = req.body || {};
  const interval = Number(b.intervalMinutes);
  if (typeof b.enabled !== "boolean" || ![15,30,60,180,360,720,1440].includes(interval) || (b.readNow !== undefined && typeof b.readNow !== "boolean")) {
    return jsonError(res, 400, "Configuração inválida");
  }
  const result = db.prepare("UPDATE devices SET collection_enabled=?,interval_minutes=?,read_now_requested=? WHERE id=?")
    .run(b.enabled ? 1 : 0, interval, b.readNow ? 1 : 0, req.params.id);
  if (!result.changes) return jsonError(res, 404, "Dispositivo não encontrado");
  res.json({ ok: true });
});

app.use((err, _req, res, _next) => {
  if (err instanceof SyntaxError) return jsonError(res, 400, "JSON inválido");
  console.error("Request error:", err.message);
  return jsonError(res, 500, "Erro interno");
});
const server = app.listen(PORT, "0.0.0.0", () => console.log(`XP Battery API listening on port ${PORT}; SQLite: ${DB_PATH}`));
function shutdown() { server.close(() => { db.close(); process.exit(0); }); }
process.on("SIGTERM", shutdown);
process.on("SIGINT", shutdown);
