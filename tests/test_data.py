import json
import pytest
from pathlib import Path

from cpr.data import DataStore, SearchResult, Document

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

    def test_search(self, data_store):
        results = data_store.search('apple', limit=1)
        assert results == [
            SearchResult(
                score=2.0,
                document=Document(
                    id= "1",
                    title="Alpha",
                    text="I contain the word apple twice, and apple"
                )
            )
        ]

    def test_unique_search_tdidf(self, tmp_path):
        docs = [
            {'id': '1', 'title': 'First', "text": 'shared unique content'},
            {'id': '2', 'title': 'Second', "text": 'shared general content'},
            {'id': '3', 'title': 'Third', "text": 'shared general content'},
        ]
        path = tmp_path / 'docs.json'
        path.write_text(json.dumps(docs), encoding='utf-8')
        store = DataStore()
        store.load(path)

        doc1_unique_score = store.search_tfidf('unique')[0].score
        doc1_shared_score = next(r.score for r in store.search_tfidf('shared') if r.document.id == "1")

        assert doc1_unique_score > doc1_shared_score
