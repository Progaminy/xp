import subprocess
import json
import smtplib
import requests
from email.mime.text import MIMEText
from datetime import datetime

# CONFIGURE AQUI
EMAIL = "pensadorsemfronteiras0@gmail.com"
SENHA = "aqjf amlx padb akze"
TOKEN = "8557708504:AAG2hnmS81MzE4Dj3wscfBIa6gc8hfJS6Yw"
CHAT_ID = "7756976956"
# ------------------

def pegar_mensagens(tipo):
    """Pega mensagens SMS (inbox = recebidas, sent = enviadas)"""
    try:
        resultado = subprocess.run(
            ['termux-sms-list', '-t', tipo, '-l', '20'],
            capture_output=True,
            text=True,
            timeout=15
        )
        return json.loads(resultado.stdout)
    except Exception as e:
        print(f"Erro ao pegar SMS ({tipo}): {e}")
        return []

def formatar_data(timestamp):
    """Converte timestamp para data legivel"""
    try:
        dt = datetime.fromtimestamp(int(timestamp) / 1000)
        return dt.strftime('%d/%m/%Y %H:%M')
    except:
        return "Data desconhecida"

def montar_relatorio():
    """Monta o relatorio completo de mensagens"""
    enviadas = pegar_mensagens('sent')
    recebidas = pegar_mensagens('inbox')

    relatorio = "📱 *RELATORIO DE MENSAGENS SMS*\n"
    relatorio += "═" * 30 + "\n\n"

    # Mensagens Recebidas
    relatorio += "*📥 RECEBIDAS:*\n"
    relatorio += "─" * 20 + "\n"
    if recebidas:
        for msg in recebidas[:10]:
            numero = msg.get('number', 'Desconhecido')
            data = formatar_data(msg.get('received', ''))
            texto = msg.get('body', 'Sem conteudo')[:50]
            relatorio += f"👤 *De:* {numero}\n"
            relatorio += f"🕐 *Data:* {data}\n"
            relatorio += f"💬 *Mensagem:* {texto}\n"
            relatorio += "─" * 20 + "\n"
    else:
        relatorio += "Nenhuma mensagem recebida.\n"
        relatorio += "─" * 20 + "\n"

    # Mensagens Enviadas
    relatorio += "\n*📤 ENVIADAS:*\n"
    relatorio += "─" * 20 + "\n"
    if enviadas:
        for msg in enviadas[:10]:
            numero = msg.get('number', 'Desconhecido')
            data = formatar_data(msg.get('sent', ''))
            texto = msg.get('body', 'Sem conteudo')[:50]
            relatorio += f"👤 *Para:* {numero}\n"
            relatorio += f"🕐 *Data:* {data}\n"
            relatorio += f"💬 *Mensagem:* {texto}\n"
            relatorio += "─" * 20 + "\n"
    else:
        relatorio += "Nenhuma mensagem enviada.\n"
        relatorio += "─" * 20 + "\n"

    return relatorio

def enviar_telegram(mensagem):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.get(url, params={
            "chat_id": CHAT_ID,
            "text": mensagem,
            "parse_mode": "Markdown"
        }, timeout=15)
        print("Relatorio enviado ao Telegram.")
    except Exception as e:
        print(f"Erro Telegram: {e}")

def enviar_email(assunto, mensagem):
    try:
        msg = MIMEText(mensagem)
        msg['Subject'] = assunto
        msg['From'] = EMAIL
        msg['To'] = EMAIL

        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(EMAIL, SENHA)
        server.sendmail(EMAIL, EMAIL, msg.as_string())
        server.quit()
        print("Relatorio enviado por email.")
    except Exception as e:
        print(f"Erro email: {e}")

if __name__ == '__main__':
    print("Gerando relatorio de mensagens...")
    print("-" * 40)

    relatorio = montar_relatorio()
    print(relatorio.replace('*', ''))

    print("-" * 40)
    print("Enviando relatorio...")

    enviar_telegram(relatorio)
    enviar_email("Relatorio de Mensagens SMS", relatorio.replace('*', ''))

    print("\n✅ Relatorio enviado ao Telegram e Email!")
