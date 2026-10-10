import os
import subprocess
import json
import time
import requests

TOKEN = os.environ.get("XP_TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.environ.get("XP_TELEGRAM_CHAT_ID", "")
INTERVALO = 300

ultima_mensagem_id = None

def verificar_config():
    if not TOKEN or not CHAT_ID:
        raise SystemExit("Configura XP_TELEGRAM_BOT_TOKEN e XP_TELEGRAM_CHAT_ID.")

def apagar_mensagem_anterior():
    global ultima_mensagem_id
    if not ultima_mensagem_id:
        return
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/deleteMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "message_id": ultima_mensagem_id}, timeout=10)
    except Exception as e:
        print(f"Erro ao apagar mensagem anterior: {e}")

def enviar_telegram(mensagem):
    global ultima_mensagem_id
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        resposta = requests.post(url, data={"chat_id": CHAT_ID, "text": mensagem}, timeout=10)
        dados = resposta.json()
        if dados.get("ok"):
            ultima_mensagem_id = dados["result"]["message_id"]
        else:
            print("Telegram recusou a mensagem.")
    except Exception as e:
        print(f"Erro ao enviar Telegram: {e}")

def verificar_bateria():
    resultado = subprocess.run(["termux-battery-status"], capture_output=True, text=True, timeout=10, check=True)
    return json.loads(resultado.stdout)

if __name__ == "__main__":
    verificar_config()
    print("Monitor de bateria via Telegram iniciado.")
    while True:
        try:
            dados = verificar_bateria()
            status = dados.get("status", "N/D")
            emoji = "⚡" if status == "CHARGING" else "🔋" if status == "DISCHARGING" else "🔌"
            mensagem = (
                f"{emoji} Relatório de Bateria\n"
                f"────────────────────\n"
                f"Nivel: {dados.get('percentage', 'N/D')}%\n"
                f"Status: {status}\n"
                f"Temperatura: {dados.get('temperature', 'N/D')}°C\n"
                f"Saude: {dados.get('health', 'N/D')}"
            )
            apagar_mensagem_anterior()
            enviar_telegram(mensagem)
        except Exception as e:
            print(f"Erro no monitor de bateria: {e}")
        time.sleep(INTERVALO)
