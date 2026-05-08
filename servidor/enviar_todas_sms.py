import subprocess
import json
import time
import smtplib
import requests
from email.mime.text import MIMEText
from datetime import datetime

# CONFIGURE AQUI
EMAIL = "pensadorsemfronteiras0@gmail.com"
SENHA = "aqjf amlx padb akze"
TOKEN = "8557708504:AAG2hnmS81MzE4Dj3wscfBIa6gc8hfJS6Yw"
CHAT_ID = "7756976956"
INTERVALO = 2  # segundos entre envios
# ------------------

ARQUIVO_CONTROLE = "/data/data/com.termux/files/home/storage/xp/servidor/ultima_enviada.txt"

ultimo_id_telegram = None
ultimo_id_notificacao = None

def carregar_ultimo_indice():
    """Carrega o indice da ultima mensagem enviada"""
    try:
        with open(ARQUIVO_CONTROLE, 'r') as f:
            return int(f.read().strip())
    except:
        return -1  # Nenhuma enviada ainda

def salvar_ultimo_indice(indice):
    """Salva o indice da ultima mensagem enviada"""
    with open(ARQUIVO_CONTROLE, 'w') as f:
        f.write(str(indice))

def pegar_todas_sms():
    """Pega todas as SMS do celular, ordenadas por data (mais antigas primeiro)"""
    todas = []
    try:
        # Pega recebidas
        recebidas = subprocess.run(
            ['termux-sms-list', '-t', 'inbox', '-l', '500'],
            capture_output=True, text=True, timeout=30
        )
        dados_recebidas = json.loads(recebidas.stdout)

        # Pega enviadas
        enviadas = subprocess.run(
            ['termux-sms-list', '-t', 'sent', '-l', '500'],
            capture_output=True, text=True, timeout=30
        )
        dados_enviadas = json.loads(enviadas.stdout)

        # Junta todas com etiqueta
        for msg in dados_recebidas:
            msg['tipo'] = 'RECEBIDA'
            msg['data_ordenacao'] = int(msg.get('received', 0))
            todas.append(msg)

        for msg in dados_enviadas:
            msg['tipo'] = 'ENVIADA'
            msg['data_ordenacao'] = int(msg.get('sent', 0))
            todas.append(msg)

        # Ordena por data (mais antigas primeiro)
        todas.sort(key=lambda x: x['data_ordenacao'])

        return todas
    except Exception as e:
        print(f"Erro ao pegar SMS: {e}")
        return []

def formatar_data(timestamp):
    """Converte timestamp para data legivel"""
    try:
        dt = datetime.fromtimestamp(int(timestamp) / 1000)
        return dt.strftime('%d/%m/%Y %H:%M:%S')
    except:
        return "Data desconhecida"

def enviar_telegram(mensagem):
    """Envia mensagem ao Telegram e apaga a anterior"""
    global ultimo_id_telegram
    try:
        # Apaga mensagem anterior
        if ultimo_id_telegram:
            url_apagar = f"https://api.telegram.org/bot{TOKEN}/deleteMessage"
            requests.get(url_apagar, params={
                "chat_id": CHAT_ID,
                "message_id": ultimo_id_telegram
            }, timeout=5)

        # Envia nova
        url_enviar = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        resposta = requests.get(url_enviar, params={
            "chat_id": CHAT_ID,
            "text": mensagem,
            "parse_mode": "Markdown"
        }, timeout=10)

        dados = resposta.json()
        if dados.get('ok'):
            ultimo_id_telegram = dados['result']['message_id']
            print("  ➤ Telegram: OK")
    except Exception as e:
        print(f"  ➤ Telegram: Erro - {e}")

