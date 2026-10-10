# XP Admin — instalação e segurança

O painel fica em `servidor/admin.py`. O ficheiro antigo `servidor/servidor_vivo.py` agora encaminha para o painel autenticado, para não manter a página antiga de bateria/GPS sem login.

## Segurança incluída

- Utilizador e palavra-passe definidos fora do código.
- A palavra-passe nunca é guardada no repositório.
- Sessão assinada com segredo aleatório, validade de 30 minutos e cookie `Secure`, `HttpOnly` e `SameSite=Strict`.
- Proteção CSRF nos formulários e limitação de tentativas de login.
- Respostas sem cache, política CSP e mensagens de erro sem detalhes internos.
- O servidor escuta apenas em `127.0.0.1:8080`; não abrir esta porta diretamente à Internet.
- O painel só consulta bateria/localização; não executa comandos arbitrários enviados pelo navegador.

## Configuração no Termux

1. Instala/abre Termux e Termux:API, e confirma que os comandos `termux-battery-status` e `termux-location` funcionam.
2. No diretório do repositório, cria um ficheiro de configuração privado fora do Git:

```sh
umask 077
nano "$HOME/.xp-admin.env"
```

Coloca neste ficheiro, substituindo os exemplos por valores teus:

```sh
export XP_ADMIN_USERNAME='admin'
export XP_ADMIN_PASSWORD='COLOCA_AQUI_UMA_PALAVRA_PASSE_LONGA_E_UNICA'
export XP_ADMIN_SECRET='COLOCA_AQUI_64_CARACTERES_HEXADECIMAIS_ALEATORIOS'
```

Gera o segredo aleatório com:

```sh
python -c 'import secrets; print(secrets.token_hex(32))'
```

Usa o resultado como `XP_ADMIN_SECRET`. A palavra-passe deve ter pelo menos 16 caracteres. Não a envies no chat nem a coloques em ficheiros do repositório. Protege o ficheiro:

```sh
chmod 600 "$HOME/.xp-admin.env"
source "$HOME/.xp-admin.env"
```

3. Inicia o painel e o túnel na mesma sessão do Termux, para ambos receberem a configuração:

```sh
python servidor/servidor_vivo.py &
python guardiao/notificador.py
```

O túnel existente encaminha a porta local 8080. Abre o endereço HTTPS gerado pelo túnel e inicia sessão com o utilizador e a palavra-passe configurados. Não uses o endereço HTTP; usa apenas HTTPS. Mantém o Termux e o telemóvel protegidos e não partilhes o URL público.

## Notificações opcionais

O Telegram já não tem token embutido no código. Se quiseres voltar a ativar as notificações, configura `XP_TELEGRAM_BOT_TOKEN` e `XP_TELEGRAM_CHAT_ID` no ficheiro privado `$HOME/.xp-admin.env`. O email usa `XP_EMAIL_ADDRESS`, `XP_EMAIL_APP_PASSWORD` e `XP_EMAIL_DESTINATION`.

## Importante antes de publicar/usar

Credenciais que já estiveram no histórico Git devem ser consideradas comprometidas mesmo depois de removidas dos ficheiros atuais. Revoga o token antigo do bot no BotFather e cria um novo; revoga a palavra-passe de aplicação Gmail exposta e gera outra. Não reutilizes esses valores. Se possível, remove os segredos do histórico Git e verifica os registos do fornecedor.

Esta primeira versão usa o servidor HTTP simples da biblioteca padrão do Python, por isso deve ficar acessível externamente apenas através de um túnel HTTPS confiável. Para uma instalação pública permanente, migra para um servidor de aplicação mantido e um túnel/proxy com controlos de acesso adicionais. Não exponhas a porta 8080 diretamente no router/firewall.
