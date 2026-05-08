import subprocess
import json
import time
import smtplib
from email.mime.text import MIMEText

# CONFIGURE AQUI
EMAIL = "pensadorsemfronteiras0@gmail.com"
SENHA = "aqjf amlx padb akze"
DESTINO = "pensadorsemfronteiras0@gmail.com"
INTERVALO = 5  # segundos para teste
# ------------------

def enviar_email(assunto, mensagem):
    try:
        msg = MIMEText(mensagem)
        msg['Subject'] = assunto
        msg['From'] = EMAIL
        msg['To'] = DESTINO

        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(EMAIL, SENHA)
        server.sendmail(EMAIL, DESTINO, msg.as_string())
        server.quit()
        print(f"Email enviado para {DESTINO}")
    except Exception as e:
        print(f"Erro ao enviar email: {e}")

def verificar_bateria():
    resultado = subprocess.run(
        ['termux-battery-status'],
        capture_output=True,
        text=True
    )
    return json.loads(resultado.stdout)

if __name__ == '__main__':
    print("Monitor de bateria iniciado...")
    print(f"Email a cada {INTERVALO} segundos")
    print(f"Destino: {DESTINO}")
    print("-" * 40)

    while True:
        try:
            dados = verificar_bateria()
            porcentagem = dados['percentage']
            status = dados['status']
            temperatura = dados['temperature']
            saude = dados.get('health', 'N/D')

            mensagem = (
                f"Relatorio de Bateria\n"
                f"====================\n"
                f"Nivel: {porcentagem}%\n"
                f"Status: {status}\n"
                f"Temperatura: {temperatura}°C\n"
                f"Saude: {saude}"
            )

            print(mensagem.replace('\n', ' | '))
            enviar_email("Alerta de Bateria", mensagem)

        except Exception as e:
            print(f"Erro: {e}")

        time.sleep(INTERVALO)
