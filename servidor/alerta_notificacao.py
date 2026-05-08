import subprocess
import json
import time

# CONFIGURE AQUI
INTERVALO = 5  # segundos para teste (depois mude para 300)
# ------------------

ultimo_id = None

def notificar_bateria(titulo, mensagem):
    """Atualiza a notificacao Android (substitui a anterior)"""
    global ultimo_id
    try:
        # Se ja tem uma notificacao anterior, usa o mesmo ID para substituir
        if ultimo_id is None:
            ultimo_id = "bateria-alerta"

        subprocess.run([
            'termux-notification',
            '--id', ultimo_id,
            '--title', titulo,
            '--content', mensagem,
            '--priority', 'high',
            '--alert-once'
        ], timeout=10)
        print("Notificacao atualizada.")
    except Exception as e:
        print(f"Erro na notificacao: {e}")

def remover_notificacao():
    """Remove a notificacao atual"""
    global ultimo_id
    if ultimo_id:
        try:
            subprocess.run([
                'termux-notification-remove', ultimo_id
            ], timeout=5)
            print("Notificacao removida.")
        except Exception as e:
            print(f"Erro ao remover: {e}")

def verificar_bateria():
    """Retorna dados da bateria"""
    resultado = subprocess.run(
        ['termux-battery-status'],
        capture_output=True,
        text=True
    )
    return json.loads(resultado.stdout)

if __name__ == '__main__':
    print("Monitor de bateria via Notificacao iniciado...")
    print(f"Atualizando a cada {INTERVALO} segundos")
    print("A notificacao sera atualizada no topo da tela")
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
            elif porcentagem <= 20:
                emoji = '🪫'
            else:
                emoji = '🔋'

            titulo = f"{emoji} Bateria: {porcentagem}%"
            mensagem = f"Status: {status} | Temp: {temperatura}°C | Saude: {saude}"

            print(f"{titulo} | {mensagem}")

            # Atualiza a notificacao (substitui a anterior)
            notificar_bateria(titulo, mensagem)

        except Exception as e:
            print(f"Erro: {e}")

        time.sleep(INTERVALO)
