import io
import os
import tempfile
from pathlib import Path

# Configurar ambiente isolado ANTES de importar o aplicativo.
ROOT=Path(tempfile.mkdtemp(prefix='aevia-test-'))
os.environ['DB_PATH']=str(ROOT/'test.sqlite3')
os.environ['STORAGE_DIR']=str(ROOT/'storage')
os.environ['ADMIN_PASSWORD']='senha-teste-comprida-e-segura'
os.environ['SESSION_SECRET']='1234567890abcdefghijklmnopqrstuv'
os.environ['APP_ENV']='development'
from fastapi.testclient import TestClient
from PIL import Image
from app.main import app,CLIENT_POSTS
from app.db import database
from app.sources import normalize, text_only


def test_normalization():
    assert normalize('São José')=='sao jose'
    assert text_only('<b>Crédito &amp; fonte</b>')=='Crédito & fonte'


def test_city_timeline_scenario():
    with TestClient(app) as c:
        s=c.get('/api/status').json()
        assert s['municipalities']>=16
        city=c.get('/api/municipios?q=ouro').json()['results'][0]
        assert city['name']=='Ouro Preto'
        future=c.get('/api/2050?city_id=3146107&green=90&mobility=80&heritage=95').json()
        assert future['is_prediction'] is False
        assert len(future['themes'])==3
        assert 'arborização ampliada' in future['themes'][0]['text']
        assert c.get('/api/2050?city_id=3146107&green=101').status_code==400


def test_contribution_stays_private_until_human_approval():
    with TestClient(app) as c:
        img=Image.new('RGB',(680,560),(200,170,125))
        out=io.BytesIO();img.save(out,'PNG')
        data={
          'city_id':'3115300','city_name':'Cataguases','latitude':'-21.3892','longitude':'-42.6963',
          'place_name':'Praça Central','title':'Uma história da praça em família',
          'story':'Imagem de arquivo familiar, data aproximada e autoria declarada pela família.',
          'author_name':'Pessoa de Teste','license':'Autorizo exibição no AEVIA','rights_basis':'owner',
          'source_reference':'Acervo familiar','historic_year':'1970','consent':'true','ai_consent':'false'
        }
        submitted=c.post('/api/contribuicoes',data=data,files={'image':('praça.png',out.getvalue(),'image/png')})
        assert submitted.status_code==201,submitted.text
        cid=submitted.json()['id']
        assert submitted.json()['status']=='pendente'
        public=c.get('/api/contribuicoes?city_id=3115300').json()['items']
        assert not public
        assert c.get('/media/'+cid+'.jpg').status_code==404
        assert c.get('/api/admin/contribuicoes').status_code==401
        bad=c.post('/api/admin/login',json={'password':'incorreta'})
        assert bad.status_code==401
        logged=c.post('/api/admin/login',json={'password':'senha-teste-comprida-e-segura'})
        assert logged.status_code==200
        queue=c.get('/api/admin/contribuicoes').json()['items']
        assert len(queue)==1
        assert queue[0]['ai_consent']==0
        assert c.post('/api/admin/contribuicoes/'+cid+'/ia').status_code==403
        assert c.get('/api/admin/media/'+cid).status_code==200
        approved=c.post('/api/admin/contribuicoes/'+cid+'/revisar',json={'status':'aprovada','note':'Conferência documental feita para teste.'})
        assert approved.status_code==200
        public=c.get('/api/contribuicoes?city_id=3115300').json()['items']
        assert len(public)==1
        assert public[0]['image'].startswith('/media/')
        assert c.get(public[0]['image']).status_code==200


def test_cross_origin_write_is_blocked():
    with TestClient(app) as c:
        r=c.post('/api/admin/login',headers={'Origin':'https://site-invalido.example'},json={'password':'senha-teste-comprida-e-segura'})
        assert r.status_code==403


