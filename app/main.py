import hashlib
import hmac
import json
import os
import re
import secrets
import time
import uuid
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated
from urllib.parse import urlparse

from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image, ImageOps, UnidentifiedImageError
import httpx

from .db import ROOT, database, initialize
from .sources import (seed, count_municipalities, search_municipalities, sync_municipalities,
                      get_city, commons_archive, commons_text_archive, geocode_address, get_ibge_profile)
from .moderation import basic_check, gemini_triage

STATIC=ROOT/'static'
STORAGE=Path(os.getenv('STORAGE_DIR',str(ROOT/'storage')))
UPLOADS=STORAGE/'uploads'
ADMIN_PASSWORD=os.getenv('ADMIN_PASSWORD','')
SESSION_SECRET=os.getenv('SESSION_SECRET','') or secrets.token_urlsafe(48)
PUBLIC_URL=os.getenv('PUBLIC_URL') or os.getenv('RENDER_EXTERNAL_URL') or 'http://localhost:8017'
DEPLOY_MODE=os.getenv('APP_ENV','development').lower()
BETA_MODE=DEPLOY_MODE=='beta'
PRODUCTION=DEPLOY_MODE in ('beta','production')
PUBLIC_CONTRIBUTIONS_ENABLED=(
    os.getenv('ENABLE_PUBLIC_CONTRIBUTIONS', 'no' if BETA_MODE else 'yes').lower() in ('yes','true','1')
)
CURRENT_YEAR=datetime.now(timezone.utc).year
MAX_UPLOAD=8*1024*1024
ALLOWED_LICENSES={'CC BY 4.0','CC BY-SA 4.0','Autorizo exibição no AEVIA','Domínio público','Relato autorizado'}
PHOTO_BASES={'owner','permission','open','public_domain'}
CLIENT_POSTS=defaultdict(deque)
ADMIN_ATTEMPTS=defaultdict(deque)

@asynccontextmanager
async def lifespan(application):
    if BETA_MODE:
        if PUBLIC_CONTRIBUTIONS_ENABLED:
            raise RuntimeError('Beta pública: contribuições devem ficar desativadas sem armazenamento persistente.')
        if not PUBLIC_URL.startswith('https://'):
            raise RuntimeError('Beta pública exige endereço HTTPS. Configure PUBLIC_URL ou RENDER_EXTERNAL_URL.')
        if not os.getenv('GEOAPIFY_API_KEY') and os.getenv('ENABLE_PUBLIC_NOMINATIM','no').lower() in ('yes','true','1'):
            raise RuntimeError('Beta pública sem chave: desative Nominatim com ENABLE_PUBLIC_NOMINATIM=no.')
    elif PRODUCTION:
        if len(ADMIN_PASSWORD)<16 or len(os.getenv('SESSION_SECRET',''))<32:
            raise RuntimeError('Produção exige ADMIN_PASSWORD (16+ caracteres) e SESSION_SECRET (32+ caracteres).')
        if not PUBLIC_URL.startswith('https://'):
            raise RuntimeError('Produção exige PUBLIC_URL com HTTPS.')
        if os.getenv('PERSISTENT_STORAGE_CONFIRMED')!='yes':
            raise RuntimeError('Produção bloqueada: configure DB_PATH/STORAGE_DIR persistentes, backups, e confirme PERSISTENT_STORAGE_CONFIRMED=yes.')
        if os.getenv('LEGAL_REVIEW_CONFIRMED')!='yes':
            raise RuntimeError('Produção bloqueada: revisão das licenças/privacidade ainda não confirmada.')
        if os.getenv('LIVE_TESTS_CONFIRMED')!='yes':
            raise RuntimeError('Produção bloqueada: validação final das integrações ainda não confirmada.')
        if os.getenv('ENABLE_PUBLIC_NOMINATIM','yes').lower() in ('yes','true','1') and not os.getenv('GEOAPIFY_API_KEY'):
            raise RuntimeError('Produção bloqueada: configure serviço próprio/de cota para busca de ruas ou use ENABLE_PUBLIC_NOMINATIM=no.')
    initialize()
    seed()
    if DEPLOY_MODE=='production' and count_municipalities()<5500:
        raise RuntimeError('Produção bloqueada: catálogo nacional incompleto. Execute python -m app.sync_data com internet.')
    UPLOADS.mkdir(parents=True,exist_ok=True)
    yield

app=FastAPI(title='AEVIA — memória das cidades', version='1.7.0', docs_url='/docs' if not PRODUCTION else None, lifespan=lifespan)

