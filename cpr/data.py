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

def _read_txt(path: Path):
    lines = path.read_text(encoding='UTF-8').splitlines()
    rows = [
        {'id': str(i),
         'title': line[:60].rstrip(),
         'text': line
         }
        for i, line in enumerate((l for l in lines if l.strip()), start=1)
    ]
    return pd.DataFrame(rows)

class AbstractDataStore(ABC):

    def load(self, path: str|Path):
        raise NotImplementedError

    def search(self, query: str, limit: int = 10) -> list[SearchResult] | list[None]:
        raise NotImplementedError


class DataStore(AbstractDataStore):


    _LOADERS = {
        ".json": lambda p: pd.read_json(p),
        '.xml': lambda p: pd.read_xml(p),
        '.txt': _read_txt
    }

    def __init__(self):
        self._df: pd.DataFrame | None = None
        self._meta_cols: tuple[str] | tuple[None] = tuple()


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
        self._meta_cols = tuple(c for c in self._df.columns if c not in ('id', 'title', 'text'))

    def search(self, query: str, limit: int = 10) -> list[SearchResult] | list[None]:
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

        ranked = scores[mask].nlargest(limit)

        results: list[SearchResult] = []
        for idx, score in ranked.items():
            row = self._df.iloc[idx]
            results.append(
                SearchResult(
                    document=Document(
                        id=row['id'],
                        title=row['title'],
                        text = row['text'],
                        metadata={c: row[c] for c in self._meta_cols}
                    ),
                    score=float(score)
                )
            )
        return results

    def search_tdidf(self, query: str, limit: int = 10) -> list[SearchResult] | list[None]:
        ranked = {}
        results: list[SearchResult] = []
        for idx, score in ranked.items():
            row = self._df.iloc[idx]
            results.append(
                SearchResult(
                    document=Document(
                        id=row['id'],
                        title=row['title'],
                        text=row['text'],
                        metadata={}
                    ),
                    score=float(score)
                )
            )
        return results