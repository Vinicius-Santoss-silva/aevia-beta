"""Fontes públicas: IBGE, coordenadas comunitárias, Wikimedia Commons e Geoapify (opcional)."""
import csv
import html
import io
import json
import os
import re
import time
import threading
import unicodedata
from urllib.parse import quote
import httpx
from .db import database

IBGE = 'https://servicodados.ibge.gov.br/api/v1/localidades/municipios'
NOMINATIM = 'https://nominatim.openstreetmap.org/search'
NOMINATIM_LOCK = threading.Lock()
LAST_NOMINATIM_CALL = [0.0]
COORDS_CSV = 'https://raw.githubusercontent.com/kelvins/Municipios-Brasileiros/main/csv/municipios.csv'
COMMONS = 'https://commons.wikimedia.org/w/api.php'
USER_AGENT = 'AEVIA/1.7 (acervo historico educativo; ' + (os.getenv('AEVIA_CONTACT_EMAIL') or os.getenv('PUBLIC_URL') or os.getenv('RENDER_EXTERNAL_URL') or 'http://localhost:8017') + ')' 
UF = {11:'RO',12:'AC',13:'AM',14:'RR',15:'PA',16:'AP',17:'TO',21:'MA',22:'PI',23:'CE',24:'RN',25:'PB',26:'PE',27:'AL',28:'SE',29:'BA',31:'MG',32:'ES',33:'RJ',35:'SP',41:'PR',42:'SC',43:'RS',50:'MS',51:'MT',52:'GO',53:'DF'}
FALLBACK = [
(3115300,'Cataguases','MG',-21.3892,-42.6963),(3146107,'Ouro Preto','MG',-20.3855,-43.5034),
(3140001,'Mariana','MG',-20.3777,-43.4168),(3106200,'Belo Horizonte','MG',-19.9167,-43.9345),
(3304557,'Rio de Janeiro','RJ',-22.9068,-43.1729),(3550308,'São Paulo','SP',-23.5505,-46.6333),
(2927408,'Salvador','BA',-12.9777,-38.5016),(5300108,'Brasília','DF',-15.7939,-47.8828),
(4106902,'Curitiba','PR',-25.4284,-49.2733),(4314902,'Porto Alegre','RS',-30.0346,-51.2177),
(2611606,'Recife','PE',-8.0476,-34.8770),(2304400,'Fortaleza','CE',-3.7319,-38.5267),
(3106705,'Betim','MG',-19.9668,-44.1985),(3118601,'Contagem','MG',-19.9319,-44.0539),
(3136702,'Juiz de Fora','MG',-21.7609,-43.3503),(3169901,'Ubá','MG',-21.1203,-42.9426),
]


def valid_brazil_coords(lat, lon):
    """Limites amplos do Brasil; validação preliminar contra coordenadas absurdas."""
    try:
        a, b = float(lat), float(lon)
        return -35 <= a <= 6 and -75 <= b <= -30
    except (TypeError, ValueError):
        return False


def clean_city_coords(city):
    """Nunca mostrar coordenadas inválidas; recuperar locais-piloto conhecidos."""
    city = dict(city)
    if not valid_brazil_coords(city.get('latitude'),city.get('longitude')):
        fallback = next((x for x in FALLBACK if x[0] == city['id']), None)
        city['latitude'],city['longitude'] = (fallback[3],fallback[4]) if fallback else (None,None)
    return city


def normalize(value):
    raw = unicodedata.normalize('NFKD', str(value))
    return ''.join(c for c in raw if not unicodedata.combining(c)).casefold().strip()


def http_get(url, params=None, timeout=17):
    with httpx.Client(timeout=timeout, follow_redirects=True, headers={'User-Agent':USER_AGENT, 'Accept':'application/json, text/csv;q=0.9'}) as client:
        response = client.get(url, params=params)
        response.raise_for_status()
        return response


def seed():
    with database() as db:
        db.executemany('INSERT OR IGNORE INTO municipalities VALUES (?,?,?,?,?,?)',
                       [(i,n,uf,lat,lon,normalize(n)) for i,n,uf,lat,lon in FALLBACK])


