import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.exceptions import BaseAPIException
from app.api.routes import health, documents, edges, search, debug

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Hybrid Vector-Graph Retrieval API",
    description="Combines semantic vector search with graph knowledge traversal",
    version="2.0.0")


@app.exception_handler(BaseAPIException)
async def api_exception_handler(request: Request, exc: BaseAPIException):
    """Handle all custom API exceptions"""
    logger.error(f"API Exception: {exc.message}", exc_info=True)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message, "type": exc.__class__.__name__}
    )

app.include_router(health.router, prefix="/v1")
app.include_router(documents.router, prefix="/v1")
app.include_router(edges.router, prefix="/v1")
app.include_router(search.router, prefix="/v1")
app.include_router(debug.router, prefix="/v1")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
