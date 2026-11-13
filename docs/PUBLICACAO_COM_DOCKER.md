# AEVIA 1.3 — publicação responsável (Docker)

Esta é uma configuração de **deploy técnico**, não um site já publicado. A hospedagem deve permitir um disco/volume persistente para SQLite e imagens. **Hospedagem gratuita sem disco persistente pode apagar os uploads após um reinício.**

## Pré-requisitos

1. Ter um provedor compatível com Docker, HTTPS e **volume persistente** montado em `/data`, gravável pelo processo `aevia` (usuário da imagem). Configure backups/restauração.
2. Definir como variáveis de ambiente fora do Git: `APP_ENV=production`, `PUBLIC_URL=https://seu-dominio...`, `ADMIN_PASSWORD` (16+ caracteres, aleatória), `SESSION_SECRET` (32+ caracteres aleatórios), `AEVIA_CONTACT_EMAIL` (e-mail válido), `DB_PATH=/data/aevia.sqlite3`, `STORAGE_DIR=/data`.
3. Para tráfego público, usar provedor de busca de endereços com cota adequada (`GEOAPIFY_API_KEY`) e `ENABLE_PUBLIC_NOMINATIM=no`, ou geocodificador próprio. O Nominatim comunitário não é para alto tráfego.
4. Revisar dados pessoais/LGPD, direitos/licenças, textos legais e procedimento de denúncia/exclusão. Confirmar `LEGAL_REVIEW_CONFIRMED=yes` só **depois** da revisão.
5. Testar mapa, imagens, pelo menos três municípios, acervo, envio de foto, moderação e exclusão no domínio HTTPS real. Confirmar `LIVE_TESTS_CONFIRMED=yes` só depois.
6. Confirmar que banco **e** arquivos gravados sobrevivem a reinício/redeploy e que existe backup/restauração testados. Só então `PERSISTENT_STORAGE_CONFIRMED=yes`.
7. Configurar monitoramento, regras antiabuso/proxy e limitação de taxa que funcione com várias réplicas. Este backend usa bloqueio de taxa local em memória, inadequado para alta escala.

O serviço recusa o modo de produção se o Nominatim público estiver ativo sem alternativa de geocodificação; desative-o ou configure `GEOAPIFY_API_KEY`.

A imagem `Dockerfile` instala dependências, baixa municípios na inicialização quando necessário, e executa o servidor em `0.0.0.0:${PORT}`. Em produção ele recusa iniciar sem senha, HTTPS, catálogo nacional completo e confirmações de segurança. Uma confirmação declarada NÃO substitui a auditoria nem prova que o provedor preserva os arquivos.

**Não use SQLite com múltiplas réplicas independentes.** Para crescer, migre para PostgreSQL e armazenamento de objetos, com políticas de acesso ao acervo privado.

## Checklist local antes de ir ao host

Execute `verificar_publicacao.bat` no Windows, após configurar `.env`. O resultado não é substituto de revisão real. Os testes automatizados não simulam o tráfego público nem garantem autenticidade de fotos.
