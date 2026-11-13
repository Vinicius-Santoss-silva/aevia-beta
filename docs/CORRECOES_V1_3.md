# AEVIA 1.3 — Revisão de incidentes

- Separação do servidor local para porta **8013**, eliminando confusão com aplicações antigas na 8000.
- Versão V1.3 visível no cabeçalho e no rodapé, endpoint /api/status e cabeçalho HTTP X-AEVIA-Version.
- HTML, CSS e JS servidos com Cache-Control no-store para reduzir interface desatualizada.
- Campo de cidade exibe estado **não confirmada** durante a digitação, em vez de continuar apresentando a cidade anterior.
- Busca automática para correspondências exatas sem acentos e também botão Buscar/Enter; resultados ambíguos precisam de escolha de UF.
- Botões de endereço, acervo e 2050 bloqueados enquanto a cidade ainda não está confirmada.
- Mapa reduzido para 340 px desktop, 300 px tablet, 270 px mobile e 240 px celular compacto.
- O catálogo ainda depende de uma primeira sincronização online com IBGE; acervos e mapas dependem de serviços externos.

## Testes necessários após extrair

1. Digite `sao paulo` e confirme **São Paulo — SP**.
2. Digite `juiz de fora` e confirme **Juiz de Fora — MG**.
3. Digite `ouro preto` e confirme **Ouro Preto — MG**.
4. Consulte uma rua e verifique o resultado aproximado e o marcador.
5. Mova a linha do tempo, busque acervo, compare fotos e veja 2050.
6. Teste em celular, administração e contribuições antes de colocar na internet.

## Limite da entrega

Não há como garantir fotos históricas em todo município nem certificar local, autoria ou época automaticamente. Serviços externos e recursos de produção exigem testes e configuração de hospedagem.
