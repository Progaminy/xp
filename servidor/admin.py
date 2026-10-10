#!/usr/bin/env python3
"""Painel administrativo XP para Termux. Ouve apenas em localhost."""
import hashlib
import hmac
import html
import json
import os
import secrets
import subprocess
import time
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs

HOST = "127.0.0.1"
PORT = 8080  # O túnel do guardiao/notificador.py já encaminha esta porta.
SESSION_COOKIE = "__Host-xp_admin"
CSRF_COOKIE = "__Host-xp_csrf"
SESSION_TTL = 30 * 60
LOCK_SECONDS = 15 * 60
MAX_FAILURES = 5
MAX_BODY = 4096
FAILURES = {}

ADMIN_USER = os.environ.get("XP_ADMIN_USERNAME", "")
ADMIN_PASSWORD = os.environ.get("XP_ADMIN_PASSWORD", "")
SESSION_SECRET = os.environ.get("XP_ADMIN_SECRET", "")

def check_config():
    if not ADMIN_USER or len(ADMIN_USER) > 128:
        raise SystemExit("Configuração ausente: define XP_ADMIN_USERNAME.")
    if len(ADMIN_PASSWORD) < 16:
        raise SystemExit("XP_ADMIN_PASSWORD deve ter pelo menos 16 caracteres.")
    if len(SESSION_SECRET) < 32:
        raise SystemExit("XP_ADMIN_SECRET deve ter pelo menos 32 caracteres aleatórios.")

def cookie_value(handler, name):
    jar = SimpleCookie()
    try:
        jar.load(handler.headers.get("Cookie", ""))
        return jar[name].value if name in jar else ""
    except Exception:
        return ""

def cookie_header(name, value, *, http_only=True, max_age=None):
    # O prefixo __Host- exige Secure, Path=/ e ausência de Domain.
    parts = [f"{name}={value}", "Path=/", "Secure", "SameSite=Strict"]
    if http_only:
        parts.append("HttpOnly")
    if max_age is not None:
        parts.append(f"Max-Age={max_age}")
    return "; ".join(parts)

