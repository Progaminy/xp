import os
import subprocess
import json
import time
import smtplib
import imaplib
from email.mime.text import MIMEText

EMAIL = os.environ.get("XP_EMAIL_ADDRESS", "")
SENHA = os.environ.get("XP_EMAIL_APP_PASSWORD", "")
DESTINO = os.environ.get("XP_EMAIL_DESTINATION", EMAIL)
INTERVALO = 300

def verificar_config():
    if not EMAIL or not SENHA or not DESTINO:
        raise SystemExit("Configura XP_EMAIL_ADDRESS, XP_EMAIL_APP_PASSWORD e XP_EMAIL_DESTINATION.")

def apagar_email_anterior():
    """Apaga o último email de bateria enviado, se existir."""
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
        mail.login(EMAIL, SENHA)
        status, _ = mail.select('"[Gmail]/Sent Mail')
        if status == "OK":
            status, mensagens = mail.search(None, 'SUBJECT "Alerta de Bateria"')
            if status == "OK" and mensagens and mensagens[0]:
                ids = mensagens[0].split()
                if ids:
                    mail.store(ids[-1], "+FLAGS", "\\Deleted")
                    mail.expunge()
        mail.logout()
    except Exception as e:
        print(f"Erro ao processar email anterior: {e}")

def enviar_email(assunto, mensagem):
    try:
        msg = MIMEText(mensagem)
        msg["Subject"] = assunto
        msg["From"] = EMAIL
        msg["To"] = DESTINO
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as server:
            server.login(EMAIL, SENHA)
            server.sendmail(EMAIL, [DESTINO], msg.as_string())
    except Exception as e:
        print(f"Erro ao enviar email: {e}")

def verificar_bateria():
    resultado = subprocess.run(["termux-battery-status"], capture_output=True, text=True, timeout=10, check=True)
    return json.loads(resultado.stdout)

if __name__ == "__main__":
    verificar_config()
    print("Monitor de bateria por email iniciado.")
    while True:
        try:
            dados = verificar_bateria()
            mensagem = (
                "Relatório de Bateria\n"
                "====================\n"
                f"Nivel: {dados.get('percentage', 'N/D')}%\n"
                f"Status: {dados.get('status', 'N/D')}\n"
                f"Temperatura: {dados.get('temperature', 'N/D')}°C\n"
                f"Saude: {dados.get('health', 'N/D')}"
            )
            apagar_email_anterior()
            enviar_email("Alerta de Bateria", mensagem)
        except Exception as e:
            print(f"Erro no monitor de bateria: {e}")
        time.sleep(INTERVALO)
