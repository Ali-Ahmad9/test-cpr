from pydantic import BaseModel

class DocumentResult(BaseModel):
    id: str
    title: str
    score: float|int
    snippet: str

class SearchResponse(BaseModel):
    query: str
    total: int
    results: list[DocumentResult]


