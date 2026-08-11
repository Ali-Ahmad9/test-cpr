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

    def search(self, query: str, limit: int = 10) -> list[SearchResult] | None:
        raise NotImplementedError


class DataStore(AbstractDataStore):

    _LOADERS = {
        ".json": lambda p: pd.read_json(p),
        '.xml': lambda p: pd.read_xml(p)
    }

    def __init__(self):
        self._df: pd.DataFrame | None = None

    @staticmethod
    def _clean_df(df: pd.DataFrame) -> pd.DataFrame:
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

    def search(self, query: str, limit: int = 10) -> list[SearchResult] | None:
        keywords = [kw.lower() for kw in query.strip().split() if kw]
        if not keywords or self._df is None:
            print("Nothing found!")
            return []

        haystack = (self._df['title'] + ' ' + self._df['text']).str.lower()
        scores = sum(haystack.str.count(kw) for kw in keywords)

        # only count results that have at least one match
        mask = scores > 0
        if not mask.any():
            print("Nothing found!")
            return []

        # only produce top 'limit' results
        ranked = scores[mask].sort_values(ascending=False).head(limit)

        meta_cols = [c for c in self._df.columns if c not in ('id', 'text', 'title')]
        results: list[SearchResult] = []
        for idx, score in ranked.items():
            row = self._df.iloc[idx]
            results.append(
                SearchResult(
                    document=Document(
                        id=row['id'],
                        title=row['title'],
                        text = row['text'],
                        metadata={c: row[c] for c in meta_cols}
                    ),
                    score=float(score)
                )
            )
        return results

