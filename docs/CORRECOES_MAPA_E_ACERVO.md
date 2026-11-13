# AEVIA — correções visíveis nos testes de 13/11/2026

- Corrigida a assinatura SRI da folha de estilos do Leaflet, que não correspondia ao arquivo oficial (erro que pode bloquear o carregamento do mapa).
- Removida a mensagem "Carregando mapa" quando o Leaflet inicializa.
- Impedida a seleção de coordenadas impossíveis para o Brasil. Coordenadas incorretas de localidades conhecidas, como Cataguases, recebem recuperação segura.
- Fotos orbitais da estação espacial ISS e imagens genericamente intituladas "View of Earth" deixaram de aparecer misturadas a fotos de ruas.
- Incluídos testes de regressão para coordenadas, fotos orbitais e inicialização do mapa.

## Importante

O mapa ainda requer internet para carregar as bibliotecas Leaflet e os mosaicos OpenStreetMap. O arquivo local corrigiu um erro real no CSS, mas o acesso externo pode estar bloqueado pela rede, navegador ou extensão.

O catálogo nacional cobre municípios, **não garante fotografias históricas** de cada município. Imagens do Wikimedia Commons podem ter geotags aproximadas e datas incorretas; revise as fontes antes de publicar. A busca por rua precisa configurar GEOAPIFY_API_KEY. A IA de triagem precisa configurar GEMINI_API_KEY e consentimento.

Para usar, extraia o ZIP como uma **nova pasta**, feche o terminal anterior e execute `iniciar_aevia.bat`. Não substitua a pasta anterior se já houver contribuições salvas em `storage/`.
