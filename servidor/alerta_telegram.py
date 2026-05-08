import subprocess
import json
import time
import requests

# CONFIGURE AQUI
TOKEN = "8557708504:AAG2hnmS81MzE4Dj3wscfBIa6gc8hfJS6Yw"
CHAT_ID = "7756976956"
INTERVALO = 5  # segundos para teste (depois mude para 300)
# ------------------

ultima_mensagem_id = None

def apagar_mensagem_anterior():
    """Apaga a ultima mensagem de bateria enviada no Telegram"""
    global ultima_mensagem_id
    if ultima_mensagem_id:
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/deleteMessage"
            requests.get(url, params={
                "chat_id": CHAT_ID,
                "message_id": ultima_mensagem_id
            }, timeout=10)
            print("Mensagem anterior apagada.")
        except Exception as e:
            print(f"Erro ao apagar mensagem: {e}")

def enviar_telegram(mensagem):
    """Envia mensagem para o Telegram e guarda o ID"""
    global ultima_mensagem_id
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        resposta = requests.get(url, params={
            "chat_id": CHAT_ID,
            "text": mensagem
        }, timeout=10)

        dados = resposta.json()
        if dados.get('ok'):
            ultima_mensagem_id = dados['result']['message_id']
            print(f"Mensagem enviada ao Telegram (ID: {ultima_mensagem_id})")
        else:
            print(f"Erro na API: {dados}")
    except Exception as e:
        print(f"Erro ao enviar Telegram: {e}")

def verificar_bateria():
    """Retorna dados da bateria"""
    resultado = subprocess.run(
        ['termux-battery-status'],
        capture_output=True,
        text=True
    )
    return json.loads(resultado.stdout)

if __name__ == '__main__':
    print("Monitor de bateria via Telegram iniciado...")
    print(f"Atualizando a cada {INTERVALO} segundos")
    print(f"Modo: Apaga anterior antes de enviar novo")
    print("-" * 40)

    while True:
        try:
            dados = verificar_bateria()
            porcentagem = dados['percentage']
            status = dados['status']
            temperatura = dados['temperature']
            saude = dados.get('health', 'N/D')

            # Emojis para status
            if status == 'CHARGING':
                emoji = '⚡'
            elif status == 'DISCHARGING':
                emoji = '🔋'
            else:
                emoji = '🔌'

            mensagem = (
                f"{emoji} *Relatorio de Bateria*\n"
                f"────────────────────\n"
                f"📊 *Nivel:* {porcentagem}%\n"
                f"📈 *Status:* {status}\n"
                f"🌡 *Temperatura:* {temperatura}°C\n"
                f"💚 *Saude:* {saude}"
            )

            print(mensagem.replace('*', '').replace('\n', ' | '))

            # 1. Apaga a mensagem anterior
            apagar_mensagem_anterior()

            # 2. Envia a nova mensagem
            enviar_telegram(mensagem)

        except Exception as e:
            print(f"Erro: {e}")

        time.sleep(INTERVALO)
