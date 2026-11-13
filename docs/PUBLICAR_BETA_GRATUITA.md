# AEVIA Beta — Publicação gratuita com segurança básica

## O que está liberado

- Selecionar municípios do Brasil e ver o mapa.
- Buscar e consultar imagens do Wikimedia Commons com créditos e aviso sobre localização incerta.
- Comparar imagens disponíveis e explorar cenários hipotéticos 2050 baseados em dados do IBGE quando disponíveis.
- Seguir links externos para Brasiliana e Wikimedia Commons. **A Brasiliana pode retornar zero resultados.**

## O que permanece desativado

Envio público de fotos e relatos, contas e moderação pública, triagem por IA externa e geocodificação gratuita em larga escala. Essas funções só serão reativadas depois que houver armazenamento persistente, revisão dos termos, segurança, controle de abuso e backups. A rota POST `/api/contribuicoes` retorna HTTP 403 e não salva arquivos no modo Beta.

## Publicar no Render Free usando GitHub

1. Crie um repositório novo para a Beta. **Não sobrescreva a versão anterior do GitHub Pages sem backup.**
2. Faça o upload do conteúdo **de dentro desta pasta `AEVIA`** para a raiz do novo repositório, incluindo `Dockerfile`, `render.yaml`, `app/`, `static/` e `requirements.txt`. Não envie `.env`, `storage/` nem `.venv/`.
3. No Render, escolha **New > Blueprint**, conecte esse repositório e verifique que o plano sugerido é **Free** e o ambiente é `APP_ENV=beta`. Em algumas interfaces também é possível criar **New > Web Service**, apontar o repositório, runtime Docker e plano Free.
4. A variável `RENDER_EXTERNAL_URL` é fornecida automaticamente pelo Render e será usada pelo AEVIA para conferir o endereço HTTPS. Não publique usando HTTP.
5. Opcional: configure `AEVIA_CONTACT_EMAIL` no painel do Render com um contato público do projeto, ou deixe a URL do serviço como identificação do acesso externo aos acervos.
6. Acompanhe o deploy e abra `/api/status`. Confira `version=1.7.0`, `release_channel=beta`, `public_contributions_enabled=false` e **`city_catalog_complete=true` com aproximadamente 5.571 municípios**. Se o catálogo estiver incompleto, não divulgue a Beta até corrigir a sincronização com o IBGE.
7. Teste São Paulo, Cataguases e Juiz de Fora com o mapa, acervo, links externos e 2050. Teste também que o botão de envio avisa "em breve". Se houver falha nas APIs externas, investigue logs.
8. Ao compartilhar, descreva como **versão Beta demonstrativa**, sem alegar que todas as cidades têm fotos históricas ou que os cenários de 2050 são previsões.

## Limitações do gratuito

O Render Free entra em suspensão após 15 minutos sem acesso e o disco local não é persistente. Por isso, imagens enviadas pelo público estão desativadas; o banco SQLite guarda apenas catálogo e cache que podem ser reconstruídos. A plataforma depende de internet e de disponibilidade/limites de IBGE, Wikimedia Commons, OpenStreetMap e Brasiliana. É uma Beta de demonstração, não uma produção com garantia de disponibilidade.

## O que falta antes de reativar contribuições

Banco e arquivos persistentes com backups testados, controles de autenticação e antispam, moderação humana, canal para denúncia e remoção, políticas revisadas e testes de carga e privacidade. Não configure `ENABLE_PUBLIC_CONTRIBUTIONS=yes` no Render Free: a aplicação bloqueia a inicialização nesse caso.
