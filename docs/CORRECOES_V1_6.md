# AEVIA 1.6 — Fontes por cidade e AEVIA 2050 com evidência

## 1. Pesquisa específica na Brasiliana Fotográfica

O botão junto ao acervo agora abre `https://brasilianafotografica.bn.gov.br/brasiliana/discover?query=<cidade>` usando o município selecionado, em vez de abrir sempre a página inicial. Esse endereço corresponde à pesquisa pública do portal (verificado em artigos da instituição). **Não é uma integração API nem garantia de registros da cidade**: confira os metadados e a licença na página aberta. Os cartões já recebidos do Wikimedia Commons continuam usando links individuais de origem.

## 2. AEVIA 2050 sem trocar só o nome

A API `/api/2050` consulta o IBGE (SIDRA, tabela 4714, Censo 2022, variáveis 93 população, 6318 área e 614 densidade), exibe números com fonte e considera a escala populacional da cidade para formular **hipóteses** de áreas verdes e mobilidade. O patrimônio continua uma pauta narrativa, pois essa tabela do IBGE não mede o patrimônio local.

Se não houver dados acessíveis, o AEVIA informa claramente que o cenário é genérico. **Não existem previsões reais ou imagens de 2050**. Os números nunca são inventados.

## 3. Testes e publicação

Execute `python -m pytest -q` e valide ao vivo em http://127.0.0.1:8016. A porta foi alterada para evitar abrir versões antigas. Para publicar é obrigatório configurar persistência para mídia e dados, HTTPS, administração segura, diretos autorais, privacidade, controle de abuso e validar integrações públicas.

*Fontes:* https://sidra.ibge.gov.br/tabela/4714 ; https://servicodados.ibge.gov.br/api/v3/agregados/4714 ; https://brasilianafotografica.bn.gov.br/brasiliana/