@app.middleware('http')
async def headers_and_origin(request:Request, call_next):
    if request.method=='POST' and request.url.path=='/api/contribuicoes' and not PUBLIC_CONTRIBUTIONS_ENABLED:
        return JSONResponse({'detail':'O envio de fotografias e relatos está temporariamente fechado no AEVIA Beta. Não recebemos arquivos nesta fase.'},status_code=403)
    if request.method in ('POST','PUT','PATCH','DELETE'):
        origin=request.headers.get('origin')
        if origin:
            host=urlparse(origin).netloc
            valid={request.headers.get('host',''),urlparse(PUBLIC_URL).netloc}
            if host not in valid:
                return JSONResponse({'detail':'Origem não autorizada.'},status_code=403)
    result=await call_next(request)
    result.headers['X-Content-Type-Options']='nosniff'
    result.headers['X-AEVIA-Version']='1.7.0'
    if request.url.path=='/' or request.url.path in ('/static/app.js','/static/style.css'):
        result.headers['Cache-Control']='no-store, no-cache, must-revalidate'
        result.headers['Pragma']='no-cache'
    result.headers['Referrer-Policy']='strict-origin-when-cross-origin'
    result.headers['X-Frame-Options']='DENY'
    result.headers['Permissions-Policy']='camera=(), microphone=(), geolocation=()'
    # Leaflet, OSM tiles, Commons thumbnails, Google Fonts (opcional) e CSS inline do leaflet.
    result.headers['Content-Security-Policy']=(
        "default-src 'self'; script-src 'self' https://unpkg.com; "
        "style-src 'self' 'unsafe-inline' https://unpkg.com https://fonts.googleapis.com; "
        "img-src 'self' data: blob: https://*.wikimedia.org https://tile.openstreetmap.org https://*.tile.openstreetmap.org https://unpkg.com; "
        "font-src 'self' https://fonts.gstatic.com; connect-src 'self'; object-src 'none'; "
        "frame-ancestors 'none'; base-uri 'self'; form-action 'self'")
    return result


def fail(message, status=400):
    raise HTTPException(status_code=status, detail=message)


def sign_token(exp):
    part=str(exp)
    digest=hmac.new(SESSION_SECRET.encode(),part.encode(),'sha256').hexdigest()
    return f'{part}.{digest}'


def is_admin(request):
    if not ADMIN_PASSWORD: return False
    value=request.cookies.get('aevia_admin','')
    try:
        part,digest=value.split('.',1)
        return int(part)>time.time() and hmac.compare_digest(sign_token(int(part)).split('.')[1],digest)
    except (ValueError,IndexError): return False


def admin_or_401(request):
    if not is_admin(request): fail('Administrador não autenticado.',401)


def check_rate(request):
    # Limitador local básico; usar proxy/rate limit distribuído na publicação nacional.
    ip=request.client.host if request.client else 'unknown'
    now=time.monotonic()
    calls=CLIENT_POSTS[ip]
    while calls and now-calls[0]>600: calls.popleft()
    if len(calls)>=3: fail('Limite de 3 contribuições por 10 minutos neste acesso.',429)
    calls.append(now)


@app.get('/healthz')
def health():
    return {'status':'ok'}


@app.get('/api/status')
def status():
    return {'project':'AEVIA','version':'1.7.0','release_channel':'beta' if BETA_MODE else DEPLOY_MODE,
            'public_contributions_enabled':PUBLIC_CONTRIBUTIONS_ENABLED,'municipalities':count_municipalities(),
            'city_catalog_complete':count_municipalities()>=5500,
            'geocoding_configured':bool(os.getenv('GEOAPIFY_API_KEY')) or (not BETA_MODE and os.getenv('ENABLE_PUBLIC_NOMINATIM','yes').lower() in ('yes','true','1')),
            'ai_configured':bool(os.getenv('GEMINI_API_KEY')),
            'admin_configured':bool(ADMIN_PASSWORD),
            'disclaimer':'Fotos históricas dependem das fontes, localidades e licenças.'}

@app.get('/api/municipios')
def municipios(q:str='',limit:int=25):
    if len(q)>120: fail('Pesquisa muito longa.')
    return {'results':search_municipalities(q,min(limit,50)), 'total_catalog':count_municipalities()}

