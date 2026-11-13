# AEVIA — O tempo mora em cada lugar

Projeto web de memória histórica de municípios brasileiros. Versão 1.7 (Beta de demonstração com fontes contextualizadas e envios temporariamente desativados), com **FastAPI + SQLite + Leaflet + HTML/CSS/JavaScript**. Não exige serviços pagos para abrir e explorar as partes básicas.

**PARA PUBLICAR A BETA GRATUITA:** leia primeiro `docs/PUBLICAR_BETA_GRATUITA.md`. A Beta tem o envio de fotos desligado por segurança; não use o Guia Docker antigo para criar servidor gratuito com recebimento público de arquivos.

## Começar em Windows (recomendado)

1. Instale o [Python 3.11 ou superior](https://www.python.org/downloads/). Marque **Add Python to PATH** na instalação.
2. Extraia todo o ZIP em uma pasta (não execute de dentro do ZIP).
3. Dê dois cliques em **`iniciar_aevia.bat`**. A primeira execução instala bibliotecas e tenta baixar o catálogo nacional. As seguintes reutilizam o catálogo quando já está completo.
4. O navegador abre automaticamente em **http://127.0.0.1:8017** (porta nova, distinta do AEVIA anterior). Precisa de internet para os mapas, o Wikimedia Commons e a primeira sincronização.

### Terminal em macOS/Linux

```sh
bash iniciar_linux_mac.sh
```

### Execução manual

```sh
python -m pip install -r requirements.txt
python -m app.sync_data
python -m app.launcher
```

**Importante:** use `python -m app.sync_data` antes da primeira utilização para que a pesquisa inclua os municípios brasileiros. Se a internet estiver indisponível, o sistema inicia com uma lista reduzida de cidades de exemplo; o indicador na interface mostrará a contagem real.

## Ativar administração

No Windows, abra **`configurar_administrador.bat`** para criar senha longa e segredo aleatório sem editar código. Depois feche e reabra o servidor. A senha não aparece enquanto é digitada. Como alternativa manual, copie `.env.example` para `.env`. Remova o `#` e defina pelo menos:

```
ADMIN_PASSWORD=coloque-sua-senha-longa
SESSION_SECRET=uma-sequencia-aleatoria-com-mais-de-32-caracteres
```

Feche e reabra o servidor. Clique em **Administração** no rodapé. Lá é possível atualizar o cadastro, aprovar/rejeitar imagens e consultar a fila de contribuições.

**Nunca** inclua `.env` no GitHub. A pasta `storage/` contém imagens e dados privados pendentes e também não deve ser publicada nem versionada.

## Recursos e limitações por etapa

| # | Funcionalidade | Implementado nesta entrega | Dependência/limite real |
|---|---|---|---|
| 1 | Pesquisa nacional de municípios | Sim, sincronização com IBGE e pesquisa por nome/UF | Necessita internet para carregar lista nacional na primeira execução. Centro de cidade vem de base comunitária e é aproximado. |
| 2 | Acervo de imagens históricas | Sim, consulta geográfica e pesquisa complementar por nome no Wikimedia Commons com créditos, data e licença | Não garante cobertura de todos os lugares. Brasiliana tem link externo, não ingestão automatizada. |
| 3 | Site e mapa interativo | Sim, Leaflet/OpenStreetMap, pesquisa de cidades e marcação por clique | Mapas online; tiles públicos sujeitos à política de uso. |
| 4 | Linha do tempo e comparação | Sim, data filtrada pelos metadados e comparação de 2 imagens | Fotos com datas ausentes aparecem separadas. Não garante mesma câmera/rua. |
| 5 | Banco de dados | Sim, SQLite com municípios, cache e contribuições | Produção nacional exige banco/armazenamento persistentes e backups. |
| 6 | Colaborações da comunidade | Sim, relatos e fotos, direitos/licenças, fila privada de aprovação | Ainda não há contas individuais, denúncia pública ou reenvio de revisões. |
| 7 | IA de triagem | Integração opcional com Gemini + regras locais + revisão humana obrigatória | Exige chave configurada e autorização explícita do remetente; IA não prova fatos históricos. |
| 8 | AEVIA 2050 | Sim, cenário hipotético com dados do Censo 2022 do IBGE, quando acessíveis | Sem dados locais, informa indisponibilidade e usa narrativa genérica; não produz previsões nem imagens futuristas. |
| 9 | Publicação | **Não realizada**, conforme solicitado | Preparar servidor persistente, domínio/HTTPS, backups, proteção antispam e escala. |

## Busca por cidade e rua (sem chave, uso local)

- **Cidades:** digite o nome (ex.: *Juiz de Fora*) e pressione **Enter**, clique em **Buscar**, ou selecione na lista. O sistema também reconhece automaticamente nomes exatos não ambíguos após uma pausa. O nome/UF da cidade selecionada fica visível.
- **Ruas:** após selecionar a cidade, digite o endereço e clique em **Localizar endereço**. No teste local, sem chave, utiliza a API pública do [OpenStreetMap Nominatim](https://nominatim.org/release-docs/latest/api/Search/) mediante ação explícita do visitante, nunca por autocomplete. Atribuição fica visível na interface. Resultados aproximados devem ser confirmados no mapa.
- O Nominatim público exige **máximo de 1 pedido/segundo, identificação do aplicativo, atribuição e cache**; há trava local para 1 pedido a cada 1,1 segundos e cache de 30 dias. Não é adequado para o lançamento com alto tráfego, múltiplos servidores ou consultas em massa. Consulte [a política oficial](https://operations.osmfoundation.org/policies/nominatim/).
- Para publicação nacional com mais acessos, configure `GEOAPIFY_API_KEY=...` no `.env` ou hospede seu próprio geocodificador, e defina `ENABLE_PUBLIC_NOMINATIM=no`. A opção de chave é aplicada no backend, sem expor o segredo no navegador.
- Sem serviço de geocodificação disponível, ainda é possível marcar um ponto no mapa clicando nele. O mapa depende de internet para carregar os mosaicos externos.

## IA (opcional)

Adicione `GEMINI_API_KEY=...` em `.env`. Dentro da moderação, a triagem só fica disponível se o autor assinalar que **autoriza envio a serviço externo de IA**. O resultado é um relatório de possíveis inconsistências e perguntas a verificar — **nunca é aprovação automática, autenticação de fotografia, geolocalização comprovada ou prova histórica**. A disponibilidade, gratuidade e custos dependem do provedor e devem ser verificados por você antes do uso.

## Como dados e mídia são tratados

- Imagens do Wikimedia Commons aparecem com link para a página de origem, crédito e licença informada pelo metadado; **consulte a página antes de reutilizar a imagem**.
- A consulta ao Commons combina **proximidade geográfica** e, onde houver poucos arquivos, **pesquisa textual pelo nome da cidade**. Resultados textuais **não comprovam o lugar** e são sinalizados na interface. Nenhuma busca garante reconhecimento de rua nem ângulo exato.
- A fonte de município é a API do IBGE. Coordenadas do centro vêm do projeto comunitário [kelvins/municipios-brasileiros](https://github.com/kelvins/municipios-brasileiros) (licença MIT). Nomes e códigos podem ser atualizados no IBGE.
- Envio de imagem é convertido para JPEG, elimina metadados EXIF/GPS e é armazenado fora de arquivos públicos até aprovação. A checagem local detecta arquivos inválidos, tamanho excessivo e duplicação literal (hash).
- O sistema **não confirma** data, local, autoria nem veracidade de uma fotografia. A revisão exige acesso ao material original, referências, permissões e, quando preciso, avaliação humana externa.
- Os textos de 2050 são cenários condicionais didáticos, sem qualquer pretensão de previsão ou visualização fotorrealista.

## Testes

```sh
python -m pytest -q
```

Os 14 testes automatizados cobrem catálogo, cenários, envio, privacidade antes de aprovação, autenticação, exclusão, mapa, coordenadas, filtragem orbital e endpoints. A interface também foi exercitada em navegador offline simulado (desktop e celular). **Sem internet, não é possível fazer validação real de Wikimedia/IBGE/Nominatim/Geoapify/Gemini** neste ambiente. É necessário efetuar testes reais de integração antes de publicar.

## Checklist obrigatório antes da publicação nacional

1. Usar HTTPS e segredos de autenticação seguros. Configurar rate limiting no proxy/firewall, autenticação robusta e proteção antispam; revisar cabeçalhos, privacidade e logs.
2. Migrar banco e mídia para infraestrutura com persistência confiável e backups testados (SQLite em hospedagem efêmera perde dados).
3. Definir termos de uso, política de privacidade, LGPD, retenção/exclusão de dados, canal de reclamações e licenças das contribuições.
4. Revisar autorização de mídia do acervo, consultar condições do Wikimedia e direitos de terceiros.
5. Configurar provedor de busca de ruas para maior tráfego e limites de mapas (OpenStreetMap), incluindo escalabilidade do provedor de tiles em tráfego público.
6. Conferir os dados reais de cidade/foto antes do lançamento, acessibilidade, mobile, moderação e testes de integração com serviços externos.
7. Configurar domínio, monitoramento, backups e deploy somente quando você autorizar.

## Organização do projeto

```
app/main.py           Endpoints e regras de acesso
app/db.py             SQLite e tabelas
app/sources.py        Municípios, Wikimedia e geocodificação opcional
app/moderation.py     Triagem local e IA opcional
app/sync_data.py      Sincronização nacional
static/index.html     Interface principal
static/style.css      Visual responsivo
static/app.js         Mapa, buscas, envio, comparação e 2050
tests/                Testes do backend
.env.example          Exemplo de variáveis de ambiente
```

### Referências técnicas (verificadas em novembro de 2026)

- [IBGE API de Localidades](https://servicodados.ibge.gov.br/api/docs/localidades)
- [Wikimedia Commons — pesquisa por localização](https://commons.wikimedia.org/wiki/Commons:Search_by_location)
- [Wikimedia Commons — metadados de imagens](https://commons.wikimedia.org/wiki/Commons:Machine-readable_data)
- [Dados abertos de coordenadas municipais — kelvins](https://github.com/kelvins/municipios-brasileiros)
- [Geoapify geocoding API](https://apidocs.geoapify.com/docs/geocoding/)
- [OpenStreetMap tile usage](https://operations.osmfoundation.org/policies/tiles/)
- [Gemini generateContent](https://ai.google.dev/api/generate-content)

Este projeto é um **MVP funcional pré-publicação**, não um serviço nacional já homologado ou um acervo completo de cidades e épocas. A integridade histórica é prioridade acima da quantidade de registros.

## Revisões de 13/11/2026: instalação e publicação

- `configurar_administrador.bat`: cria credenciais locais de moderação, sem publicar segredos.
- `verificar_publicacao.bat`: lista pendências técnicas e de política antes de abrir o site ao público; **não é certificado de segurança**.
- `static/privacidade.html` e `static/termos.html`: rascunhos informativos para revisão antes do lançamento.
- Moderação: agora mostra pendentes, aprovados e rejeitados; inclui exclusão administrativa de registros e imagem.
- As regras de produção exigem HTTPS, senha longa e segredo persistente. Em hospedagem efêmera, SQLite e `storage/uploads` **podem ser perdidos**, portanto NÃO declare o projeto pronto para receber dados reais sem persistência e backups.
- O mapa pode não aparecer se a CDN ou os blocos de mosaico forem bloqueados. A integração Geoapify por chave permanece opcional, assim como a triagem Gemini.
- **O último clique de publicação não está automatizado:** domínio/hospedagem, dados persistentes, termo final, contato público, segurança e testes reais são decisões externas.

## Ajustes de busca da versão 1.2 (13/11/2026)

- O campo de cidade agora efetivamente **seleciona** o município via digitação de nome exato, Enter, botão Buscar ou escolha na lista. Apenas digitar uma palavra ambígua não muda silenciosamente o mapa: escolha o município correto.
- Buscar uma rua usa o código IBGE da cidade selecionada. Com internet, no uso local, não é necessária chave paga. A precisão das coordenadas depende da fonte e deve ser verificada pelo visitante.
- A seleção de cidade limpa a galeria e a comparação anteriores e invalida respostas atrasadas de buscas que estavam em andamento.
- Sincronização do IBGE reutiliza coordenadas já conhecidas se o CSV auxiliar estiver indisponível e não precisa baixar os mesmos 5.571 municípios a cada inicialização. Para atualizar manualmente, use a função de administração ou defina `AEVIA_FORCE_SYNC=yes`.
- Textos de privacidade/termos são **minutas**, não aprovação jurídica. Não publique para aceitar dados reais de terceiros sem revisão.

## Notas da versão 1.3

- O AEVIA 1.7 usa exclusivamente a porta **8017** na inicialização assistida; as versões antigas costumavam usar 8000 a 8016. Confira o selo **V1.7** no topo.
- O campo Cidade brasileira seleciona automaticamente a única cidade encontrada com o nome exato, inclusive sem acentos. Se houver mais de um município homônimo, escolha o estado na lista.
- A indicação **"Cidade ainda não confirmada"** impede confundir o mapa da cidade anterior com o nome digitado.
- O mapa está menor e cabe melhor no celular. As fotos continuam a depender de existência, georreferenciamento e licença da fonte.
- Para produção com Docker e disco persistente, consulte `docs/PUBLICACAO_COM_DOCKER.md`. Não publique usando disco temporário.

## Formulário simples de contribuição — v1.6

A licença técnica foi substituída por uma pergunta acessível sobre os direitos autorais da **fotografia anexada**. Sem foto, não aparece a pergunta. Fotos de terceiros exigem comprovante/identificação da autorização ou fonte da licença. A opção “não sei” impede o envio da foto. O servidor também valida essas regras, sem confiar apenas no navegador. Contribuições continuam pendentes de revisão humana.


## Novidades da versão 1.6 (13/11/2026)

- A Brasiliana Fotográfica recebe o nome da **cidade selecionada** como termo da busca externa: dois municípios não abrem mais indiscriminadamente a página inicial. O portal pode retornar zero resultados e o AEVIA não valida nem importa automaticamente as fotos da Brasiliana.
- AEVIA 2050 consulta a **tabela 4714 do IBGE** (população residente, área municipal e densidade do Censo 2022). Só mostra números realmente fornecidos pela API. A escala populacional modifica hipóteses narrativas; a cidade continua sem previsão real do futuro.
- Se a consulta falhar ou não houver dado, exibe **Dados indisponíveis** e identifica o cenário genérico.
- Novo controle para não apresentar a resposta de um município anterior ao trocar rapidamente de cidade.
- O navegador local abre em **http://127.0.0.1:8017** e a versão visível é **V1.7**.
- Testes de regressão: `python -m pytest -q`, incluindo respostas simuladas do IBGE e falha de conexão. Como este ambiente não acessa as APIs externas, a integração real deve ser testada na máquina e no servidor da publicação.

Veja `docs/CORRECOES_V1_6.md`.


## Beta de publicação v1.7

Para lançar uma versão pública sem aceitar dados privados e sem risco de perder fotos na hospedagem Free, use `APP_ENV=beta` e `ENABLE_PUBLIC_CONTRIBUTIONS=no`. A inicialização falha se o envio estiver ativado no modo Beta. Veja `docs/PUBLICAR_BETA_GRATUITA.md` e `render.yaml`. Na versão Beta a busca manual de ruas por serviço público Nominatim é desativada; o visitante pode marcar o ponto no mapa. A Brasiliana é link externo e pode retornar nenhum resultado; o Wikimedia Commons continua como acervo de fotos com fontes e ressalvas.
