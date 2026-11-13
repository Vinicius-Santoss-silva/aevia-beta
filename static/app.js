'use strict';
const $ = (s) => document.querySelector(s);
const state = {
  city: {id:3115300,name:'Cataguases',uf:'MG',latitude:-21.3892,longitude:-42.6963},
  lat:-21.3892,lon:-42.6963,pointValid:true,selectedYear:2026,map:null,marker:null,photos:[],
  compare:{a:null,b:null},scenarioCircle:null,geocodeReady:false
};
const dom = {};
const el = (tag, cls='', content='') => {
  const node=document.createElement(tag); if(cls) node.className=cls;
  if(content!==undefined&&content!==null) node.textContent=String(content); return node;
};
const fmt = (v) => String(v).replace(/\s+/g,' ').trim();
function message(text, type='') {
  const t=$('#toast'); t.textContent=text; t.className='toast visible '+type;
  window.clearTimeout(message.tid); message.tid=window.setTimeout(()=>t.classList.remove('visible'),4000);
}
async function api(endpoint,options={}) {
  let res;
  try {res=await fetch(endpoint,{credentials:'same-origin',...options});}
  catch(e){throw new Error('Não foi possível conectar ao servidor AEVIA.');}
  let json; try{json=await res.json();}catch{json={};}
  if(!res.ok) throw new Error(json.detail || `Erro HTTP ${res.status}`);
  return json;
}
function isBrazilCoordinate(lat,lon) {
  return Number.isFinite(Number(lat)) && Number.isFinite(Number(lon)) &&
         Number(lat)>=-35 && Number(lat)<=6 && Number(lon)>=-75 && Number(lon)<=-30;
}
function initMap() {
  if(typeof L==='undefined') {$('#map').innerHTML='<div class="map-placeholder">Mapa indisponível.<small>Verifique sua conexão com a internet e recarregue a página.</small></div>';return;}
  // Retirar a mensagem inicial: ela não deve cobrir o mapa renderizado.
  $('#map').replaceChildren();
  state.map=L.map('map',{zoomControl:false}).setView([state.lat,state.lon],14);
  L.control.zoom({position:'bottomright'}).addTo(state.map);
  let tileErrors=0;
  const layer=L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{
    maxZoom:19,attribution:'&copy; <a target="_blank" href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>'
  }).addTo(state.map);
  layer.on('tileerror',()=>{
    tileErrors++;
    if(tileErrors>=3 && !$('#mapError')) {
      const alert=el('div','map-error','Não foi possível carregar as imagens do mapa. Verifique sua conexão ou bloqueadores de rede.');
      alert.id='mapError'; $('#map').append(alert);
    }
  });
  layer.on('tileload',()=>{tileErrors=0;const error=$('#mapError');if(error)error.remove();});
  state.marker=L.circleMarker([state.lat,state.lon],{radius:9,color:'#fff',weight:3,fillColor:'#bc925e',fillOpacity:1}).addTo(state.map);
  state.map.on('click',ev=>{
    if(!isBrazilCoordinate(ev.latlng.lat,ev.latlng.lng)){
      message('Selecione um ponto dentro do Brasil.');return;
    }
    setPoint(ev.latlng.lat,ev.latlng.lng,true);
  });
  requestAnimationFrame(()=>state.map.invalidateSize());
}
function setPoint(lat,lon,manual=false) {
  lat=Number(lat);lon=Number(lon);
  if(!isBrazilCoordinate(lat,lon)){
    message('Coordenadas inválidas: selecione um ponto dentro do Brasil.');return false;
  }
  state.lat=lat;state.lon=lon;state.pointValid=true;
  if(state.map) {
    if(state.marker) state.marker.setLatLng([lat,lon]);
    else state.marker=L.circleMarker([lat,lon],{radius:9,color:'#fff',weight:3,fillColor:'#bc925e',fillOpacity:1}).addTo(state.map);
    if(!manual)state.map.setView([lat,lon],15);
  }
  $('#selectedPoint').textContent='• '+(manual?'PONTO MARCADO':'CENTRO DA CIDADE');
  $('#coordsInfo').textContent=`${lat.toFixed(4)}, ${lon.toFixed(4)}`;
  return true;
}
function chooseCity(city) {
  ++citySearchSequence; ++archiveSearchSequence; ++futureRequestSequence;
  state.city=city;
  $('#citySearch').value=`${city.name} — ${city.uf}`;$('#cityResults').hidden=true;
  $('#cityName').textContent=`${city.name} — ${city.uf}`;
  const brasiliana=$('#brasilianaLink');
  brasiliana.href='https://brasilianafotografica.bn.gov.br/brasiliana/discover?query='+encodeURIComponent(city.name);
  brasiliana.textContent=`Pesquisar ${city.name} na Brasiliana ↗`;
  $('#commonsSearchLink').href='https://commons.wikimedia.org/w/index.php?search='+encodeURIComponent(city.name+' '+city.uf)+'&title=Special%3AMediaSearch&type=image';
  $('#commonsSearchLink').textContent=`Pesquisar ${city.name} no Wikimedia Commons ↗`;
  $('#brasilianaHelp').textContent=`Acervo externo: consulta sem garantia de resultados por “${city.name}”. Verifique o local e os direitos antes de usar imagens.`;
  $('#futureFacts').replaceChildren(el('p','',`Selecione “Explorar cenário para 2050” para consultar dados do Censo 2022 de ${city.name} — ${city.uf}.`));
  $('#futureThemes').replaceChildren(el('p','', 'Aguardando atualização para a cidade selecionada.'));
  $('#addressResults').replaceChildren();
  $('#addressSearch').value='';
  if(isBrazilCoordinate(city.latitude,city.longitude)) {
    setPoint(city.latitude,city.longitude,false);
  } else {
    state.pointValid=false;
    if(state.marker && state.map){state.map.removeLayer(state.marker);state.marker=null;}
    if(state.map)state.map.setView([-14.2,-51.9],4);
    $('#coordsInfo').textContent='Sem coordenadas confiáveis; marque um ponto no mapa.';
    $('#selectedPoint').textContent='• MARQUE UM PONTO ANTES DE CONSULTAR';
    message('Este município não tem centro geográfico cadastrado. Marque um ponto no mapa ou sincronize as coordenadas.');
  }
  $('#cityHint').textContent=`Município ${city.id} selecionado.`;
  $('#cityHint').className='field-help success-selection';
  $('#loadArchive').disabled=false;
  $('#addressGo').disabled=false;
  $('#generate2050').disabled=false;
  $('#futureCity').textContent=`${city.name} — ${city.uf}`;
  $('#futureThemes').replaceChildren(el('p','','Ajuste os parâmetros e clique em Explorar cenário para esta cidade.'));
  state.photos=[];state.compare={a:null,b:null};populateCompare();
  $('#photoGallery').replaceChildren(emptyState('Escolha um ponto do mapa e busque os registros próximos.'));
  $('#undatedBox').hidden=true;$('#resultsCount').textContent='0';
  $('#archiveStatus').textContent='Clique em “Buscar registros” para consultar esta cidade.';
}
function emptyState(text,title='Nenhum registro para exibir'){
  const wrap=el('div','empty-state');wrap.append(el('span','empty-icon','◷'),el('h4','',title),el('p','',text));return wrap;
}
let searchTimer;
let citySearchSequence=0;
let archiveSearchSequence=0;
let futureRequestSequence=0;
function cityNameKey(value){
  return String(value||'').normalize('NFKD').replace(/[\u0300-\u036f]/g,'')
    .toLowerCase().replace(/[^a-z0-9]+/g,' ').trim();
}
function cityQueryMatches(city,text){
  const query=cityNameKey(text);
  return query===cityNameKey(city.name) || query===cityNameKey(city.name+' '+city.uf);
}
function cityInputIsCurrent(){
  return cityQueryMatches(state.city,$('#citySearch').value);
}
function markCityInputPending(){
  const hint=$('#cityHint');
  hint.className='field-help needs-selection';
  hint.textContent='Pesquisando cidade... aguarde a seleção ou pressione Enter.';
  $('#cityName').textContent='Cidade ainda não confirmada';
  $('#coordsInfo').textContent='O mapa mantém o ponto anterior até a nova cidade ser selecionada.';
  $('#loadArchive').disabled=true;
  $('#addressGo').disabled=true;
  $('#generate2050').disabled=true;
}
function renderCityOptions(cities){
  const list=$('#cityResults');list.replaceChildren();
  for(const city of cities){
    const b=el('button','search-item');b.type='button';b.setAttribute('role','option');
    b.append(el('span','',city.name),el('span','',city.uf));
    b.onclick=()=>chooseCity(city);list.append(b);
  }
  if(!cities.length)list.append(el('div','search-item','Nenhum município encontrado.'));
  list.hidden=false;
}
async function selectTypedCity(){
  const query=fmt($('#citySearch').value);
  if(!query){message('Digite o nome de uma cidade brasileira.');return false;}
  if(cityInputIsCurrent()){
    $('#cityHint').textContent=`Município ${state.city.id} selecionado.`;
    $('#cityResults').hidden=true;
    return true;
  }
  const seq=++citySearchSequence;
  $('#cityGo').disabled=true;
  $('#cityHint').textContent='Consultando municípios...';
  try{
    const data=await api('/api/municipios?q='+encodeURIComponent(query)+'&limit=50');
    if(seq!==citySearchSequence)return false;
    const exact=data.results.filter(city=>cityQueryMatches(city,query));
    if(exact.length===1){chooseCity(exact[0]);message(`Cidade selecionada: ${exact[0].name} — ${exact[0].uf}`,'success');return true;}
    if(data.results.length===1){chooseCity(data.results[0]);message(`Cidade selecionada: ${data.results[0].name} — ${data.results[0].uf}`,'success');return true;}
    renderCityOptions(exact.length>1?exact:data.results);
    $('#cityHint').className='field-help needs-selection';
    $('#cityHint').textContent=data.results.length
      ? 'Há mais de uma opção. Clique na cidade correta e no estado.'
      : 'Cidade não encontrada. Confira o nome e o estado.';
    message(data.results.length?'Selecione a cidade na lista.':'Cidade não encontrada.');
    return false;
  }catch(err){markCityInputPending();$('#cityHint').textContent='Falha ao consultar as cidades. Confira a conexão e tente novamente.';message(err.message);return false;}
  finally{$('#cityGo').disabled=false;}
}
async function ensureCitySelected(){
  if(cityInputIsCurrent())return true;
  return selectTypedCity();
}
async function searchCity(){
  const q=fmt($('#citySearch').value);
  if(q.length<2){$('#cityResults').hidden=true;return;}
  const seq=++citySearchSequence;
  try{
    const data=await api('/api/municipios?q='+encodeURIComponent(q)+'&limit=15');
    if(seq!==citySearchSequence || fmt($('#citySearch').value)!==q)return;
    const exact=data.results.filter(city=>cityQueryMatches(city,q));
    if(exact.length===1){chooseCity(exact[0]);return;}
    renderCityOptions(data.results);
  }catch(e){if(seq===citySearchSequence){$('#cityHint').textContent='Não foi possível consultar o catálogo. Tente novamente.';message(e.message);}}
}
function validPhoto(url) {
  try{const u=new URL(url,location.origin);return u.protocol==='https:' || (u.origin===location.origin&&u.pathname.startsWith('/media/'));}catch{return false;}
}
function safeLink(url) {try{const u=new URL(url);return u.protocol==='https:'?u.href:null;}catch{return null;}}
function galleryCard(item,unknown=false){
  const card=el('article','photo-card');
  const img=el('img');img.loading='lazy';img.alt=item.title||'Foto do acervo';
  if(item.image&&validPhoto(item.image))img.src=item.image;
  else img.alt='Sem prévia de imagem disponível';
  img.onerror=()=>{img.removeAttribute('src');img.alt='Não foi possível carregar a imagem';};
  const body=el('div','photo-card-content');const meta=el('div','photo-meta');
  meta.append(el('span','',item.year?`ANO ${item.year}`:(item.historic_year?`ANO ${item.historic_year}`:'DATA NÃO CONFIRMADA')),
              el('span','',item.kind==='commons'?'WIKIMEDIA':'COMUNIDADE'));
  const title=el('div','photo-title',(item.title||'Sem título').slice(0,110));
  const note=el('div','photo-note',item.kind==='commons'
    ?`Crédito: ${item.author||'consulte a fonte'} · Licença: ${item.license||'não identificada'}`
    :`Enviado por ${item.author_name} · Licença: ${item.license}`);
  const extra=el('div','photo-note',item.kind==='commons'
    ?(item.location_confidence==='busca_textual_nao_geolocalizada'?'Resultado por nome da cidade: localização NÃO verificada. Confira a fonte.':'Foto próxima ao ponto selecionado. Local/ângulo exatos não verificados.')
    :'Local e data declarados pelo colaborador; revisão humana realizada.');
  const controls=el('div','photo-buttons');
  if(item.image&&validPhoto(item.image)){
    const compare=el('button','','Comparar como A');compare.type='button';compare.onclick=()=>{
      if(!state.photos.some(p=>p.id===item.id))state.photos.push(item);
      state.compare.a=item.id;populateCompare();$('#comparar').scrollIntoView({behavior:'smooth'});
    };controls.append(compare);
    const compareB=el('button','','Como B');compareB.type='button';compareB.onclick=()=>{
      if(!state.photos.some(p=>p.id===item.id))state.photos.push(item);
      state.compare.b=item.id;populateCompare();$('#comparar').scrollIntoView({behavior:'smooth'});
    };controls.append(compareB);
  }
  const url=safeLink(item.source_url);
  if(url){const a=el('a','','Ver fonte ↗');a.href=url;a.target='_blank';a.rel='noopener noreferrer';controls.append(a);}
  body.append(meta,title,note,extra,controls);card.append(img,body);return card;
}
async function loadArchive(){
  if(!await ensureCitySelected())return;
  const searchId=++archiveSearchSequence;
  if(!state.pointValid || !isBrazilCoordinate(state.lat,state.lon)){message('Primeiro marque um ponto válido do Brasil no mapa.');return;}
  const button=$('#loadArchive');button.disabled=true;button.textContent='Consultando fontes...';
  $('#archiveStatus').textContent='Consultando registros e eliminando imagens espaciais que não mostram a cidade...';
  try{
    const [data,community]=await Promise.all([
      api(`/api/acervo?lat=${state.lat}&lon=${state.lon}&radius=5000&year=${state.selectedYear}&city_id=${state.city.id}`),
      api(`/api/contribuicoes?city_id=${state.city.id}&lat=${state.lat}&lon=${state.lon}`)
    ]);
    if(searchId!==archiveSearchSequence)return;
    const filteredCommunity=community.items.filter(i=>i.historic_year===null||i.historic_year<=state.selectedYear).map(i=>({
      ...i,year:i.historic_year,image:i.image||null}));
    const dated=[...data.items,...filteredCommunity.filter(i=>i.historic_year)].sort((a,b)=>(a.year||0)-(b.year||0));
    const undated=[...data.undated,...filteredCommunity.filter(i=>!i.historic_year)];
    state.photos=[...dated,...undated].filter(i=>i.image&&validPhoto(i.image));
    const list=$('#photoGallery');list.replaceChildren();
    if(dated.length){for(const p of dated)list.append(galleryCard(p));}
    else list.append(emptyState(`Não encontramos fotografias datadas para ${state.city.name} até ${state.selectedYear} nesta consulta. Experimente outro ano, marque outro ponto no mapa ou utilize as pesquisas externas na seção acima. Os acervos não cobrem todas as cidades.`, 'Nenhum registro datado encontrado'));
    $('#undatedBox').hidden=undated.length===0;
    $('#undatedCount').textContent='('+undated.length+')';
    const noDate=$('#undatedGallery');noDate.replaceChildren();
    for(const p of undated)noDate.append(galleryCard(p,true));
    $('#resultsCount').textContent=String(dated.length);
    $('#archiveStatus').textContent=(dated.length+undated.length===0)
      ? `Nenhum registro encontrado nesta consulta de ${state.city.name}. Confira também as fontes externas; resultados são variáveis.`
      : `${dated.length} registro(s) datado(s) até ${state.selectedYear} e ${undated.length} sem data documentada. Fonte externa pode conter dados incompletos.`;
    populateCompare();
  }catch(e){
    if(searchId!==archiveSearchSequence)return;
    $('#archiveStatus').textContent='Não foi possível consultar os acervos neste momento.';
    $('#photoGallery').replaceChildren(emptyState(e.message,'Acervo temporariamente indisponível'));
    $('#undatedBox').hidden=true;message(e.message);
  }finally{button.disabled=false;button.innerHTML='Buscar registros <span>↗</span>';}
}
function populateCompare(){
  for(const side of ['a','b']){
    const select=$('#compare'+side.toUpperCase());
    select.replaceChildren();
    const defaultOption=new Option('Selecione uma foto','');select.add(defaultOption);
    for(const p of state.photos)select.add(new Option(`${p.year??'?'} · ${(p.title||'Imagem').slice(0,43)}`,p.id));
    select.value=state.compare[side]||'';
    paintCompare(side);
  }
}
function paintCompare(side){
  const item=state.photos.find(p=>p.id===state.compare[side]);
  const box=$('#comparePhoto'+side.toUpperCase());box.replaceChildren();
  if(!item){box.append(el('span','', 'Selecione uma imagem do acervo'));return;}
  const img=el('img');img.alt=item.title||'Foto';img.src=item.image;
  const caption=el('span','compare-stamp',`${item.year||'Data não informada'} · ${(item.title||'Sem título').slice(0,90)}`);
  box.append(img,caption);
}
async function show2050(){
  const requestId=++futureRequestSequence;
  const cityId=state.city.id;
  const g=Number($('#greenSlider').value),m=Number($('#mobSlider').value),h=Number($('#heritageSlider').value);
  try{
    const data=await api(`/api/2050?city_id=${cityId}&green=${g}&mobility=${m}&heritage=${h}`);
    if(requestId!==futureRequestSequence || state.city.id!==cityId)return;
    $('#futureCity').textContent=data.city;
    const facts=$('#futureFacts');facts.replaceChildren();
    const profile=data.profile||{};
    if(data.data_available){
      const f=el('div','future-facts-grid');
      const formatNumber=n=>typeof n==='number'?n.toLocaleString('pt-BR',{maximumFractionDigits:2}):'não informado';
      for(const [name,val,unit] of [['População em 2022',profile.population,' habitantes'],['Área em 2022',profile.area_km2,' km²'],['Densidade em 2022',profile.density_per_km2,' hab./km²']]){
        const metric=el('div','future-metric');metric.append(el('small','',name),el('strong','',formatNumber(val)+(val==null?'':unit)));f.append(metric);
      }
      facts.append(f);
      const context=el('p','future-context',data.city_context||'');facts.append(context);
      if(profile.api_url){const a=el('a','future-source','Fonte: IBGE — Censo 2022 (tabela 4714) ↗');a.href=profile.api_url;a.target='_blank';a.rel='noopener noreferrer';facts.append(a);}
    }else{
      facts.append(el('p','future-no-data','Dados do Censo 2022 indisponíveis nesta consulta. O cenário a seguir é genérico e NÃO descreve dados particulares desta cidade.'));
      if(profile.source_url){const a=el('a','future-source','Consultar tabela 4714 do IBGE ↗');a.href=profile.source_url;a.target='_blank';a.rel='noopener noreferrer';facts.append(a);}
    }
    const box=$('#futureThemes');box.replaceChildren();
    for(const theme of data.themes){
      const div=el('div','future-theme');div.append(el('strong','',theme.name),el('span','',theme.text));box.append(div);
    }
    message('Cenário hipotético atualizado. Não representa uma previsão.');
  }catch(e){if(requestId===futureRequestSequence)message(e.message);}
}
function modal(which,open){
  $('#'+which).hidden=!open;
  if(open){if(which==='contributionModal')$('#placeNameInput').placeholder='Ex.: praça, rua, edifício';}
}