def test_address_without_paid_key_uses_public_nominatim_with_city_id(monkeypatch):
    from app import sources
    monkeypatch.delenv('GEOAPIFY_API_KEY',raising=False)
    monkeypatch.setenv('ENABLE_PUBLIC_NOMINATIM','yes')
    seen=[]
    def fake_loader(url,params=None,timeout=17):
        seen.append((url,params))
        class Fake:
            def json(self):
                return [{'lat':'-21.7609','lon':'-43.3503','display_name':'Rua Halfeld, Juiz de Fora, MG, Brasil',
                        'address':{'city':'Juiz de Fora','state':'Minas Gerais'}}]
        return Fake()
    monkeypatch.setattr(sources,'http_get',fake_loader)
    with TestClient(app) as c:
        r=c.get('/api/enderecos?q=Rua%20Halfeld&city_id=3136702')
        assert r.status_code==200, r.text
        payload=r.json()
        assert payload['provider'].startswith('OpenStreetMap')
        assert payload['results'][0]['lat']==-21.7609
        assert 'Juiz de Fora, MG' in seen[0][1]['q']
        assert seen[0][1]['countrycodes']=='br'
        assert c.get('/api/enderecos?q=Rua%20A&city_id=9999999').status_code==404
        # O cache evita a segunda chamada à instância pública.
        assert c.get('/api/enderecos?q=Rua%20Halfeld&city_id=3136702').status_code==200
        assert len(seen)==1


def test_city_search_returns_juiz_de_fora_and_city_coordinates():
    with TestClient(app) as c:
        items=c.get('/api/municipios?q=juiz%20de%20fora').json()['results']
        selected=next(city for city in items if city['name']=='Juiz de Fora')
        assert selected['uf']=='MG'
        assert selected['id']==3136702
        assert -35<selected['latitude']<6
        assert -75<selected['longitude']<-30
        assert c.get('/api/municipio/3136702').json()['name']=='Juiz de Fora'


def test_geocoder_can_be_switched_off(monkeypatch):
    from app import sources
    monkeypatch.delenv('GEOAPIFY_API_KEY',raising=False)
    monkeypatch.setenv('ENABLE_PUBLIC_NOMINATIM','no')
    with TestClient(app) as c:
        response=c.get('/api/enderecos?q=Rua%20Central&city_id=3115300')
        assert response.status_code==200
        assert response.json()=={'configured':False,'provider':None,'results':[]}


def test_commons_geodata_separates_undated_images(monkeypatch):
    from app import sources
    def fake_loader(url, params=None, timeout=17):
        class Fake:
            def json(self):
                return {"query": {"pages": [
                  {"pageid": 11,"title": "File:Praca_1930.jpg","imageinfo": [{
                     "mime":"image/jpeg","thumburl":"https://upload.wikimedia.org/test.jpg",
                     "descriptionurl":"https://commons.wikimedia.org/wiki/File:Praca_1930.jpg",
                     "extmetadata":{"DateTimeOriginal":{"value":"1930"},"LicenseShortName":{"value":"CC BY-SA 4.0"}}}]},
                  {"pageid": 12,"title": "File:Antiga.jpg","imageinfo": [{
                     "mime":"image/jpeg","thumburl":"https://upload.wikimedia.org/test2.jpg",
                     "descriptionurl":"https://commons.wikimedia.org/wiki/File:Antiga.jpg",
                     "extmetadata":{"DateTime":{"value":"2025-09-01"}}}]},
                ]}}
        return Fake()
    monkeypatch.setattr(sources,'http_get',fake_loader)
    results=sources.commons_archive(-21.3892,-42.6963,1000)
    assert len(results)==2
    assert results[0]['year']==1930
    # Data de upload NÃO é tratada como ano da fotografia.
    assert results[1]['year'] is None
    assert results[1]['location_confidence']=='geotag_proximidade'


def test_invalid_coordinates_are_never_sent_to_a_city_card():
    from app import sources
    fake={'id':3115300,'name':'Cataguases','uf':'MG','latitude':-84.4200,'longitude':147.3157}
    city=sources.clean_city_coords(fake)
    assert city['latitude']==-21.3892
    assert city['longitude']==-42.6963
    assert sources.valid_brazil_coords(city['latitude'],city['longitude'])
    assert not sources.valid_brazil_coords(-84.4200,147.3157)
    assert not sources.valid_brazil_coords(None,None)


def test_iss_orbital_images_do_not_masquerade_as_street_photos():
    from app.sources import parse_commons_pages
    def page(pid,name):
        return {'pageid':pid, 'title':'File:'+name, 'imageinfo':[{'mime':'image/jpeg',
            'descriptionurl':'https://commons.wikimedia.org/wiki/File:'+name,
            'thumburl':'https://upload.wikimedia.org/example.jpg',
            'extmetadata':{'DateTimeOriginal':{'value':'2014'}}}]}
    rows=parse_commons_pages([page(1,'ISS038-E-66933_-_View_of_Earth.jpg'),
                              page(2,'Praca_Cataguases_1960.jpg')],
                              'geotag_proximidade','proxima')
    assert len(rows)==1
    assert rows[0]['id']=='commons-2'


