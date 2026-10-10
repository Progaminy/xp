# XP Battery — Android + XP Admin

Projeto em desenvolvimento: aplicação Android em Kotlin, painel web e API própria com SQLite.

## Componentes
- `android-app/`: aplicação Android; mantém dados locais e sincroniza com a API quando configurada.
- `web-admin/`: painel web publicado pelo GitHub Pages.
- `backend/self-hosted/`: API Node.js + SQLite para alojamento num servidor Linux/VPS próprio. Não usa Cloudflare nem Firebase.

## Publicar o servidor
Consulta [backend/self-hosted/README.md](backend/self-hosted/README.md). É necessário um servidor que permaneça ligado e um endereço HTTPS público para que o APK e o painel funcionem pela Internet. O ficheiro SQLite remoto é persistido num volume Docker.

## Estado atual
O APK debug já foi compilado no GitHub Actions, mas a API própria ainda precisa de ser instalada num servidor com HTTPS. Até essa publicação, não há um URL de API ativo para ligar o APK e o painel.

## Privacidade e segurança
A aplicação recolhe apenas os dados previstos pelo projeto (bateria, carregamento, modelo/Android e armazenamento). A recolha remota deve ser ativada pelo administrador e configurada pelo proprietário do dispositivo. Mantém as chaves de administrador e dispositivo fora do repositório.