function updatePhotoRights(){
  const form=$('#contributionForm');
  const hasPhoto=Boolean($('#photoInput').files.length);
  const basis=form.querySelector('input[name="rights_basis"]:checked')?.value||'';
  const needsEvidence=hasPhoto && ['permission','open','public_domain'].includes(basis);
  const open=hasPhoto && basis==='open';
  $('#photoRights').hidden=!hasPhoto;
  $('#rightsExtra').hidden=!needsEvidence;
  $('#openLicenseBox').hidden=!open;
  $('#rightsWarning').hidden=!(hasPhoto && basis==='unsure');
  $('#rightsReference').required=needsEvidence;
  $('#openLicense').required=open;
  $('#rightsReferenceLabel').textContent=basis==='permission'
      ?'Quem autorizou e como você recebeu a permissão? *'
      :basis==='public_domain'
      ?'Onde está documentado que a foto é de domínio público? *'
      :'Qual é o link original da imagem e sua licença? *';
  const requiredRadio=form.querySelector('input[name="rights_basis"]');
  requiredRadio.required=hasPhoto;
  $('#contributionLicense').value=!hasPhoto?'Relato autorizado'
      :basis==='public_domain'?'Domínio público'
      :basis==='open'?$('#openLicense').value
      :'Autorizo exibição no AEVIA';
}

