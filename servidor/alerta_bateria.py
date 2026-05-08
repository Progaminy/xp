import subprocess
import json
import time

# CONFIGURE AQUI
NUMERO = "+258872599084"  # Substitua pelo seu numero
INTERVALO = 5             # 5 segundos para teste (depois mude para 300 = 5 minutos)
# ------------------

def enviar_sms(mensagem):
    """Envia SMS usando a API do Termux"""
    try:
        subprocess.run([
            'termux-sms-send',
            '-n', NUMERO,
            mensagem
        ], check=True, timeout=10)
        print(f"SMS enviado: {mensagem}")
    except Exception as e:
        print(f"Erro ao enviar SMS: {e}")

def verificar_bateria():
    """Retorna dados da bateria"""
    resultado = subprocess.run(
        ['termux-battery-status'],
        capture_output=True,
        text=True
    )
    return json.loads(resultado.stdout)

if __name__ == '__main__':
    print("Monitor de bateria iniciado...")
    print(f"SMS sera enviado a cada {INTERVALO} segundos")
    print(f"Numero: {NUMERO}")
    print("-" * 40)

    while True:
        try:
            dados = verificar_bateria()
            porcentagem = dados['percentage']
            status = dados['status']
            temperatura = dados['temperature']

            mensagem = (
                f"Bateria: {porcentagem}%\n"
                f"Status: {status}\n"
                f"Temperatura: {temperatura}C"
            )

            print(mensagem.replace('\n', ' | '))
            enviar_sms(mensagem)

        except Exception as e:
            print(f"Erro: {e}")

        time.sleep(INTERVALO)