def test_leaflet_stylesheet_has_official_integrity_and_placeholder_removed():
    from app.db import ROOT
    html=(ROOT/'static/index.html').read_text(encoding='utf-8')
    js=(ROOT/'static/app.js').read_text(encoding='utf-8')
    assert 'sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=' in html
    assert "$('#map').replaceChildren();" in js
    assert 'function isBrazilCoordinate' in js


def test_iss_filter_even_without_view_of_earth():
    from app.sources import parse_commons_pages
    page={'pageid':100, 'title':'File:ISS042-E-00051.jpg', 'imageinfo':[{'mime':'image/jpeg',
       'descriptionurl':'https://commons.wikimedia.org/wiki/File:ISS042-E-00051.jpg',
       'thumburl':'https://upload.wikimedia.org/sample.jpg','extmetadata':{}}]}
    assert parse_commons_pages([page],'geotag_proximidade','próxima') == []


def test_admin_can_delete_contribution_and_photo():
    import uuid
    from app.main import UPLOADS
    with TestClient(app) as c:
        login=c.post('/api/admin/login',json={'password':'senha-teste-comprida-e-segura'})
        assert login.status_code==200
        img=Image.new('RGB',(640,480),(100,20,200))
        stream=io.BytesIO();img.save(stream,'PNG')
        item=c.post('/api/contribuicoes',data={
          'city_id':'3146107','city_name':'Ouro Preto','latitude':'-20.3855','longitude':'-43.5034',
          'place_name':'Praça','title':'Arquivo de teste para exclusão '+uuid.uuid4().hex[:6],
          'story':'Relato do arquivo familiar para o teste de exclusão permanente de registros.',
          'author_name':'Pessoa de Teste','license':'Autorizo exibição no AEVIA','rights_basis':'owner',
          'source_reference':'Arquivo de teste','historic_year':'1950','consent':'true', 'ai_consent':'false'
        },files={'image':('foto.png',stream.getvalue(),'image/png')})
        assert item.status_code==201,item.text
        cid=item.json()['id']
        queue=c.get('/api/admin/contribuicoes?status=pendente').json()['items']
        target=next(x for x in queue if x['id']==cid)
        assert c.get('/api/admin/media/'+cid).status_code==200
        deleted=c.delete('/api/admin/contribuicoes/'+cid)
        assert deleted.status_code==200
        assert c.get('/api/admin/media/'+cid).status_code==404
        assert c.get('/api/admin/contribuicoes?status=pendente').status_code==200
        assert c.delete('/api/admin/contribuicoes/'+cid).status_code==404


def test_prepublication_includes_privacy_terms_and_health():
    from app.db import ROOT
    with TestClient(app) as c:
        assert c.get('/healthz').json()=={'status':'ok'}
        assert c.get('/static/privacidade.html').status_code==200
        assert c.get('/static/termos.html').status_code==200
        assert c.get('/static/app.js').status_code==200
    assert (ROOT/'configurar_administrador.bat').exists()
    assert (ROOT/'verificar_publicacao.bat').exists()


def test_release_1_7_and_web_cache_are_identifiable():
    with TestClient(app) as c:
        r=c.get('/')
        assert r.status_code==200
        assert 'V1.7' in r.text
        assert 'no-store' in r.headers['cache-control']
        assert r.headers['x-aevia-version']=='1.7.0'
        assert '/static/app.js?v=1.7.0' in r.text
        assert c.get('/api/status').json()['version']=='1.7.0'


def test_search_city_sem_acentos_sao_paulo():
    with TestClient(app) as c:
        cities=c.get('/api/municipios?q=sao%20paulo').json()['results']
        assert any(x['id']==3550308 and x['uf']=='SP' and x['name']=='São Paulo' for x in cities)


def test_release_launch_path_and_compact_map():
    from app.db import ROOT as project_root
    launcher=(project_root/'app'/'launcher.py').read_text(encoding='utf-8')
    css=(project_root/'static'/'style.css').read_text(encoding='utf-8')
    assert "'8017'" in launcher and "EXPECTED='1.7.0'" in launcher
    assert '#map{height:340px' in css
    assert '#map{height:240px' in css


