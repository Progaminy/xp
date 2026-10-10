import os
import subprocess
import time
import re
import threading
import requests

# Credenciais fornecidas fora do repositório.
TOKEN = os.environ.get("XP_TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.environ.get("XP_TELEGRAM_CHAT_ID", "")

ultima_url = ""

def enviar_telegram(mensagem):
    """Envia mensagem ao Telegram apenas se as variáveis estiverem configuradas."""
    if not TOKEN or not CHAT_ID:
        print("Telegram desativado: configura XP_TELEGRAM_BOT_TOKEN e XP_TELEGRAM_CHAT_ID.")
        return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": mensagem}, timeout=10)
    except Exception as e:
        print(f"Erro ao enviar Telegram: {e}")

def notificar_android(titulo, mensagem, url):
    """Envia notificação Android com link clicável."""
    try:
        subprocess.run([
            "termux-notification",
            "--title", titulo,
            "--content", mensagem,
            "--action", f"android.intent.action.VIEW,{url}"
        ], timeout=10, check=False)
    except Exception as e:
        print(f"Erro ao notificar Android: {e}")

def extrair_url(texto):
    """Extrai URL HTTPS do túnel Serveo."""
    match = re.search(r"https://[a-zA-Z0-9.-]+\.serveousercontent\.com", texto)
    return match.group(0) if match else None

def manter_tunel_vivo(url):
    """Mantém o túnel acordado com verificações periódicas."""
    while True:
        try:
            r = requests.get(url, timeout=10)
            print(f"Ping do túnel: HTTP {r.status_code}")
        except Exception as e:
            print(f"Ping do túnel falhou: {e}")
        time.sleep(15)

def iniciar_tunel():
    """Inicia o túnel SSH e monitoriza a saída."""
    global ultima_url
    processo = subprocess.Popen(
        ["autossh", "-M", "0", "-o", "ServerAliveInterval=30",
         "-o", "ServerAliveCountMax=3", "-R", "80:localhost:8080", "serveo.net"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    for linha in processo.stdout:
        url = extrair_url(linha)
        if url and url != ultima_url:
            ultima_url = url
            notificar_android("XP Admin — túnel ativo", "Abrir o painel autenticado", url)
            enviar_telegram(f"Novo túnel XP Admin: {url}")
            threading.Thread(target=manter_tunel_vivo, args=(url,), daemon=True).start()
        else:
            print(linha.strip())

if __name__ == "__main__":
    enviar_telegram("Guardião XP iniciado.")
    while True:
        try:
            iniciar_tunel()
        except Exception as e:
            print(f"Erro no túnel: {e}")
            time.sleep(10)