@app.post('/api/admin/sincronizar-municipios')
def synchronize(request:Request):
    admin_or_401(request)
    try: num,coordinates=sync_municipalities()
    except (httpx.HTTPError,ValueError,KeyError) as exc: fail(f'Não foi possível sincronizar: {type(exc).__name__}',503)
    return {'total':num,'coordinates_available':coordinates}

@app.get('/api/municipio/{municipality_id}')
def municipality(municipality_id:int):
    city=get_city(municipality_id)
    if not city: fail('Município não encontrado no catálogo local.',404)
    return city

@app.get('/api/enderecos')
def addresses(q:str,city:str='',city_id:int|None=None):
    if not 3<=len(q.strip())<=140: fail('Digite ao menos três caracteres no endereço.')
    if city_id is not None:
        selected = get_city(city_id)
        if not selected: fail('Selecione um município válido antes de buscar uma rua.',404)
        city = f"{selected['name']}, {selected['uf']}"
    if BETA_MODE and not os.getenv('GEOAPIFY_API_KEY'):
        return {'configured':False,'results':[]}
    try: return geocode_address(q,city)
    except (httpx.HTTPError,ValueError,TypeError): fail('Serviço de geocodificação indisponível.',503)

@app.get('/api/acervo')
def archive(lat:float,lon:float,radius:int=3000,year:int=CURRENT_YEAR,city_id:int|None=None):
    if not -90<=lat<=90 or not -180<=lon<=180: fail('Coordenadas inválidas.')
    if year<1800 or year>max(CURRENT_YEAR,2050): fail('Ano fora do intervalo permitido.')
    try:
        images=commons_archive(lat,lon,radius)
        city=get_city(city_id) if city_id else None
        if city and len(images)<8:
            by_name=commons_text_archive(city['name'],city['uf'])
            known_ids={i['id'] for i in images}
            images.extend(i for i in by_name if i['id'] not in known_ids)
    except (httpx.HTTPError,ValueError) as exc: fail(f'Não foi possível consultar o Wikimedia Commons ({type(exc).__name__}).',503)
    dated=[i for i in images if i['year'] is not None and i['year']<=year]
    undated=[i for i in images if i['year'] is None]
    return {'items':dated,'undated':undated,'found':len(images),'year_filter':year,
            'notes':['As datas são extraídas dos metadados da fonte e podem conter erros.',
                     'Proximidade geográfica não garante a correspondência exata com uma rua.']}

@app.get('/api/contribuicoes')
def contributions(city_id:int|None=None,lat:float|None=None,lon:float|None=None):
    with database() as db:
        rows=db.execute('SELECT id,city_id,city_name,latitude,longitude,place_name,historic_year,title,story,author_name,license,rights_basis,source_reference,image_file,created_at FROM contributions WHERE status=? AND (? IS NULL OR city_id=?) ORDER BY created_at DESC LIMIT 100',
                        ('aprovada',city_id,city_id)).fetchall()
    items=[]
    for row in rows:
        item=dict(row)
        item['image']='/media/'+row['image_file'] if row['image_file'] else None
        item.pop('image_file')
        if lat is not None and lon is not None and (abs(lat-item['latitude'])>1 or abs(lon-item['longitude'])>1):
            continue
        item['kind']='contribuicao'
        item['location_confidence']='declarado_por_colaborador'
        items.append(item)
    return {'items':items}

@app.get('/media/{file_name}')
def approved_image(file_name:str):
    if not re.fullmatch(r'[0-9a-f]{32}\.jpg',file_name): fail('Arquivo não encontrado.',404)
    with database() as db:
        row=db.execute('SELECT id FROM contributions WHERE image_file=? AND status=?',(file_name,'aprovada')).fetchone()
    if not row: fail('Arquivo não publicado.',404)
    path=UPLOADS/file_name
    if not path.is_file(): fail('Arquivo indisponível.',404)
    return FileResponse(path,media_type='image/jpeg',headers={'Cache-Control':'public, max-age=3600'})

