import pytest
from dev_server import create_app
from api import Api


@pytest.fixture
def client():
    api = Api()
    app = create_app(api=api)
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_index_route(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'erAL' in response.data
    assert response.headers.get('Cache-Control') is not None


def test_static_asset_serving(client):
    response = client.get('/css/style.css')
    assert response.status_code == 200


def test_api_call_success(client):
    payload = {
        'manager': 'world',
        'func': 'get_state',
        'args': [],
    }
    response = client.post('/api/call', json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert 'result' in data
    assert 'player' in data['result']
    assert 'time' in data['result']


def test_api_call_missing_parameters(client):
    response = client.post('/api/call', json={'manager': 'world'})
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False
    assert 'required' in data['error']


def test_api_call_invalid_manager(client):
    payload = {
        'manager': 'non_existent_manager',
        'func': 'get_state',
    }
    response = client.post('/api/call', json=payload)
    assert response.status_code == 500
    data = response.get_json()
    assert data['success'] is False


def test_api_report_error(client):
    payload = {
        'message': 'Test JS frontend error',
        'source': 'test.js',
        'line': 42,
        'column': 10,
        'stack': 'Error: test',
    }
    response = client.post('/api/report_error', json=payload)
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
