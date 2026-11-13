# AEVIA — Relatório de entrega (13/11/2026)

**Versão:** 1.0 — MVP pré-publicação (código-fonte entregue, não hospedado).

## Concluído e verificado localmente

- Interface web responsiva, navegação, mapa integrado ao Leaflet e zonas de busca (a renderização de tiles depende da internet no navegador).
- API FastAPI inicializável com banco local SQLite e catálogo de municípios com entradas de exemplo.
- Rotina `python -m app.sync_data` que consulta a API do IBGE para o catálogo nacional e arquivo CSV de coordenadas, desde que haja internet.
- Integrações implementadas para o Wikimedia Commons: imagens georreferenciadas próximas ao ponto e busca complementar por nome; licença, crédito, fonte e ano documentado são exibidos quando disponíveis.
- Linha do tempo que não atribui anos fictícios a imagens sem data original.
- Comparação lado a lado de duas fotografias selecionadas.
- Envio de contribuição com limite de imagem, conversão para JPEG sem EXIF/GPS, deduplicação literal, declaração de direitos e fila de revisão.
- Painel administrativo com autenticação por senha configurável, aprovação/rejeição e imagens pendentes não públicas.
- Triagem local automática com alertas e integração opcional para Gemini (não acionada sem chave e consentimento).
- Simulador narrativo didático para 2050, com indicação explícita de que não se trata de previsão.
- **14 testes automatizados passaram** (incluindo privacidade de envio pendente, autenticação, autorização de aprovação, cenários, datas da Wikimedia simuladas e restrição de origem).

## O que não foi validado ou concluído

1. **Sincronização nacional online** — a execução neste ambiente não conseguiu acessar o IBGE/GitHub; portanto o ZIP não traz a base nacional já sincronizada. No seu computador, o script tentará baixá-la na primeira execução.
2. **Acervos em produção** — não é possível garantir que existam fotografias históricas de todas as cidades, ruas ou períodos. Esta entrega não inclui cópia de imagens nem apropriação de conteúdo de terceiros.
3. **Serviços externos** — chamadas reais ao Wikimedia Commons, Geoapify e Gemini ainda precisam ser testadas com acesso à internet e chaves autorizadas.
4. **Inteligência artificial** — triagem opcional implementada, não treinada nem validada para comprovação histórica. Toda publicação continua sujeita a decisão humana.
5. **AEVIA 2050** — cenário interativo textual entregue; não há geração de foto futurista, previsão científica ou modelagem urbana baseada em dados municipais.
6. **Operação pública nacional** — ainda precisa de banco e mídia persistentes, backups, políticas LGPD, proteção antispam/rate limit por infraestrutura, domínio e HTTPS; não basta simplesmente copiar o SQLite para hospedagem temporária.

## Como começar

Extraia o ZIP, execute `iniciar_aevia.bat` (Windows), abra `http://127.0.0.1:8013` e siga `docs/GUIA_DE_TESTE.md`.

**Critério de honestidade técnica:** o projeto está entregue para teste local, com estrutura e funcionalidades pré-publicação. Não está homologado como um acervo histórico nacional completo ou uma aplicação pronta para alto tráfego sem etapas adicionais.


## Revisão ampliada (13/11/2026)

- Corrigida assinatura SRI do Leaflet CSS e retirada do mapa a sobreposição “Carregando mapa...”.
- Coordenadas impossíveis são descartadas; cidades-piloto conhecidas possuem coordenadas corrigidas para contingência.
- Nomes de arquivos orbitais ISS e “View of Earth” foram filtrados do acervo para não substituir fotografias de ruas.
- Criada configuração guiada de senha do administrador e página de checklist de publicação.
- Fila administrativa agora apresenta pendentes, aprovados e rejeitados, com exclusão definitiva.
- Incluídos rascunhos informativos de privacidade e termos de contribuição para revisão antes da abertura pública.
- **14 testes automatizados aprovados**; verificação offline de interface em 1280 px e 390 px, sem erros de JavaScript e sem rolagem horizontal.
- **Restrições**: nenhuma integração online foi validada neste ambiente sem rede externa; validação de mapas, Wikimedia, IBGE, IA e geocodificação no servidor final continua obrigatória. Site público não foi criado. Hospedagem persistente, backups, proteção de abuso, contato, termos finais e revisão LGPD permanecem pendentes.

Veja também `RELATORIO_VALIDACAO_V1_2.md` para a correção de busca por cidade e geocodificação no uso local.