@app.post('/api/contribuicoes',status_code=201)
async def new_contribution(request:Request,city_id:Annotated[int,Form()],city_name:Annotated[str,Form()],
    latitude:Annotated[float,Form()],longitude:Annotated[float,Form()],place_name:Annotated[str,Form()],
    title:Annotated[str,Form()],story:Annotated[str,Form()],author_name:Annotated[str,Form()],
    license:Annotated[str,Form()],source_reference:Annotated[str,Form()],consent:Annotated[bool,Form()],
    ai_consent:Annotated[bool,Form()]=False,historic_year:Annotated[str,Form()]='',
    rights_basis:Annotated[str,Form()]='', rights_reference:Annotated[str,Form()]='',
    image:UploadFile|None=File(default=None)):
    if not PUBLIC_CONTRIBUTIONS_ENABLED:
        fail('As contribuições estão desativadas nesta versão Beta.',403)
    if not consent: fail('É necessário aceitar os termos e declarar os direitos sobre o material.')
    if license not in ALLOWED_LICENSES: fail('Licença inválida.')
    if len(rights_reference)>500: fail('Comprovação de direitos excede o limite de 500 caracteres.')
    city=get_city(city_id)
    if not city: fail('Selecione município válido.',400)
    if not (-35<=latitude<=6 and -75<=longitude<=-30): fail('Localização deve estar no Brasil.')
    for value,maxlen,name in [(title,110,'título'),(story,2200,'relato'),(author_name,90,'nome'),
                              (place_name,150,'lugar'),(source_reference,500,'fonte')]:
        if len(value.strip())>maxlen: fail(f'Campo {name} excede o limite.')
    if len(title.strip())<5 or len(story.strip())<20 or len(author_name.strip())<2 or not place_name.strip():
        fail('Preencha o título, local, nome e um relato de ao menos 20 caracteres.')
    try: year=int(historic_year) if historic_year.strip() else None
    except ValueError: fail('Ano inválido.')
    if year is not None and not 1800<=year<=CURRENT_YEAR: fail('Ano fora do intervalo 1800 até o ano atual.')
    image_file=None
    image_hash=None
    filepath=None
    has_photo=bool(image and image.filename)
    if has_photo:
        if rights_basis not in PHOTO_BASES:
            fail('Informe como você tem direitos para compartilhar a fotografia.')
        if rights_basis in ('owner','permission') and license!='Autorizo exibição no AEVIA':
            fail('Para autorização particular, escolha somente exibição no AEVIA.')
        if rights_basis=='open' and license not in ('CC BY 4.0','CC BY-SA 4.0'):
            fail('Informe a licença aberta corretamente.')
        if rights_basis=='public_domain' and license!='Domínio público':
            fail('Indique a situação de domínio público.')
        if rights_basis in ('permission','open','public_domain') and len(rights_reference.strip())<8:
            fail('Informe quem autorizou ou a fonte que comprova os direitos da fotografia.')
    else:
        if rights_basis or license!='Relato autorizado':
            fail('Sem fotografia, envie apenas o relato autorizado.')
        rights_basis='story'
        rights_reference=''
    if has_photo:
        raw=await image.read(MAX_UPLOAD+1)
        if len(raw)>MAX_UPLOAD: fail('Limite de imagem: 8 MB.',413)
        if not raw: fail('Imagem vazia.')
        image_hash=hashlib.sha256(raw).hexdigest()
        with database() as db:
            dup=db.execute('SELECT id FROM contributions WHERE image_hash=?',(image_hash,)).fetchone()
            if dup: fail('Esta imagem já foi enviada para revisão.',409)
        try:
            import io
            with Image.open(io.BytesIO(raw)) as im:
                im.verify()
            with Image.open(io.BytesIO(raw)) as im:
                if im.width*im.height>35_000_000: fail('Dimensões da imagem muito grandes.')
                im=ImageOps.exif_transpose(im).convert('RGB')
                im.thumbnail((1800,1800))
                image_file=uuid.uuid4().hex+'.jpg'
                filepath=UPLOADS/image_file
                im.save(filepath,'JPEG',quality=85,optimize=True)
        except (UnidentifiedImageError,OSError,ValueError,Image.DecompressionBombError):
            fail('Arquivo inválido: envie imagem JPG, PNG ou WebP.')
    check_rate(request)
    cid=uuid.uuid4().hex
    report=basic_check(filepath,year,source_reference)
    try:
        with database() as db:
            db.execute('''INSERT INTO contributions
                (id,created_at,city_id,city_name,latitude,longitude,place_name,historic_year,title,story,
                 author_name,license,rights_basis,rights_reference,source_reference,image_file,image_hash,consent,ai_consent,ai_status,ai_report)
                 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
              (cid,datetime.now(timezone.utc).isoformat(),city_id,f"{city['name']} — {city['uf']}",latitude,longitude,
               place_name.strip(),year,title.strip(),story.strip(),author_name.strip(),license,rights_basis,rights_reference.strip(),source_reference.strip(),
               image_file,image_hash,1,int(ai_consent),'nao_avaliada',json.dumps(report,ensure_ascii=False)))
    except Exception:
        if filepath and filepath.exists(): filepath.unlink()
        raise
    return {'id':cid,'status':'pendente','message':'Recebido para revisão humana. Não está publicado.'}

@app.post('/api/admin/login')
async def login(request:Request):
    ip=request.client.host if request.client else 'unknown'
    now=time.monotonic()
    attempts=ADMIN_ATTEMPTS[ip]
    while attempts and now-attempts[0]>900: attempts.popleft()
    if len(attempts)>=6: fail('Muitas tentativas de acesso. Aguarde 15 minutos.',429)
    if BETA_MODE: fail('Administração de contribuições desativada no Beta público.',403)
    if not ADMIN_PASSWORD: fail('Configure ADMIN_PASSWORD para ativar a moderação.',503)
    body=await request.json()
    password=str(body.get('password',''))
    if not hmac.compare_digest(password.encode(),ADMIN_PASSWORD.encode()):
        attempts.append(now)
        fail('Senha inválida.',401)
    attempts.clear()
    response=JSONResponse({'ok':True})
    response.set_cookie('aevia_admin',sign_token(int(time.time())+8*3600),httponly=True,secure=PRODUCTION,
                        samesite='strict',max_age=8*3600,path='/')
    return response

@app.post('/api/admin/logout')
def logout():
    response=JSONResponse({'ok':True})
    response.delete_cookie('aevia_admin',path='/')
    return response

@app.get('/api/admin/contribuicoes')
def review_queue(request:Request, status:str='pendente'):
    admin_or_401(request)
    if status not in ('pendente','aprovada','rejeitada'): fail('Status inválido.')
    with database() as db:
        rows=db.execute('SELECT * FROM contributions WHERE status=? ORDER BY created_at DESC LIMIT 200',(status,)).fetchall()
    return {'items':[{**dict(r),'image_file':None,'image':f'/api/admin/media/{r["id"]}' if r['image_file'] else None} for r in rows]}

@app.get('/api/admin/media/{contribution_id}')
def pending_media(contribution_id:str,request:Request):
    admin_or_401(request)
    with database() as db:
        row=db.execute('SELECT image_file FROM contributions WHERE id=?',(contribution_id,)).fetchone()
    if not row or not row['image_file']: fail('Imagem inexistente.',404)
    path=UPLOADS/row['image_file']
    if not path.is_file(): fail('Imagem não encontrada no armazenamento.',404)
    return FileResponse(path,media_type='image/jpeg',headers={'Cache-Control':'no-store'})

@app.post('/api/admin/contribuicoes/{contribution_id}/revisar')
async def review(contribution_id:str,request:Request):
    admin_or_401(request)
    payload=await request.json()
    status=payload.get('status')
    note=str(payload.get('note',''))[:500]
    if status not in ('aprovada','rejeitada','pendente'): fail('Status inválido.')
    with database() as db:
        cur=db.execute('UPDATE contributions SET status=?,reviewer_note=?,reviewed_at=? WHERE id=?',
            (status,note,datetime.now(timezone.utc).isoformat(),contribution_id))
        if cur.rowcount==0: fail('Contribuição não encontrada.',404)
    return {'ok':True,'status':status}

@app.delete('/api/admin/contribuicoes/{contribution_id}')
def delete_contribution(contribution_id:str, request:Request):
    """Exclusão definitiva na moderação; requer identificação e revisão de solicitação."""
    admin_or_401(request)
    with database() as db:
        row=db.execute('SELECT image_file FROM contributions WHERE id=?',(contribution_id,)).fetchone()
        if not row: fail('Contribuição não encontrada.',404)
        db.execute('DELETE FROM contributions WHERE id=?',(contribution_id,))
    if row['image_file']:
        (UPLOADS/row['image_file']).unlink(missing_ok=True)
    return {'ok':True,'deleted':contribution_id}


@app.post('/api/admin/contribuicoes/{contribution_id}/ia')
def run_ai(contribution_id:str,request:Request):
    admin_or_401(request)
    with database() as db:
        row=db.execute('SELECT * FROM contributions WHERE id=?',(contribution_id,)).fetchone()
    if not row: fail('Contribuição não encontrada.',404)
    if not row['ai_consent']: fail('Autor não autorizou o envio a provedor externo de IA.',403)
    try:
        report=gemini_triage(UPLOADS/row['image_file'] if row['image_file'] else None,
             row['title'],row['story'],row['city_name'],row['historic_year'])
    except RuntimeError as exc: fail(str(exc),503)
    except (httpx.HTTPError,ValueError,KeyError): fail('Serviço de IA indisponível; revisão humana permanece necessária.',503)
    with database() as db:
        db.execute('UPDATE contributions SET ai_status=?,ai_report=? WHERE id=?',
                   ('triada',json.dumps(report,ensure_ascii=False),contribution_id))
    return {'ai_status':'triada','report':report,'warning':'IA não prova local, ano ou autenticidade.'}

def explain_size(population, density):
    """Categorização didática própria, baseada exclusivamente nos números publicados."""
    if population is None:
        return None, 'Não foi possível consultar população do Censo 2022; nenhum perfil local foi presumido.'
    if population >= 1_000_000:
        label='escala populacional muito elevada'
        detail='Pela população informada, o debate pode abranger redes extensas de transporte, moradia e serviços.'
    elif population >= 100_000:
        label='escala populacional intermediária ou elevada'
        detail='Pela população informada, o debate pode avaliar a integração de bairros e equipamentos públicos.'
    else:
        label='escala populacional menor'
        detail='Pela população informada, o debate pode avaliar conexões entre centro, bairros e zonas de uso diverso.'
    if density is not None:
        if density >= 1000:
            detail+=' A densidade municipal calculada no Censo é alta; isso não informa, isoladamente, a arborização ou as condições de cada bairro.'
        else:
            detail+=' A densidade média municipal não descreve, isoladamente, ocupação e necessidades de cada bairro.'
    return label, detail


@app.get('/api/2050')
def scenario(city_id:int,green:int=50,mobility:int=50,heritage:int=50):
    city=get_city(city_id)
    if not city: fail('Município inválido.',404)
    if any(n<0 or n>100 for n in [green,mobility,heritage]): fail('Parâmetros devem estar entre 0 e 100.')
    profile=get_ibge_profile(city_id)
    pop=profile['population']
    density=profile['density_per_km2']
    category,context=explain_size(pop,density)
    has_data=pop is not None
    def hypothesis(high,low,value):
        return high if value>=60 else low
    green_text=hypothesis('Explorar hipótese de arborização ampliada, praças sombreadas e corredores verdes como escolhas possíveis de planejamento.',
        'Explorar manutenção dos espaços verdes e intervenções pontuais, de forma hipotética.',green)
    mobility_text=hypothesis('Explorar acessibilidade, transporte coletivo e caminhos seguros, como objetivos a serem discutidos.',
        'Explorar melhorias graduais de travessias, vias e sinalização, como possibilidades.',mobility)
    heritage_text=hypothesis('Explorar políticas de documentação, restauração e proteção do patrimônio cultural.',
        'Explorar inventários locais e preservação seletiva, dependente de escolhas públicas.',heritage)
    if has_data:
        if pop>=1_000_000:
            mobility_text+=' Em município de grande população, considerar diferentes escalas de deslocamento.'
            green_text+=' Avaliar a distribuição territorial dessas ações seria essencial.'
        elif pop>=100_000:
            mobility_text+=' Considerar conexões entre bairros e equipamentos urbanos.'
            green_text+=' Comparar acessibilidade a áreas verdes em diferentes bairros.'
        else:
            mobility_text+=' Considerar deslocamentos entre centro, bairros e comunidades, conforme a realidade local.'
            green_text+=' Considerar praças e espaços comunitários, sem presumir sua presença atual.'
    else:
        mobility_text+=' Sem indicadores locais disponíveis nesta consulta.'
        green_text+=' Sem indicadores locais disponíveis nesta consulta.'
    return {
        'city':f"{city['name']} — {city['uf']}", 'city_id':city_id,
        'target_year':2050,'is_prediction':False,
        'label':'CENÁRIO HIPOTÉTICO — NÃO É PREVISÃO',
        'profile':profile,'data_available':has_data,
        'city_context':context,'city_category':category,
        'themes':[
            {'name':'Áreas verdes','text':green_text},
            {'name':'Mobilidade','text':mobility_text},
            {'name':'Patrimônio','text':heritage_text}],
        'method':'Fatos: indicadores IBGE, Censo 2022, quando disponíveis. Cenários: possibilidades narrativas condicionadas aos controles; não representam projetos aprovados, previsões científicas, dados medidos de áreas verdes, mapas futuros ou fotografias reais.'}

@app.get('/')
def homepage(): return FileResponse(STATIC/'index.html')

app.mount('/static',StaticFiles(directory=STATIC),name='static')
