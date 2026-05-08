import imaplib
import email

# CONFIGURE AQUI
EMAIL = "pensadorsemfronteiras0@gmail.com"
SENHA = "aqjf amlx padb akze"
# ------------------

def apagar_emails_bateria():
    try:
        # Conecta ao Gmail
        mail = imaplib.IMAP4_SSL('imap.gmail.com', 993)
        mail.login(EMAIL, SENHA)

        # Seleciona a pasta "Enviados"
        mail.select('"[Gmail]/Sent Mail"')

        # Busca emails com assunto "Alerta de Bateria"
        status, mensagens = mail.search(None, 'SUBJECT "Alerta de Bateria"')

        if not mensagens[0]:
            print("Nenhum email de bateria encontrado.")
            mail.logout()
            return

        ids = mensagens[0].split()
        total = len(ids)
        print(f"Encontrados {total} emails de bateria.")

        for id_email in ids:
            mail.store(id_email, '+FLAGS', '\\Deleted')
            print(f"Email {id_email.decode()} marcado para apagar.")

        # Apaga definitivamente
        mail.expunge()
        print(f"{total} emails apagados com sucesso.")

        mail.logout()

    except Exception as e:
        print(f"Erro: {e}")

if __name__ == '__main__':
    print("Apagando emails de relatorio de bateria...")
    print("-" * 40)
    apagar_emails_bateria()