function setupContribution(){
  $('#photoInput').addEventListener('change',updatePhotoRights);
  for(const radio of document.querySelectorAll('input[name=rights_basis]')) radio.addEventListener('change',updatePhotoRights);
  $('#openLicense').addEventListener('change',updatePhotoRights);
  updatePhotoRights();
  $('#openContribution').onclick=()=>{
    if(state.contributionsEnabled===false){
      $('#betaContributionNotice').hidden=false;
      $('#betaContributionNotice').scrollIntoView({behavior:'smooth',block:'center'});
      message('Os envios serão abertos em uma etapa posterior do AEVIA Beta.');
      return;
    }
    if(!state.pointValid){message('Marque primeiro um ponto desta cidade no mapa.');return;}
    modal('contributionModal',true);
  };
  $('#contributionForm').addEventListener('submit',async ev=>{
    ev.preventDefault();const form=ev.currentTarget,btn=form.querySelector('button[type=submit]');
    const payload=new FormData(form);
    payload.set('city_id',String(state.city.id));payload.set('city_name',state.city.name);
    payload.set('latitude',String(state.lat));payload.set('longitude',String(state.lon));
    payload.set('consent',String(form.elements.consent.checked));
    payload.set('ai_consent',String(form.elements.ai_consent.checked));
    const image=form.elements.image.files[0];
    if(image&&image.size>8*1024*1024){message('Imagem excede 8 MB.');return;}
    if(image && !form.querySelector('input[name=rights_basis]:checked')){message('Indique como você tem permissão para publicar a fotografia.');return;}
    if(image && form.querySelector('input[name=rights_basis]:checked')?.value==='unsure'){message('Remova a foto ou obtenha autorização antes de enviar.');$('#rightsWarning').hidden=false;return;}
    updatePhotoRights();
    btn.disabled=true;$('#contributionMessage').textContent='Enviando para revisão...';
    try{
      const data=await api('/api/contribuicoes',{method:'POST',body:payload});
      $('#contributionMessage').textContent=`Enviado! Protocolo: ${data.id.slice(0,12)}. Pendente de revisão.`;
      $('#contributionMessage').className='form-message success';
      form.reset();updatePhotoRights();message('Contribuição recebida para revisão humana.');
    }catch(e){$('#contributionMessage').textContent=e.message;$('#contributionMessage').className='form-message';}
    finally{btn.disabled=false;}
  });
}
async function refreshQueue(){
  const queue=$('#adminQueue');queue.replaceChildren(el('p','','Carregando pendências...'));
  try{
    const data=await api('/api/admin/contribuicoes?status='+encodeURIComponent($('#queueStatus').value));queue.replaceChildren();
    if(!data.items.length){queue.append(el('p','','Nenhuma contribuição pendente.'));return;}
    for(const item of data.items){
      const card=el('div','admin-card');
      card.append(el('strong','',`${item.title} · ${item.city_name}`),
                  el('div','',`Lugar: ${item.place_name} · Ano: ${item.historic_year||'não informado'}`),
                  el('p','',item.story),
                  el('p','',`Fonte: ${item.source_reference||'não apresentada'}`),
                  el('p','',`Direitos da foto: ${item.rights_basis||'registro anterior'} · Comprovação: ${item.rights_reference||'não apresentada'}`),
                  el('small','',`Consentimento para IA: ${item.ai_consent?'sim':'não'} · ${item.ai_status}`));
      if(item.image){const img=el('img');img.src=item.image;img.alt='Imagem recebida e não publicada';card.append(img);}
      if(item.ai_report)card.append(el('p','',`Triagem: ${item.ai_report.slice(0,700)}`));
      const controls=el('div','admin-buttons');
      for(const [text,status] of [['Aprovar','aprovada'],['Rejeitar','rejeitada']]){
        const button=el('button','',text);button.onclick=async()=>{
          const note=window.prompt('Observação da revisão (opcional):','');if(note===null)return;
          try{await api(`/api/admin/contribuicoes/${item.id}/revisar`,{
            method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({status,note})});
            message(`Registro ${status}.`);refreshQueue();}catch(e){message(e.message);}
        };controls.append(button);
      }
      if(item.ai_consent){
        const aiBtn=el('button','','Triagem por IA (opcional)');aiBtn.onclick=async()=>{
          aiBtn.disabled=true;
          try{const r=await api(`/api/admin/contribuicoes/${item.id}/ia`,{method:'POST'});
            message('Triagem registrada, revisão humana continua necessária.');
            card.append(el('p','',JSON.stringify(r.report).slice(0,1200)));
          }catch(e){message(e.message);}finally{aiBtn.disabled=false;}
        };controls.append(aiBtn);
      }
      const del=el('button','','Excluir definitivamente');del.type='button';
      del.onclick=async()=>{
        if(!window.confirm('Excluir este registro e sua fotografia do banco de dados? Essa ação é irreversível.'))return;
        try{await api(`/api/admin/contribuicoes/${item.id}`,{method:'DELETE'});message('Contribuição excluída.');refreshQueue();}
        catch(e){message(e.message);}
      };controls.append(del);
      card.append(controls);queue.append(card);
    }
  }catch(e){queue.replaceChildren(el('p','',e.message));}
}
function setupAdmin(){
  $('#openAdmin').onclick=()=>{
    modal('adminModal',true);
    if(!state.adminConfigured)$('#adminMessage').textContent='A administração ainda não foi configurada. Execute configurar_administrador.bat na pasta do AEVIA e reinicie o servidor.';
  };
  $('#adminLoginForm').onsubmit=async e=>{
    e.preventDefault();try{
      await api('/api/admin/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({password:$('#adminPassword').value})});
      $('#adminPassword').value='';$('#adminLoginForm').hidden=true;$('#adminActions').hidden=false;
      $('#adminMessage').textContent='Administrador autenticado.';await refreshQueue();
    }catch(error){$('#adminMessage').textContent=error.message;}
  };
  $('#refreshQueue').onclick=refreshQueue;
  $('#queueStatus').onchange=refreshQueue;
  $('#syncMunicipios').onclick=async()=>{
    const button=$('#syncMunicipios');button.disabled=true;$('#adminMessage').textContent='Sincronizando fontes nacionais...';
    try{const result=await api('/api/admin/sincronizar-municipios',{method:'POST'});
      $('#adminMessage').textContent=`Catálogo sincronizado: ${result.total} municípios. Coordenadas encontradas para ${result.coordinates_available}.`;
      $('#municipioTotal').textContent=result.total.toLocaleString('pt-BR');
    }catch(e){$('#adminMessage').textContent=e.message;}finally{button.disabled=false;}
  };
  $('#adminLogout').onclick=async()=>{await api('/api/admin/logout',{method:'POST'});$('#adminLoginForm').hidden=false;$('#adminActions').hidden=true;};
}
async function share(){
  const data={title:'AEVIA — O tempo mora em cada lugar',text:'Conheça a memória das cidades brasileiras.',url:window.location.href};
  if(navigator.share){try{await navigator.share(data);return;}catch{}}
  try{await navigator.clipboard.writeText(data.url);message('Link copiado.');}
  catch{message('Copie o endereço da barra do navegador para compartilhar.');}
}
async function locateAddress(){
  if(!await ensureCitySelected())return;
  const cityId=state.city.id;
  const q=fmt($('#addressSearch').value);if(q.length<3){message('Digite pelo menos 3 caracteres.');return;}
  const results=$('#addressResults');results.replaceChildren(el('p','field-help','Localizando...'));
  try{
    const data=await api(`/api/enderecos?q=${encodeURIComponent(q)}&city_id=${cityId}`);
    if(cityId!==state.city.id)return;
    results.replaceChildren();
    if(!data.configured){results.append(el('p','field-help','Busca por endereço temporariamente indisponível. Marque o ponto no mapa.'));return;}
    if(!data.results.length)results.append(el('p','field-help','Nenhum endereço encontrado.'));
    for(const location of data.results){
      const b=el('button','',location.label);b.type='button';b.onclick=()=>{
        if(!setPoint(location.lat,location.lon,false))return;
        $('#addressSearch').value=location.label;results.replaceChildren();$('#selectedPoint').textContent='• ENDEREÇO SELECIONADO';
      };results.append(b);
    }
  }catch(e){results.replaceChildren(el('p','field-help',e.message));}
}
async function initial(){
  $('#yearSlider').max=String(Math.max(2026,new Date().getFullYear()));
  $('#yearSlider').value=String(Math.max(2026,new Date().getFullYear()));
  state.selectedYear=Number($('#yearSlider').value);$('#yearDisplay').textContent=String(state.selectedYear);
  $('#timelineCurrentYear').textContent=String(state.selectedYear);
  initMap();setPoint(state.lat,state.lon);
  $('#citySearch').addEventListener('input',()=>{
    ++citySearchSequence;
    clearTimeout(searchTimer);
    if(cityInputIsCurrent()){
      $('#cityName').textContent=`${state.city.name} — ${state.city.uf}`;
      $('#coordsInfo').textContent=state.pointValid?`${state.lat.toFixed(4)}, ${state.lon.toFixed(4)}`:'Marque um ponto no mapa.';
      $('#cityHint').textContent=`Município ${state.city.id} selecionado.`;
      $('#cityHint').className='field-help success-selection';
      $('#loadArchive').disabled=false;$('#addressGo').disabled=false;$('#generate2050').disabled=false;
      $('#cityResults').hidden=true;
      return;
    }
    markCityInputPending();
    searchTimer=setTimeout(searchCity,320);
  });
  $('#citySearch').addEventListener('keydown',ev=>{
    if(ev.key==='Enter'){ev.preventDefault();clearTimeout(searchTimer);selectTypedCity();}
    if(ev.key==='Escape')$('#cityResults').hidden=true;
    if(ev.key==='ArrowDown' && !$('#cityResults').hidden){
      const first=$('#cityResults button');if(first){ev.preventDefault();first.focus();}
    }
  });
  $('#cityResults').addEventListener('keydown',ev=>{
    if(ev.key==='ArrowDown'||ev.key==='ArrowUp'){
      const options=[...$('#cityResults').querySelectorAll('button')];
      const at=options.indexOf(document.activeElement);
      if(options.length){ev.preventDefault();options[(at+(ev.key==='ArrowDown'?1:options.length-1))%options.length].focus();}
    }
    if(ev.key==='Escape'){$('#cityResults').hidden=true;$('#citySearch').focus();}
  });
  $('#cityGo').addEventListener('click',()=>{clearTimeout(searchTimer);selectTypedCity();});
  $('#citySearch').addEventListener('blur',()=>setTimeout(()=>{$('#cityResults').hidden=true;},200));
  $('#yearSlider').addEventListener('input',ev=>{state.selectedYear=Number(ev.target.value);$('#yearDisplay').textContent=String(state.selectedYear);});
  $('#loadArchive').onclick=loadArchive;
  $('#addressGo').onclick=locateAddress;
  $('#addressSearch').addEventListener('keydown',ev=>{if(ev.key==='Enter'){ev.preventDefault();locateAddress();}});
  $('#resetMap').onclick=()=>{if(state.city.latitude!=null)setPoint(state.city.latitude,state.city.longitude,false);};
  for(const side of ['A','B'])$('#compare'+side).onchange=ev=>{state.compare[side.toLowerCase()]=ev.target.value;paintCompare(side.toLowerCase());};
  for(const [input,output] of [['greenSlider','greenVal'],['mobSlider','mobVal'],['heritageSlider','heritageVal']]){
    $('#'+input).oninput=ev=>$('#'+output).textContent=ev.target.value+'%';
  }
  $('#generate2050').onclick=show2050;
  setupContribution();setupAdmin();
  for(const button of document.querySelectorAll('[data-close]'))button.onclick=()=>modal(button.dataset.close,false);
  for(const back of document.querySelectorAll('.modal-backdrop'))back.addEventListener('click',ev=>{if(ev.target===back)modal(back.id,false);});
  document.addEventListener('keydown',ev=>{if(ev.key==='Escape')for(const back of document.querySelectorAll('.modal-backdrop'))back.hidden=true;});
  $('#navShare').onclick=share;$('#footerShare').onclick=share;
  try{
    const status=await api('/api/status');
    $('#municipioTotal').textContent=status.municipalities.toLocaleString('pt-BR');
    state.adminConfigured=status.admin_configured;
    state.contributionsEnabled=status.public_contributions_enabled;
    if(status.public_contributions_enabled===false){
      $('#openContribution').textContent='Envio de memórias: em breve';
      $('#betaContributionNotice').hidden=false;
      $('#openAdmin').hidden=true;
      document.querySelector('#siteParticipationHint')?.removeAttribute('hidden');
    }
    if(status.version!=='1.7.0'){
      $('#releaseBadge').textContent='VERSÃO DO SERVIDOR DIFERENTE';
      $('#releaseBadge').classList.add('release-warning');
      message('Versões diferentes detectadas. Feche o servidor antigo e abra o iniciador novo.');
    }
    if(!status.city_catalog_complete)$('#cityHint').textContent='Catálogo parcial. Sincronize o IBGE no painel de administração para cobertura nacional.';
    const city=await api('/api/municipio/3115300');chooseCity(city);
  }catch(e){message(e.message);}
}
document.addEventListener('DOMContentLoaded',initial);
