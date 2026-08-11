import uvicorn
from fastapi import FastAPI, Query, Response

from cpr.models import SearchResponse


app = FastAPI()

@app.get("/search")
def search(
        query: str = Query(..., description="Search query "),
        limit: int = Query(default=10, ge=1, le=100, description="Number of results to return"),
) -> SearchResponse:
    pass


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)