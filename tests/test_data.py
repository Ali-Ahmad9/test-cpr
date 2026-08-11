import json
import pytest
from pathlib import Path

from cpr.data import DataStore
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
def data_store(data_file):
    store = DataStore()
    store.load(data_file)
    yield store

class TestDataStore():

    def test_load(self, data_store):
        assert data_store._df.shape == (4, 3)

    def test_exception(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError):
            DataStore().load(tmp_path / 'notexistent.json')

    def test_unsupported_filetype(self):
        with pytest.raises(ValueError):
            DataStore().load('somethingwrong.docx')