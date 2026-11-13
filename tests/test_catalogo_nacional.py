"""Regressão: todos os municípios disponíveis mesmo quando o servidor está offline."""
from fastapi.testclient import TestClient
from app.main import app

def test_catalogo_nacional_embutido_na_imagem():
    with TestClient(app) as client:
        status=client.get('/api/status').json()
        assert status['municipalities']>=5500
        assert status['city_catalog_complete'] is True
        for code,name in [(3205309,'Vitória'),(3171303,'Viçosa'),(3550308,'São Paulo'),(3136702,'Juiz de Fora')]:
            r=client.get(f'/api/municipio/{code}')
            assert r.status_code==200
            assert r.json()['name']==name
        matches=client.get('/api/municipios',params={'q':'vi','limit':50}).json()['results']
        assert any(x['name']=='Vitória' for x in matches)
        assert any(x['name']=='Viçosa' for x in matches)
