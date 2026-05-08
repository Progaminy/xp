import subprocess
import requests
import time
import re

# CONFIGURE AQUI
TOKEN = "SEU_TOKEN_DO_BOT"
CHAT_ID = "SEU_CHAT_ID"
# ----------------

ultima_url = ""

def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        requests.get(url, params={"chat_id": CHAT_ID, "text": mensagem}, timeout=10)
        print(f"Mensagem enviada: {mensagem[:50]}...")
    except Exception as e:
        print(f"Erro ao enviar: {e}")

def extrair_url(texto):
    match = re.search(r'https://[a-zA-Z0-9.-]+\.serveousercontent\.com', texto)
    return match.group(0) if match else None

def iniciar_tunel():
    global ultima_url
    processo = subprocess.Popen(
        ['autossh', '-M', '0', '-o', 'ServerAliveInterval=30', '-o', 'ServerAliveCountMax=3',
         '-R', '80:localhost:8080', 'serveo.net'],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    
    for linha in processo.stdout:
        print(linha.strip())
        url = extrair_url(linha)
        if url and url != ultima_url:
            ultima_url = url
            enviar_telegram(f"🔗 Novo túnel ativo:\n{url}")

if __name__ == "__main__":
    enviar_telegram("🟢 Guardião iniciado. Monitorando túneis...")
    while True:
        try:
            iniciar_tunel()
        except Exception as e:
            print(f"Erro: {e}")
            time.sleep(10)