def enviar_email(assunto, mensagem):
    """Envia email e apaga o anterior"""
    try:
        import imaplib
        # Apaga email anterior
        try:
            mail = imaplib.IMAP4_SSL('imap.gmail.com', 993)
            mail.login(EMAIL, SENHA.replace(' ', ''))
            mail.select('"[Gmail]/Sent Mail"')
            status, msgs = mail.search(None, 'SUBJECT "Relatorio SMS"')
            if msgs[0]:
                ids = msgs[0].split()
                for id_email in ids:
                    mail.store(id_email, '+FLAGS', '\\Deleted')
                mail.expunge()
            mail.logout()
        except:
            pass

        # Envia novo email
        msg = MIMEText(mensagem)
        msg['Subject'] = assunto
        msg['From'] = EMAIL
        msg['To'] = EMAIL

        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(EMAIL, SENHA.replace(' ', ''))
        server.sendmail(EMAIL, EMAIL, msg.as_string())
        server.quit()
        print("  ➤ Email: OK")
    except Exception as e:
        print(f"  ➤ Email: Erro - {e}")

def notificar_android(titulo, mensagem):
    """Atualiza notificacao Android"""
    try:
        subprocess.run([
            'termux-notification',
            '--id', 'sms-envio',
            '--title', titulo,
            '--content', mensagem,
            '--priority', 'high'
        ], timeout=5)
        print("  ➤ Notificacao: OK")
    except Exception as e:
        print(f"  ➤ Notificacao: Erro - {e}")

if __name__ == '__main__':
    print("=" * 50)
    print("ENVIO PROGRAMADO DE SMS (MAIS ANTIGAS PRIMEIRO)")
    print("=" * 50)
    print()

    # Carrega todas as SMS
    print("Carregando todas as SMS do celular...")
    todas_sms = pegar_todas_sms()
    total = len(todas_sms)
    print(f"Total de SMS encontradas: {total}")
    print()

    # Carrega ultimo indice enviado
    ultimo_indice = carregar_ultimo_indice()
    proximo_indice = ultimo_indice + 1

    if proximo_indice >= total:
        print("Todas as SMS ja foram enviadas!")
        print("Apagando arquivo de controle para reiniciar...")
        salvar_ultimo_indice(-1)
        proximo_indice = 0

    print(f"Retomando do indice: {proximo_indice + 1} de {total}")
    print(f"Intervalo entre envios: {INTERVALO} segundos")
    print("-" * 50)
    print()

    # Envia uma por uma
    for i in range(proximo_indice, total):
        msg = todas_sms[i]
        numero = msg.get('number', 'Desconhecido')
        tipo = msg.get('tipo', 'DESCONHECIDO')
        data = formatar_data(msg.get('data_ordenacao', 0))
        texto = msg.get('body', 'Sem conteudo')

        if tipo == 'RECEBIDA':
            emoji = '📥'
            acao = 'De'
        else:
            emoji = '📤'
            acao = 'Para'

        # Monta a mensagem formatada
        mensagem_completa = (
            f"{emoji} *SMS {tipo}*\n"
            f"──────────────────\n"
            f"👤 *{acao}:* {numero}\n"
            f"🕐 *Data:* {data}\n"
            f"💬 *Mensagem:* {texto}\n"
            f"──────────────────\n"
            f"📊 *Progresso:* {i + 1}/{total}"
        )

        # Exibe no terminal
        print(f"[{i + 1}/{total}] {tipo} | {numero} | {data}")
        print(f"  Mensagem: {texto[:50]}...")

        # Envia pelos 3 canais
        enviar_telegram(mensagem_completa)
        enviar_email(f"SMS {tipo} - {data}", mensagem_completa.replace('*', ''))
        notificar_android(
            f"SMS {tipo} ({i + 1}/{total})",
            f"{acao}: {numero} | {texto[:30]}..."
        )

        # Salva progresso
        salvar_ultimo_indice(i)
        print(f"  Progresso salvo. Proxima em {INTERVALO} segundos...")
        print()

        time.sleep(INTERVALO)

    print("=" * 50)
    print("TODAS AS SMS FORAM ENVIADAS COM SUCESSO!")
    print("=" * 50)
