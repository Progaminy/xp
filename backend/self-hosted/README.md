# XP Battery API — servidor próprio + SQLite

Esta alternativa não usa Cloudflare, Firebase nem D1. A API Node.js guarda os dados num ficheiro SQLite persistente no servidor. O APK mantém também a sua base de dados local; o SQLite do servidor permite ao XP Admin ver dados através da Internet.

## Requisito essencial

É necessário um servidor Linux/VPS que permaneça ligado e acessível pela Internet. Para o APK Android e o painel GitHub Pages, a API deve ter um endereço HTTPS público. Não publiques a porta 3000 diretamente na Internet: coloca um proxy HTTPS (por exemplo, Caddy ou Nginx com certificado TLS) à frente da API. O Compose só expõe a porta em 127.0.0.1.

## Instalação com Docker

1. Instala Docker Engine e o plugin Docker Compose no teu VPS.
2. Copia a pasta `backend/self-hosted` para o servidor.
3. Dentro dessa pasta, copia `.env.example` para `.env` e substitui ambos os valores por segredos aleatórios longos e diferentes. Nunca coloques os segredos no GitHub.
4. Inicia a API: `docker compose up -d --build`.
5. Configura o teu domínio/subdomínio HTTPS no proxy reverso para encaminhar para `127.0.0.1:3000`.
6. Confirma `https://TEU-DOMINIO/health`; deve responder `{"ok":true,"service":"XP Battery API"}`.
7. No APK, coloca o URL HTTPS real da API e o valor de `XP_DEVICE_KEY`. No XP Admin, coloca o mesmo URL e o valor de `XP_ADMIN_KEY`.

A base de dados fica no volume Docker `xp_battery_data` e sobrevive a reinícios do contentor. Faz cópias de segurança regulares desse volume.

## Endpoints

- `GET /health` — verificação básica.
- `POST /device/poll` — recebe comandos; cabeçalho `X-Device-Key`.
- `POST /device/snapshot` — guarda uma leitura; cabeçalho `X-Device-Key`.
- `GET /admin/devices` — lista dispositivos; cabeçalho `Authorization: Bearer XP_ADMIN_KEY`.
- `GET /admin/devices/:id` — detalhes e histórico recente.
- `POST /admin/devices/:id` — configura recolha e pedido de leitura.

A API só permite CORS ao endereço indicado em `XP_ADMIN_ORIGIN`. Protege a chave de administrador e não a partilhes. O intervalo mínimo da aplicação Android é 15 minutos, e o Android pode adiar tarefas em segundo plano.

## Estado

O código está preparado no repositório, mas não está publicado num servidor público. Não existe ainda um URL de API funcional até alguém disponibilizar/configurar o VPS, HTTPS e os segredos.
