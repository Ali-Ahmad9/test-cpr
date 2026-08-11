from abc import ABC
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


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
        self._vectoriser: TfidfVectorizer | None = None


    def _build_df(self, df: pd.DataFrame) -> pd.DataFrame:
        if 'id' not in df.columns:
            raise ValueError("Must have 'id' in column")
        df['id'] = df['id'].astype('str')
        for col in ('title', 'text'):
            if col not in df.columns:
                df[col] = ''
            df[col] = df[col].fillna('').astype('str')
        raw_text = (df['title'] + ' ' + df['text']).tolist()
        self._vectoriser = TfidfVectorizer(stop_words='english', lowercase=True)
        self._tfidf_matrix = self._vectoriser.fit_transform(raw_text)
        return df.reset_index(drop=True)

    def load(self, path):
        path = Path(path)
        file_type = path.suffix.lower()
        loader = self._LOADERS.get(file_type)
        if not loader:
            raise ValueError(f'Unsupported file type {file_type}. '
                             f'Supported: {list(self._LOADERS.keys())}')
        df = loader(path)
        self._df = self._build_df(df)
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

        ranked = scores[mask].nlargest(limit)  # mitigates top k problem

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

    def search_tfidf(self, query: str, limit: int = 10) -> list[SearchResult] | list[None]:
        if not query.strip() or self._df is None:
            print("Nothing found!")
            return []
        query_vec = self._vectoriser.transform([query])
        raw_scores = cosine_similarity(query_vec, self._tfidf_matrix).flatten()

        nonzero_mask = raw_scores > 0
        if not nonzero_mask.any():
            return []

        # top k problem
        # can become an issue where our limit > number of results
        k = min(limit, int(nonzero_mask.sum()))
        if k < len(raw_scores):
            # np.argpartition returns indices of top K elements in array
            top_k = np.argpartition(raw_scores, -k)[-k:]
        else:
            top_k = np.where(nonzero_mask)[0]
        top_k = top_k[raw_scores[top_k].argsort()[::-1]]
        results: list[SearchResult] = []
        for idx in top_k:
            row = self._df.iloc[idx]
            results.append(
                SearchResult(
                    document=Document(
                        id=row['id'],
                        title=row['title'],
                        text=row['text'],
                        metadata={}
                    ),
                    score=round(float(raw_scores[idx]), 4)
                )
            )
        return results