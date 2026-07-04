"""
Application entrypoint: wires up middleware, routers, exception handling,
and startup/shutdown hooks.
"""
import time

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import admin, auth, documents, query
from app.core.config import get_settings
from app.db.database import Base, engine
from app.utils.logger import get_logger

settings = get_settings()
logger = get_logger("app")

app = FastAPI(
    title=settings.APP_NAME,
    description="Enterprise AI Knowledge Assistant — RAG-powered document Q&A, "
                "summarization, comparison, and reporting.",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration_ms = int((time.time() - start) * 1000)
    logger.info(
        f"{request.method} {request.url.path} -> {response.status_code} ({duration_ms}ms)"
    )
    response.headers["X-Process-Time-Ms"] = str(duration_ms)
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.url.path}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error. Please try again later."},
    )


@app.on_event("startup")
def on_startup():
    # In production, use Alembic migrations instead of create_all.
    Base.metadata.create_all(bind=engine)
    logger.info(f"{settings.APP_NAME} started (env={settings.ENV}, llm={settings.LLM_PROVIDER})")


@app.get("/api/v1/health", tags=["health"])
def health_check():
    return {"status": "ok", "service": settings.APP_NAME, "env": settings.ENV}


app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(query.router)
app.include_router(admin.router)
