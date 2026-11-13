"""Regressão da Beta pública: não aceita uploads e informa ausência de acervo."""
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app
import app.main as main


def test_status_exposes_contribution_flag(monkeypatch):
    monkeypatch.setattr(main, 'PUBLIC_CONTRIBUTIONS_ENABLED', False)
    with TestClient(app) as client:
        data=client.get('/api/status').json()
        assert data['version']=='1.7.0'
        assert data['public_contributions_enabled'] is False


def test_disabled_upload_is_rejected_before_parsing_multipart(monkeypatch):
    monkeypatch.setattr(main, 'PUBLIC_CONTRIBUTIONS_ENABLED', False)
    with TestClient(app) as client:
        response=client.post('/api/contribuicoes',data={'story':'arquivo teste'})
        assert response.status_code==403
        assert 'desativ' in response.json()['detail'].lower() or 'fechado' in response.json()['detail'].lower()


def test_brazilian_sources_and_empty_state_present():
    with TestClient(app) as client:
        js=client.get('/static/app.js').text
        html=client.get('/').text
        assert 'commonsSearchLink' in html
        assert 'Acervo' in html or 'ACERVO' in html
        assert 'nenhum registro encontrado' in js.lower()
        assert 'state.contributionsEnabled===false' in js
        assert '1.7.0' in html


def test_deployment_blueprint_prevents_uploads():
    yml=(Path(__file__).resolve().parents[1]/'render.yaml').read_text()
    assert 'APP_ENV' in yml and 'beta' in yml
    assert 'ENABLE_PUBLIC_CONTRIBUTIONS' in yml and "'no'" in yml


def test_brazilian_city_and_census_apis_still_exist():
    with TestClient(app) as client:
        city=client.get('/api/municipio/3115300')
        assert city.status_code==200
        assert city.json()['name']=='Cataguases'
