"""Testes novos: fontes por município e base factual dos cenários."""
from unittest.mock import patch
import httpx
from fastapi.testclient import TestClient
from app.main import app
from app import sources


def block(code,name,value,city_id='3550308'):
    return {'id':str(code),'variavel':name,'resultados':[
        {'series':[{'localidade':{'id':city_id},'serie':{'2022':value}}]}]}


def test_parse_real_2022_indicators_and_respect_city_id():
    data=[block(93,'População residente','11451999'),
          block(6318,'Área territorial','1521.11'),
          block(614,'Densidade demográfica','7527.76'),
          block(93,'Outro município','9999999','3115300')]
    values=sources.parse_ibge_profile(data,3550308)
    assert values['population']==11451999
    assert values['area_km2']==1521.11
    assert values['density_per_km2']==7527.76
    assert values['year']==2022
    assert '3550308' in values['api_url']
    assert sources.parse_ibge_profile(data,3146107)['population'] is None


def test_unknown_values_are_never_invented():
    p=sources.parse_ibge_profile([block(93,'População','-'),block(6318,'Área','...')],3550308)
    assert p['population'] is None and p['area_km2'] is None
    assert sources.parse_ibge_profile(None,3550308)['density_per_km2'] is None


def test_ibge_transport_failure_falls_back_without_claiming_data():
    def bad(*a,**kw):
        raise httpx.ConnectError('offline')
    with patch.object(sources,'cached',side_effect=lambda key,fetch,ttl:fetch()),patch.object(sources,'http_get',side_effect=bad):
        row=sources.get_ibge_profile(3550308)
    assert row['population'] is None


def test_scenario_differs_by_census_population_and_is_labeled_hypothetical():
    def profile(city_id):
        return {'year':2022,'population':11451999 if city_id==3550308 else 74354,
                'density_per_km2':7527.76 if city_id==3550308 else 73.2,
                'area_km2':1500.0,
                'source_url':'https://sidra.ibge.gov.br/tabela/4714',
                'api_url':f'https://servicodados.ibge.gov.br/city/{city_id}'}
    with patch('app.main.get_ibge_profile',side_effect=profile):
        with TestClient(app) as c:
            sp=c.get('/api/2050?city_id=3550308&green=80&mobility=80').json()
            cat=c.get('/api/2050?city_id=3115300&green=80&mobility=80').json()
    assert sp['city']=='São Paulo — SP'
    assert cat['city']=='Cataguases — MG'
    assert sp['is_prediction'] is False and cat['is_prediction'] is False
    assert sp['data_available'] and cat['data_available']
    assert sp['themes'][1]['text']!=cat['themes'][1]['text']
    assert sp['city_context']!=cat['city_context']
    assert '2050' in sp['method'] or '2022' in sp['method']


def test_offline_scenario_discloses_generic_status():
    profile=sources.parse_ibge_profile(None,3550308)
    with patch('app.main.get_ibge_profile',return_value=profile):
        with TestClient(app) as c:
            response=c.get('/api/2050?city_id=3550308')
    assert response.status_code==200
    result=response.json()
    assert result['data_available'] is False
    assert result['profile']['population'] is None
    assert 'Sem indicadores' in result['themes'][0]['text']


def test_brasiliana_is_search_link_not_static_homepage():
    with TestClient(app) as c:
        page=c.get('/').text
        js=c.get('/static/app.js').text
        assert '/brasiliana/discover?query=Cataguases' in page
        assert 'encodeURIComponent(city.name)' in js
        assert 'sem garantia' in page.lower() or 'sem garantia' in js.lower()
        assert 'id="futureFacts"' in page
        assert '1.7.0' in page
