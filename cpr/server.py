import uvicorn

from contextlib import asynccontextmanager
from fastapi import FastAPI, Query, Response, HTTPException

from cpr.models import SearchResponse, DocumentResult
from cpr.data import DataStore

_store: DataStore | None = None

@asynccontextmanager
async def lifespan(_: FastAPI):
    global _store
    _store = DataStore()
    _store.load('/Users/ali/PycharmProjects/test-cpr/data/sample_data.json')
    yield
    _store = None


app = FastAPI(title='Search API', lifespan=lifespan)


@app.get("/search")
def search(
        query: str = Query(..., description="Search query "),
        limit: int = Query(default=10, ge=1, le=100, description="Number of results to return"),
) -> SearchResponse:
    if _store is None:
        raise HTTPException(status_code=503, detail='Data store not initialised')

    results = _store.search(query=query, limit=limit)
    return SearchResponse(
        query=query,
        total=len(results),
        results = [
            DocumentResult(
                id = r.document.id,
                title = r.document.title,
                score = r.score,
                snippet=r.document.text[:20]
            ) for r in results]
    )

@app.get('/search_tfidf')
def search_tfidf(
        query: str = Query(..., description="Search query "),
        limit: int = Query(default=10, ge=1, le=100, description="Number of results to return"),
) -> SearchResponse:
    pass

@app.get("/health")
def health() -> Response:
    return Response(status_code=200)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)