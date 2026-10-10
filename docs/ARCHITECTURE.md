# XP Battery — arquitetura local

## Objetivo
Guardar o estado da bateria exclusivamente no telefone Android que executa o XP Battery. Não é necessária uma conta Firebase nem uma base de dados na nuvem.

## Arquitetura
1. A aplicação Android lê a percentagem e o estado de carregamento.
2. SQLite local guarda leituras, data/hora e as opções de recolha.
3. O APK disponibiliza o painel XP Admin e uma pequena API HTTP na rede Wi-Fi local, na porta 8765.
4. Um navegador noutro telefone, na mesma rede, abre o endereço local mostrado no APK.
5. As rotas da API exigem o código de acesso gerado no primeiro arranque. A página web é servida pela mesma origem, evitando dependências de serviços externos.

## Limitações
- A primeira implementação do servidor só fica disponível enquanto o processo da aplicação está ativo; fechar a aplicação ou o Android terminar o processo interrompe o acesso. Um serviço em primeiro plano poderá ser acrescentado depois, com notificação persistente.
- O navegador e o telefone Android precisam de estar na mesma rede local e a rede tem de permitir comunicação entre dispositivos.
- HTTP numa rede local não cifra o tráfego. Usar apenas Wi-Fi de confiança; não encaminhar a porta para a Internet nem usar em redes públicas.
- O WorkManager aceita períodos a partir de 15 minutos, mas o Android pode atrasar tarefas devido às políticas de bateria.
- “Solicitar leitura agora” atualiza a leitura quando o processo Android está ativo; a entrega instantânea não é garantida se o processo tiver sido terminado.
- A base de dados SQLite é privada da aplicação e não é copiada para um serviço externo.

## Segurança e âmbito
O código de acesso protege as rotas da API; deve ser partilhado apenas com administradores autorizados. Esta versão recolhe apenas percentagem, estado de carregamento e data/hora. Não recolhe localização, mensagens, contactos ou outros dados pessoais.

## Compilação
Na pasta `android-app`, executar `gradle assembleDebug`. O workflow GitHub Actions `Build XP Battery APK` pode gerar um APK de teste como artefacto. O APK deve ser testado num telefone real antes de ser considerado pronto para utilização.