def count_municipalities():
    with database() as db:
        return db.execute('SELECT count(*) FROM municipalities').fetchone()[0]


def sync_municipalities():
    """Carrega catálogo oficial de municípios e coordenadas aproximadas (não endereços)."""
    coord_map = {}
    try:
        csvtext = http_get(COORDS_CSV, timeout=25).text
        for row in csv.DictReader(io.StringIO(csvtext)):
            try:
                code=int(row['codigo_ibge'])
                lat,lon=float(row['latitude']),float(row['longitude'])
                if valid_brazil_coords(lat,lon): coord_map[code]=(lat,lon)
            except (ValueError, KeyError): continue
    except (httpx.HTTPError, ValueError):
        pass  # Sem coordenadas: catálogo oficial ainda é útil.
    raw = http_get(IBGE, timeout=30).json()
    # Se a fonte auxiliar de coordenadas falhar, preservar georreferências previamente importadas.
    with database() as db:
        prior = {r['id']: (r['latitude'],r['longitude'])
                 for r in db.execute('SELECT id,latitude,longitude FROM municipalities').fetchall()}
    items = []
    for city in raw:
        code = int(city['id'])
        region = city.get('regiao-imediata') or {}
        immediate = region.get('regiao-intermediaria') or {}
        state = immediate.get('UF') or {}
        if not state:
            micro = city.get('microrregiao') or {}
            state = ((micro.get('mesorregiao') or {}).get('UF') or {})
        uf = state.get('sigla') or UF.get(code//100000, '')
        lat, lon = coord_map.get(code, (None, None))
        if not valid_brazil_coords(lat,lon):
            previous = prior.get(code, (None,None))
            lat,lon=previous if valid_brazil_coords(*previous) else (None,None)
        if code in {x[0] for x in FALLBACK} and lat is None:
            row = next(x for x in FALLBACK if x[0]==code)
            lat, lon = row[3],row[4]
        items.append((code,city['nome'],uf,lat,lon,normalize(city['nome'])))
    if len(items) < 5000:
        raise ValueError('Resposta de municípios incompleta; catálogo anterior foi preservado')
    with database() as db:
        db.executemany('INSERT OR REPLACE INTO municipalities VALUES (?,?,?,?,?,?)',items)
    return len(items), sum(1 for row in items if valid_brazil_coords(row[3],row[4]))


def search_municipalities(q='', limit=30):
    key=normalize(q)
    with database() as db:
        rows=db.execute('SELECT id,name,uf,latitude,longitude FROM municipalities WHERE search_key LIKE ? OR uf LIKE ? ORDER BY CASE WHEN search_key = ? THEN 0 WHEN search_key LIKE ? THEN 1 ELSE 2 END,name LIMIT ?',
            ('%'+key+'%',key.upper(),key,key+'%',min(limit,50))).fetchall()
        return [clean_city_coords(r) for r in rows]


def get_city(city_id):
    with database() as db:
        row=db.execute('SELECT id,name,uf,latitude,longitude FROM municipalities WHERE id=?',(city_id,)).fetchone()
        return clean_city_coords(row) if row else None


def cached(key, fetch, ttl_seconds=43200):
    now=int(time.time())
    with database() as db:
        row=db.execute('SELECT body FROM cache WHERE cache_key=? AND expires_at>?',(key,now)).fetchone()
    if row: return json.loads(row['body'])
    value=fetch()
    with database() as db:
        db.execute('INSERT OR REPLACE INTO cache (cache_key,body,expires_at) VALUES (?,?,?)',(key,json.dumps(value,ensure_ascii=False),now+ttl_seconds))
    return value


def text_only(raw):
    txt=re.sub(r'<[^>]*>', '', html.unescape(str(raw or '')))
    return re.sub(r'\s+',' ',txt).strip()[:600]


def from_ext(data, name):
    return text_only((data.get(name) or {}).get('value'))


def parse_commons_pages(pages,location_confidence,note):
    results=[]
    for page in pages:
        info=(page.get('imageinfo') or [{}])[0]
        if not info.get('mime','').startswith('image/') or info.get('mime')=='image/svg+xml': continue
        # Imagens espaciais do tipo "ISS038-E-... View of Earth" têm geotags
        # aproximadas, mas não representam fotografias da rua ou do município.
        filename=page.get('title','').removeprefix('File:').casefold()
        normalized_filename=re.sub(r'[_-]+',' ',filename)
        # Fotos orbitais podem conter geotag aproximada, mas não são registros de rua.
        if re.search(r'\biss\d{2,}\b',normalized_filename) or any(word in normalized_filename for word in (
            'view of earth','earth from space','international space station',
            'satellite image','satellite view','satellite imagery','orbital photograph')):
            continue
        md=info.get('extmetadata') or {}
        license_name=from_ext(md,'LicenseShortName') or 'Não identificada'
        license_url=from_ext(md,'LicenseUrl')
        original_year=from_ext(md,'DateTimeOriginal')  # Ano da foto, nunca inferir da data de upload.
        match=re.search(r'(?<!\d)(1[89]\d{2}|20\d{2})(?!\d)',original_year)
        year=int(match.group(0)) if match else None
        source=info.get('descriptionurl') or ''
        if not source.startswith('https://commons.wikimedia.org/'): continue
        results.append({'id':'commons-'+str(page.get('pageid')),'title':page.get('title','').removeprefix('File:').removeprefix('Ficheiro:'),
            'image':info.get('thumburl') or info.get('url'), 'year':year,'date_raw':original_year,
            'license':license_name,'license_url':license_url,'author':from_ext(md,'Artist'),
            'description':from_ext(md,'ImageDescription'), 'source_url':source,
            'kind':'commons','location_confidence':location_confidence,'note':note})
    return results


def commons_archive(lat,lon,radius=3000,limit=40):
    """Geotagged Commons; localização aproximada, data sempre atribuída à fonte."""
    if not (-35<=lat<=6 and -75<=lon<=-30):
        return []
    radius=max(100,min(int(radius),10000))
    cache_key=f'commons:{lat:.4f}:{lon:.4f}:{radius}:{limit}'
    def load():
        params={'action':'query','generator':'geosearch','ggscoord':f'{lat}|{lon}',
                'ggsradius':radius,'ggsnamespace':6,'ggsprimary':'all','ggslimit':min(limit,50),
                'prop':'imageinfo','iiprop':'url|size|mime|extmetadata','iiurlwidth':760,
                'format':'json','formatversion':2}
        data=http_get(COMMONS,params=params).json()
        return data.get('query',{}).get('pages',[])
    pages=cached(cache_key,load,43200)
    return parse_commons_pages(pages,'geotag_proximidade',
        'Foto georreferenciada próxima ao ponto; rua, data e enquadramento devem ser verificados.')


def commons_text_archive(name,uf):
    """Busca complementar por nome do município; resultados NÃO são geolocalizados."""
    city=normalize(name)
    if len(city)<3 or len(city)>100: return []
    cache_key=f'commons-text:{city}:{uf}'
    def load():
        params={'action':'query','generator':'search','gsrsearch':f'"{name}"',
                'gsrnamespace':6,'gsrlimit':25,'prop':'imageinfo',
                'iiprop':'url|size|mime|extmetadata','iiurlwidth':760,
                'format':'json','formatversion':2}
        return http_get(COMMONS,params=params).json().get('query',{}).get('pages',[])
    pages=cached(cache_key,load,43200)
    return parse_commons_pages(pages,'busca_textual_nao_geolocalizada',
        'Encontrada por texto relacionado à cidade; localização, época e assunto NÃO confirmados.')


def geocode_address(text, city=None):
    """Busca explícita, não autocomplete. Geoapify se configurado; Nominatim em baixo volume.

    A instância pública da Nominatim permite no máximo 1 pedido/s, cache obrigatório,
    identificação da aplicação e atribuição. Para alto tráfego use serviço contratado.
    """
    query = text[:140] + (', ' + city[:90] if city else '') + ', Brasil'
    key = os.getenv('GEOAPIFY_API_KEY', '').strip()
    if key:
        def load_geoapify():
            raw=http_get('https://api.geoapify.com/v1/geocode/search',
               {'text':query,'filter':'countrycode:br','lang':'pt','format':'json','limit':6,'apiKey':key}).json()
            out=[]
            for loc in raw.get('results',[]):
                lat,lon=loc.get('lat'),loc.get('lon')
                if not valid_brazil_coords(lat,lon): continue
                out.append({'label':loc.get('formatted',''), 'lat':float(lat),'lon':float(lon),'confidence':loc.get('rank',{}).get('confidence')})
            return out
        return {'configured':True,'provider':'Geoapify',
                'results':cached('geoapify:'+normalize(query),load_geoapify,604800)}

    # Desligar explicitamente em hospedagem com alto tráfego e sem geocodificador próprio.
    if os.getenv('ENABLE_PUBLIC_NOMINATIM','yes').lower() not in ('yes','true','1'):
        return {'configured':False,'provider':None,'results':[]}

    def load_nominatim():
        # Serializa e limita consultas no processo. Não suporta escalonamento multiworker.
        with NOMINATIM_LOCK:
            wait=1.1-(time.monotonic()-LAST_NOMINATIM_CALL[0])
            if wait>0:time.sleep(wait)
            LAST_NOMINATIM_CALL[0]=time.monotonic()
            rows=http_get(NOMINATIM,{
                'q':query,'format':'jsonv2','countrycodes':'br','addressdetails':1,
                'limit':6,'accept-language':'pt-BR'}, timeout=20).json()
        out=[]
        for loc in rows:
            lat,lon=loc.get('lat'),loc.get('lon')
            if not valid_brazil_coords(lat,lon):continue
            out.append({'label':loc.get('display_name','Localização aproximada'),
                        'lat':float(lat),'lon':float(lon), 'confidence':None})
        return out
    return {'configured':True,'provider':'OpenStreetMap Nominatim (uso limitado)',
            'results':cached('nominatim:'+normalize(query),load_nominatim,30*86400)}


IBGE_CENSUS_2022 = 'https://servicodados.ibge.gov.br/api/v3/agregados/4714/periodos/2022/variaveis/93%7C6318%7C614'

def parse_ibge_profile(payload, city_id):
    """Converte variáveis 93, 6318 e 614 do agregado 4714 do IBGE.

    Não infere números de chaves ausentes, e não mistura outras localidades.
    """
    def convert(value):
        if not isinstance(value,(str,int,float)) or str(value).strip() in ('','-','...','..','X','x'):
            return None
        try:
            number=float(str(value).strip().replace(',','.'))
            return number if 0 <= number < 1e12 else None
        except (ValueError, OverflowError):
            return None
    result={"year":2022,"population":None,"area_km2":None,"density_per_km2":None,
        "source_name":"IBGE — Censo Demográfico 2022, tabela SIDRA 4714",
        "source_url":f"https://sidra.ibge.gov.br/tabela/4714",
        "api_url":IBGE_CENSUS_2022+f"?localidades=N6%5B{int(city_id)}%5D"}
    mapping={'93':'population','6318':'area_km2','614':'density_per_km2'}
    if not isinstance(payload,list):return result
    for block in payload:
        var=str(block.get('id',''))
        if var not in mapping:continue
        for item in block.get('resultados',[]):
            for series in item.get('series',[]):
                if str((series.get('localidade') or {}).get('id'))!=str(city_id):continue
                series_data=series.get('serie') or {}
                value=convert(series_data.get('2022'))
                if value is not None:result[mapping[var]]=int(value) if var=='93' else round(value,2)
    return result


def get_ibge_profile(city_id):
    """Consulta oficial em cache (30 dias). Falha sem fabricar indicadores."""
    def load():
        response=http_get(IBGE_CENSUS_2022,
             {'localidades':f'N6[{int(city_id)}]'},timeout=8).json()
        return parse_ibge_profile(response,city_id)
    try:
        return cached(f'ibge-censo2022-4714:{int(city_id)}:v1',load,30*86400)
    except (httpx.HTTPError,ValueError,TypeError,KeyError,json.JSONDecodeError):
        return parse_ibge_profile(None,city_id)
