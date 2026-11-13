# Guia rápido de teste do AEVIA

## Preparação

1. Abra o arquivo ZIP extraído e execute `iniciar_aevia.bat`.
2. Aguarde no terminal a informação de quantos municípios foram sincronizados.
3. No navegador, entre em `http://127.0.0.1:8013`.

## O que testar no navegador

- **Catálogo:** digite “Ouro Preto” e selecione MG; depois pesquise “São Paulo” e selecione SP. O mapa deve mover o centro quando houver coordenadas cadastradas.
- **Rua:** clique em qualquer local do mapa. A marcação muda, e a consulta de fotografias passa a utilizar esse ponto. A busca por endereço digitado pode usar Nominatim em baixo volume sem chave no teste local, ou Geoapify com chave.
- **Acervo:** pressione “Buscar registros”. Se existirem fotos georreferenciadas próximas, aparecem com crédito e link da fonte. Registros sem ano aparecem em seção separada. Se a conexão ao Commons falhar, haverá mensagem de indisponibilidade.
- **Linha do tempo:** altere o ano para 1920 e repita a busca. O sistema deve omitir dos resultados datados fotografias com ano posterior; imagens sem data permanecem separadas.
- **Comparar:** em uma foto do acervo, escolha "Comparar como A" e em outra "Como B". Verifique imagens lado a lado. Isso não comprova o mesmo ângulo ou endereço.
- **2050:** escolha percentuais para verde, mobilidade e patrimônio e clique em “Explorar cenário”. O texto deve mudar, e o aviso de **hipótese, não previsão** deve permanecer.
- **Participar:** envie uma foto, local e relato com autorização. A mensagem deve confirmar **pendente de revisão**. Não deve aparecer no acervo público até aprovação.
- **Administração:** configure senha no `.env`, reinicie o servidor e abra o rodapé. Confira a fila; imagens pendentes somente podem ser vistas pelo administrador. Faça a revisão manual e confirme a publicação.
- **IA:** se houver chave de modelo e autorização do colaborador, a triagem opcional pode ser acionada no painel; o sistema nunca aprova automaticamente.

## Verificações automáticas

```bash
python -m pytest -q
```

Os testes automatizados não dependem da internet. Integrações externas devem ser verificadas também em um ambiente online real.

## Condições que impedem declarar o projeto pronto para público amplo

- Sincronização nacional não concluída ou fotos/municípios não disponíveis no serviço externo.
- Serviço de hospedagem sem volume persistente e backups.
- Senhas e segredos sem configuração segura.
- Ausência de política de privacidade/LGPD, regras de envio, denúncia e exclusão.
- Falta de limitação de requisições e proteção antispam em produção.
- Contratos/licenças de provedores de mapas e geocodificação não revisados para uso nacional.

Não publique fotos ou histórias de terceiros sem verificar a autorização apropriada.

## Teste obrigatório da troca de cidades na versão 1.2

1. Em **CIDADE BRASILEIRA**, selecione todo o nome anterior, digite `Juiz de Fora` e aguarde ou pressione **Enter**. Confira o rótulo `Juiz de Fora — MG`, código `3136702` e coordenadas aproximadas `-21.7609, -43.3503`.
2. Digite `Ouro Preto` e clique em **Buscar**. O rótulo deve atualizar para `Ouro Preto — MG`.
3. Digite `Mariana` e escolha na lista. A galeria da cidade anterior deve desaparecer.
4. Em Juiz de Fora, digite `Rua Halfeld` e clique em **Localizar endereço**. A busca depende de conexão externa, pode retornar resultados aproximados e exige seleção de um resultado para mover o ponto.
5. Se o endereço não aparecer, selecione a posição aproximada clicando no mapa. Não presuma que fotografias correspondem à rua sem conferir a fonte.
6. Teste **Buscar registros**, comparação, AEVIA 2050, administração e envio em modo local. Se o catálogo estiver parcial, sincronize no painel.
