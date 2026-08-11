from pydantic import BaseModel

from cpr.data import SearchResult

class DocumentResult(BaseModel):
    id: str
    title: str
    score: float|int
    snippet: str

class SearchResponse(BaseModel):
    query: str
    total: int
    results: list[DocumentResult]


def build_response(query: str, results: list[SearchResult] | list[None]) -> SearchResponse:
    return SearchResponse(
        query=query,
        total=len(results),
        results=[
            DocumentResult(
                id=r.document.id,
                title=r.document.title,
                score=r.score,
                snippet=r.document.text[:20]
            ) for r in results]
    )