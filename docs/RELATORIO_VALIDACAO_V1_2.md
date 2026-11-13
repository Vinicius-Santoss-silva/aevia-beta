# AEVIA 1.2 — Registro de validação (13/11/2026)

## Problema relatado e correções

**Sintoma:** digitar `Juiz de Fora` deixava o mapa e o município selecionado em Cataguases.

**Causa:** a interface oferecia lista de sugestões, mas não acionava a seleção com Enter/botão Buscar, e mantinha cidade antiga até clicar uma sugestão.

**Correção:** a cidade exata é selecionada automaticamente após pausa na digitação. Enter e botão Buscar acionam a escolha. Nomes ambíguos exigem selecionar a opção da UF. Alteração atualiza código IBGE, coordenadas, mapa, galeria, comparação e AEVIA 2050, além de invalidar respostas atrasadas.

**Endereços:** busca com Geoapify se houver chave; para uso local sem chave, Nominatim público sob limite e cache, sem consultas de autocomplete. Resultados são aproximados. Publicação nacional com alto tráfego deve usar serviço próprio ou contratado.

**Sincronização:** catálogo nacional preserva coordenadas previamente carregadas caso a fonte complementar falhe; inicializações seguintes reutilizam banco já completo.

## Testes realizados no ambiente desta entrega

- Testes automatizados FastAPI/SQLite com `pytest`: **14 aprovados**.
- Verificação sintática do JavaScript com `node --check`: **aprovada**.
- Código Python compilado com `compileall`: **aprovado**.
- Simulação de interface em Chromium, com APIs e fontes externas simuladas: **aprovada** em 1280 px e 390 px; alternância Cataguases → Juiz de Fora → Ouro Preto → Mariana, clique de botão/Enter, busca de rua, AEVIA 2050, busca de acervo e ausência de erros de JavaScript/rolagem horizontal.

## O que NÃO foi verificado

- O acesso real aos endpoints de Wikimedia Commons, Geoapify/Nominatim, IBGE e tiles de mapa no navegador do usuário.
- Escalabilidade de alto tráfego, sistema antifraude, auditoria de segurança e restauração de backups.
- Conformidade jurídica definitiva de direitos autorais, consentimento e LGPD.
- Georreferência e data de todas as fotografias históricas do país. Uma busca textual pode trazer imagens não correspondentes; a interface avisa essa incerteza.

**Conclusão:** pacote local revisado e testado; NÃO deve ser considerado publicação nacional plenamente homologada sem as verificações acima.