def signed_session(csrf):
    issued = str(int(time.time()))
    payload = f"{issued}.{csrf}"
    mac = hmac.new(SESSION_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{mac}"

def verify_session(handler):
    token = cookie_value(handler, SESSION_COOKIE)
    try:
        issued, csrf, supplied_mac = token.split(".", 2)
        age = int(time.time()) - int(issued)
        payload = f"{issued}.{csrf}"
        expected = hmac.new(SESSION_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
        valid = hmac.compare_digest(supplied_mac, expected)
        if valid and 0 <= age <= SESSION_TTL and len(csrf) == 64:
            return csrf
    except (ValueError, TypeError):
        pass
    return None

def termux_json(command, timeout=12):
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=True)
        return json.loads(result.stdout)
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
        return None

def page(title, body):
    return """<!doctype html>
<html lang="pt">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>""" + html.escape(title) + """ · XP Admin</title>
<style>
:root{color-scheme:dark;--bg:#0b1220;--panel:#121d30;--line:#26364e;--text:#e8eef8;--muted:#a7b5ca;--accent:#69a7ff}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:16px system-ui,-apple-system,sans-serif}
main{max-width:760px;margin:8vh auto;padding:20px}.card{background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:24px;margin:14px 0}
h1{font-size:1.7rem;margin:0 0 8px}h2{font-size:1.05rem;margin:0 0 12px}.muted{color:var(--muted)}label{display:block;margin:14px 0 6px}
input{width:100%;padding:12px;border-radius:8px;border:1px solid var(--line);background:#0b1220;color:var(--text);font:inherit}
button,.button{display:inline-block;padding:11px 15px;border:0;border-radius:8px;background:var(--accent);color:#071323;font-weight:700;text-decoration:none;cursor:pointer;margin-top:14px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px}.value{font-size:1.15rem;font-weight:650;overflow-wrap:anywhere}.error{color:#ff9b9b}
</style></head><body><main>""" + body + """</main></body></html>"""

class AdminHandler(BaseHTTPRequestHandler):
    server_version = "XPAdmin"
    sys_version = ""

    def log_message(self, fmt, *args):
        # Não registar caminhos sensíveis, cookies, corpos nem credenciais.
        return

    def send_page(self, status, content, cookies=None):
        raw = content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'")
        self.send_header("Strict-Transport-Security", "max-age=31536000")
        for item in cookies or []:
            self.send_header("Set-Cookie", item)
        self.end_headers()
        self.wfile.write(raw)

    def redirect(self, location, cookies=None):
        self.send_response(303)
        self.send_header("Location", location)
        self.send_header("Cache-Control", "no-store")
        for item in cookies or []:
            self.send_header("Set-Cookie", item)
        self.end_headers()

    def read_form(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            return None
        if length < 1 or length > MAX_BODY:
            return None
        data = self.rfile.read(length).decode("utf-8", "strict")
        return parse_qs(data, keep_blank_values=True, max_num_fields=10)

    def do_GET(self):
        if self.path not in ("/", "/login"):
            self.send_page(404, page("Não encontrado", "<section class='card'><h1>404</h1><p>Endereço não encontrado.</p></section>"))
            return
        if self.path == "/login" or not verify_session(self):
            csrf = secrets.token_hex(32)
            body = """<section class="card"><h1>XP Admin</h1>
<p class="muted">Acesso restrito ao administrador.</p>
<form method="post" action="/login" autocomplete="on">
<input type="hidden" name="csrf" value="TOKEN">
<label for="username">Utilizador</label><input id="username" name="username" maxlength="128" autocomplete="username" required>
<label for="password">Palavra-passe</label><input id="password" name="password" type="password" autocomplete="current-password" required>
<button type="submit">Entrar</button></form></section>""".replace("TOKEN", csrf)
            self.send_page(200, page("Login", body), [
                cookie_header(CSRF_COOKIE, csrf, http_only=False, max_age=600),
                cookie_header(SESSION_COOKIE, "", max_age=0),
            ])
            return
        csrf = verify_session(self)
        battery = termux_json(["termux-battery-status"])
        if battery:
            bat_body = "<div class='value'>" + html.escape(str(battery.get("percentage", "N/D"))) + "%</div><p class='muted'>Estado: " + html.escape(str(battery.get("status", "N/D"))) + "<br>Temperatura: " + html.escape(str(battery.get("temperature", "N/D"))) + " °C</p>"
        else:
            bat_body = "<p class='muted'>Dados indisponíveis. Confirma Termux:API e as permissões.</p>"
        location = termux_json(["termux-location", "-p", "network"], timeout=15)
        if location:
            loc_body = "<div class='value'>" + html.escape(str(location.get("latitude", "N/D"))) + ", " + html.escape(str(location.get("longitude", "N/D"))) + "</div><p class='muted'>Localização visível apenas após autenticação.</p>"
        else:
            loc_body = "<p class='muted'>Localização indisponível ou sem permissão.</p>"
        body = """<h1>XP Admin</h1><p class="muted">Sessão protegida · expira em 30 minutos</p>
<div class="grid"><section class="card"><h2>🔋 Bateria</h2>BATTERY</section>
<section class="card"><h2>📍 Localização</h2>LOCATION</section></div>
<section class="card"><h2>Sessão</h2><p class="muted">Este painel é apenas de consulta. Nenhum comando remoto é executado.</p>
<form method="post" action="/logout"><input type="hidden" name="csrf" value="TOKEN"><button type="submit">Terminar sessão</button></form></section>
<p class="muted">XP · painel privado</p>""".replace("BATTERY", bat_body).replace("LOCATION", loc_body).replace("TOKEN", csrf)
        self.send_page(200, page("Painel", body))

    def do_POST(self):
        if self.path not in ("/login", "/logout"):
            self.send_page(404, page("Não encontrado", "<section class='card'><h1>404</h1></section>"))
            return
        try:
            form = self.read_form()
        except (UnicodeDecodeError, ValueError):
            form = None
        if not form:
            self.send_page(400, page("Pedido inválido", "<section class='card'><h1>Pedido inválido</h1></section>"))
            return
        submitted_csrf = form.get("csrf", [""])[0]
        if self.path == "/login":
            cookie_csrf = cookie_value(self, CSRF_COOKIE)
            if not cookie_csrf or not hmac.compare_digest(submitted_csrf, cookie_csrf):
                self.send_page(403, page("Pedido recusado", "<section class='card'><h1>Pedido recusado</h1><p>Atualiza a página e tenta novamente.</p></section>"))
                return
            ip = self.client_address[0]
            now = time.time()
            state = FAILURES.get(ip, {"count": 0, "until": 0})
            if state["until"] > now:
                self.send_page(429, page("Aguarda", "<section class='card'><h1>Demasiadas tentativas</h1><p>Tenta novamente mais tarde.</p></section>"))
                return
            username = form.get("username", [""])[0]
            password = form.get("password", [""])[0]
            good_user = hmac.compare_digest(username.encode(), ADMIN_USER.encode())
            good_pass = hmac.compare_digest(password.encode(), ADMIN_PASSWORD.encode())
            if not (good_user and good_pass):
                count = state["count"] + 1 if state["until"] <= now else 1
                until = now + LOCK_SECONDS if count >= MAX_FAILURES else 0
                FAILURES[ip] = {"count": 0 if until else count, "until": until}
                self.send_page(401, page("Acesso recusado", "<section class='card'><h1 class='error'>Credenciais inválidas</h1><p>Verifica os dados e tenta novamente.</p><a class='button' href='/login'>Voltar</a></section>"), [
                    cookie_header(CSRF_COOKIE, "", http_only=False, max_age=0),
                    cookie_header(SESSION_COOKIE, "", max_age=0),
                ])
                return
            FAILURES.pop(ip, None)
            session_csrf = secrets.token_hex(32)
            self.redirect("/", [
                cookie_header(CSRF_COOKIE, "", http_only=False, max_age=0),
                cookie_header(SESSION_COOKIE, signed_session(session_csrf), max_age=SESSION_TTL),
            ])
            return
        session_csrf = verify_session(self)
        if not session_csrf or not hmac.compare_digest(submitted_csrf, session_csrf):
            self.send_page(403, page("Sessão inválida", "<section class='card'><h1>Sessão expirada</h1><a class='button' href='/login'>Entrar novamente</a></section>"), [
                cookie_header(SESSION_COOKIE, "", max_age=0)
            ])
            return
        self.redirect("/login", [cookie_header(SESSION_COOKIE, "", max_age=0)])

def main():
    check_config()
    server = ThreadingHTTPServer((HOST, PORT), AdminHandler)
    server.daemon_threads = True
    print(f"XP Admin ativo apenas em http://{HOST}:{PORT} (acesso externo apenas pelo túnel HTTPS).")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nXP Admin encerrado.")
    finally:
        server.server_close()

if __name__ == "__main__":
    main()
