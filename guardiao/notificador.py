import subprocess
import requests
import time
import re
import threading

# CONFIGURAÇÕES
TOKEN = "8557708504:AAG2hnmS81MzE4Dj3wscfBIa6gc8hfJS6Yw"
CHAT_ID = "7756976956"

ultima_url = ""

def enviar_telegram(mensagem):
    """Envia mensagem para o Telegram"""
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        requests.get(url, params={"chat_id": CHAT_ID, "text": mensagem}, timeout=10)
        print(f"Mensagem enviada ao Telegram: {mensagem[:50]}...")
    except Exception as e:
        print(f"Erro ao enviar Telegram: {e}")

def notificar_android(titulo, mensagem, url):
    """Envia notificação Android com link clicavel"""
    try:
        subprocess.run([
            'termux-notification',
            '--title', titulo,
            '--content', mensagem,
            '--action', f'android.intent.action.VIEW,{url}'
        ], timeout=10)
        print(f"Notificacao Android enviada: {url}")
    except Exception as e:
        print(f"Erro ao notificar Android: {e}")

def extrair_url(texto):
    """Extrai a URL do Serveo do texto"""
    match = re.search(r'https://[a-zA-Z0-9.-]+\.serveousercontent\.com', texto)
    return match.group(0) if match else None

def manter_tunel_vivo(url):
    """Faz ping HTTP a cada 15 segundos para manter o tunel acordado"""
    while True:
        try:
            r = requests.get(url, timeout=10)
            print(f" Ping no tunel: {r.status_code}")
        except Exception as e:
            print(f" Ping falhou: {e}")
        time.sleep(15)

def iniciar_tunel():
    """Inicia o tunel SSH e monitora a saida"""
    global ultima_url
    processo = subprocess.Popen(
        ['autossh', '-M', '0',
         '-o', 'ServerAliveInterval=30',
         '-o', 'ServerAliveCountMax=3',
         '-R', '80:localhost:8080', 'serveo.net'],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    for linha in processo.stdout:
        url = extrair_url(linha)
        if url and url != ultima_url:
            ultima_url = url
            # 1. Notificacao Android (rapida, topo da tela)
            notificar_android("Tunel Ativo", "Clique para acessar o servidor", url)
            # 2. Telegram (backup)
            enviar_telegram(f"Novo tunel ativo:\n{url}")
            # 3. Inicia thread para manter o tunel vivo
            threading.Thread(target=manter_tunel_vivo, args=(url,), daemon=True).start()
        else:
            print(linha.strip())

if __name__ == "__main__":
    enviar_telegram("Guardião iniciado. Monitorando tuneis...")
    while True:
        try:
            iniciar_tunel()
        except Exception as e:
            print(f"Erro no tunel: {e}")
            time.sleep(10)
