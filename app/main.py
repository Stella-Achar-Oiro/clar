import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.observability.logging import configure_logging
from app.api.routes import health, metrics
from app.services.llm import LLMTimeoutError
from loguru import logger

configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("clar_startup")
    yield
    logger.info("clar_shutdown")


app = FastAPI(title="CLAR", version="1.0.0", lifespan=lifespan)

app.include_router(health.router)
app.include_router(metrics.router)


@app.exception_handler(413)
async def file_too_large(_: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=413, content={"error": "File exceeds 10 MB limit"})


@app.exception_handler(415)
async def unsupported_media(_: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=415, content={"error": "Only PDF and plain text files are supported"})


@app.exception_handler(LLMTimeoutError)
async def llm_timeout(_: Request, exc: LLMTimeoutError) -> JSONResponse:
    return JSONResponse(status_code=504, content={"error": "Analysis is taking longer than expected. Please try again."})


@app.exception_handler(Exception)
async def generic_error(request: Request, exc: Exception) -> JSONResponse:
    request_id = str(uuid.uuid4())
    logger.error("unhandled_exception", error=str(exc), request_id=request_id)
    return JSONResponse(status_code=500, content={"error": "Internal server error", "request_id": request_id})


# Serve Next.js static export if it exists
static_dir = Path("static")
if static_dir.exists():
    app.mount("/", StaticFiles(directory="static", html=True), name="static")