def test_rights_form_is_understandable_and_only_shows_for_photos():
    with TestClient(app) as c:
        html=c.get('/').text
        assert 'Você pode compartilhar esta fotografia?' in html
        assert 'id="photoRights" hidden' in html
        assert 'Não sei se tenho autorização' in html
        assert 'A foto foi feita' not in html
        js=c.get('/static/app.js').text
        assert 'updatePhotoRights()' in js
        assert "$('#photoRights').hidden=!hasPhoto" in js
        assert 'Sem confirmação' in html


def test_photo_rights_required_and_evidence_checked_on_server():
    CLIENT_POSTS.clear()
    with TestClient(app) as c:
        img=Image.new('RGB',(200,180),(120,160,180))
        buf=io.BytesIO();img.save(buf,'PNG');raw=buf.getvalue()
        entry={
          'city_id':'3115300','city_name':'Cataguases','latitude':'-21.3892','longitude':'-42.6963',
          'place_name':'Rua do Teste','title':'Uma imagem histórica de teste',
          'story':'Foto de exemplo para verificar os direitos de uso na plataforma.',
          'author_name':'Usuário de Teste','license':'Autorizo exibição no AEVIA',
          'source_reference':'Acervo de teste','consent':'true', 'ai_consent':'false'
        }
        def upload(data):
            return c.post('/api/contribuicoes',data=data,files={'image':('teste.png',raw,'image/png')})
        r=upload(entry)
        assert r.status_code==400 and 'direitos' in r.json()['detail']
        r=upload({**entry,'rights_basis':'unsure'})
        assert r.status_code==400
        r=upload({**entry,'rights_basis':'permission'})
        assert r.status_code==400 and 'fonte' in r.json()['detail']
        r=upload({**entry,'rights_basis':'open','rights_reference':'Fonte CC BY 4.0 https://example.test/foto'})
        assert r.status_code==400 and 'licença' in r.json()['detail']
        r=upload({**entry,'rights_basis':'permission','rights_reference':'Autorização do titular identificada em acervo familiar'})
        assert r.status_code==201,r.text
        with database() as db:
            row=db.execute('SELECT rights_basis,rights_reference,license FROM contributions WHERE id=?',(r.json()['id'],)).fetchone()
            assert row['rights_basis']=='permission'
            assert 'Autorização' in row['rights_reference']
        r=upload({**entry,'rights_basis':'public_domain','rights_reference':'Digitalização com fonte que identifica domínio público','license':'Domínio público'})
        assert r.status_code==409  # foto repetida, embora licença e direitos agora sejam válidos


def test_story_without_photo_does_not_require_image_license():
    CLIENT_POSTS.clear()
    with TestClient(app) as c:
        entry={
          'city_id':'3115300','city_name':'Cataguases','latitude':'-21.3892','longitude':'-42.6963',
          'place_name':'Praça do Teste','title':'Relato da memória da praça',
          'story':'Relato original enviado sem fotografia para preservar a memória local.',
          'author_name':'Usuário de Teste','license':'Relato autorizado',
          'source_reference':'Relato próprio','consent':'true','ai_consent':'false'
        }
        response=c.post('/api/contribuicoes',data=entry)
        assert response.status_code==201,response.text
        with database() as db:
            row=db.execute('SELECT rights_basis,license FROM contributions WHERE id=?',(response.json()['id'],)).fetchone()
        assert row['rights_basis']=='story' and row['license']=='Relato autorizado'


def test_migration_existing_database_keeps_existing_contributions(tmp_path,monkeypatch):
    import sqlite3
    from app import db as dbmod
    old=tmp_path/'legacy.sqlite3'
    with sqlite3.connect(old) as con:
        con.execute('CREATE TABLE contributions (id TEXT PRIMARY KEY, city_id INTEGER, image_hash TEXT, status TEXT, license TEXT)')
        con.execute('INSERT INTO contributions (id,status,license) VALUES (?,?,?)',('antigo','pendente','Autorizo exibição no AEVIA'))
    monkeypatch.setattr(dbmod,'DB_PATH',old)
    dbmod.initialize()
    with sqlite3.connect(old) as con:
        row=con.execute('SELECT id,rights_basis,rights_reference FROM contributions').fetchone()
    assert row==('antigo','registro_anterior','')
