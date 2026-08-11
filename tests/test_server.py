import json
from pathlib import Path

import httpx
import pytest

import cpr.server as cpr_server_module
from cpr.data import DataStore
from cpr.server import app

SAMPLE_DATA = [
    {
        "id": "1",
        "title": "Alpha",
        "text": "I contain the word apple twice, and apple"
    },
    {
        "id": "2",
        "title": "Beta",
        "text": "Apple and cinnamon make the best crumbles"
    },
    {
        "id": "3",
        "title": "Apple",
        "text": "No fruit in this text at all"
    },
    {
        "id": "4",
        "title": "Null",
        "text": ""
    }
]

@pytest.fixture
def data_file(tmp_path: Path):
    path = tmp_path / 'docs.json'
    path.write_text(json.dumps(SAMPLE_DATA), encoding='UTF-8')
    return path

@pytest.fixture
def store(data_file: Path):
    s = DataStore()
    s.load(data_file)
    return s


@pytest.fixture
async def mock_client(store, monkeypatch):
    monkeypatch.setattr(cpr_server_module, '_store', store)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url='http://test'
    ) as client:
        yield client

class TestServer:

    async def test_health(self, mock_client):
        assert (await mock_client.get('/health')).status_code == 200

    async def test_search(self, mock_client):
        results = (await mock_client.get('/search?query=apple')).json()
        assert results == {'query': 'apple',
 'results': [{'id': '1',
              'score': 2.0,
              'snippet': 'I contain the word a',
              'title': 'Alpha'},
             {'id': '2',
              'score': 1.0,
              'snippet': 'Apple and cinnamon m',
              'title': 'Beta'},
             {'id': '3',
              'score': 1.0,
              'snippet': 'No fruit in this tex',
              'title': 'Apple'}],
 'total': 3}