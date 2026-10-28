
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.code_search import CodeSearch


app = FastAPI(
    title="RepoPilot AI",
    description="A read-only AI codebase exploration API",
    version="0.1.0",
)

# Configure the repository through an environment variable.
# Default to the current working directory for local development.
REPO_PATH = Path(
    os.getenv("REPILOT_REPO_PATH", os.getcwd())
).resolve()

try:
    code_search = CodeSearch(str(REPO_PATH))
except ValueError as exc:
    raise RuntimeError(
        f"Invalid repository path: {REPO_PATH}"
    ) from exc


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=200)
    limit: int = Field(default=20, ge=1, le=100)


class ReadRequest(BaseModel):
    path: str = Field(min_length=1, max_length=500)
    start_line: int = Field(default=1, ge=1)
    end_line: int = Field(default=100, ge=1, le=10000)


@app.get("/")
def home():
    return {
        "name": "RepoPilot AI",
        "status": "running",
        "repository": REPO_PATH.name,
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/search/files")
def search_files(request: SearchRequest):
    try:
        results = code_search.search_files(
            request.query,
            request.limit,
        )
        return {"results": results, "count": len(results)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/search/code")
def search_code(request: SearchRequest):
    try:
        results = code_search.search_code(
            request.query,
            request.limit,
        )
        return {"results": results, "count": len(results)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/read")
def read_file(request: ReadRequest):
    if request.end_line < request.start_line:
        raise HTTPException(
            status_code=400,
            detail="end_line must be >= start_line",
        )

    if request.end_line - request.start_line + 1 > 200:
        raise HTTPException(
            status_code=400,
            detail="Read at most 200 lines per request",
        )

    try:
        result = code_search.read_file(
            request.path,
            request.start_line,
            request.end_line,
        )
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="File not found") from exc
