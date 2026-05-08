import subprocess
import json
import time
import smtplib
import imaplib
from email.mime.text import MIMEText

# CONFIGURE AQUI
EMAIL = "pensadorsemfronteiras0@gmail.com"
SENHA = "aqjf amlx padb akze"
DESTINO = "pensadorsemfronteiras0@gmail.com"
INTERVALO = 5  # segundos para teste (depois mude para 300)
# ------------------

def apagar_email_anterior():
    """Apaga o ultimo email de bateria enviado"""
    try:
        mail = imaplib.IMAP4_SSL('imap.gmail.com', 993)
        mail.login(EMAIL, SENHA)
        mail.select('"[Gmail]/Sent Mail"')

        # Busca emails com assunto "Alerta de Bateria"
        status, mensagens = mail.search(None, 'SUBJECT "Alerta de Bateria"')

        if mensagens[0]:
            ids = mensagens[0].split()
            # Pega apenas o ultimo email
            ultimo = ids[-1]
            mail.store(ultimo, '+FLAGS', '\\Deleted')
            mail.expunge()
            print("Email anterior apagado.")

        mail.logout()
    except Exception as e:
        print(f"Erro ao apagar email: {e}")

def enviar_email(assunto, mensagem):
    """Envia email usando Gmail"""
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
    """Retorna dados da bateria"""
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
    print(f"Modo: Apaga anterior antes de enviar novo")
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

            # 1. Apaga o email anterior
            apagar_email_anterior()

            # 2. Envia o novo email
            enviar_email("Alerta de Bateria", mensagem)

        except Exception as e:
            print(f"Erro: {e}")

        time.sleep(INTERVALO)
