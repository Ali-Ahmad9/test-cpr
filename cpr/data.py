from abc import ABC
import re
from dataclasses import dataclass, field
from pathlib import Path
import pandas as pd


@dataclass
class Document:
    id: str
    title: str
    text: str
    metadata: dict = field(default_factory=dict)

@dataclass
class SearchResult:
    document: Document
    score: float  #  cosine similarity


class AbstractDataStore(ABC):

    def load(self, path: str|Path):
        raise NotImplementedError

    def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        raise NotImplementedError


class DataStore(AbstractDataStore):

    _LOADERS = {
        ".json": lambda p: pd.read_json(p),
        '.xml': lambda p: pd.read_xml(p)
    }

    def __init__(self):
        self._df: pd.DataFrame = None

    def _clean_df(self, df: pd.DataFrame) -> pd.DataFrame:
        if 'id' not in df.columns:
            raise ValueError("Must have 'id' in column")
        df['id'] = df['id'].astype('str')
        for col in ('title', 'text'):
            if col not in df.columns:
                df[col] = ''
            df[col] = df[col].fillna('').astype('str')
        return df.reset_index(drop=True)

    def load(self, path):
        path = Path(path)
        file_type = path.suffix.lower()
        loader = self._LOADERS.get(file_type)
        if not loader:
            raise ValueError(f'Unsupported file type {file_type}. '
                             f'Supported: {list(self._LOADERS.keys())}')
        df = loader(path)
        self._df = self._clean_df(df)