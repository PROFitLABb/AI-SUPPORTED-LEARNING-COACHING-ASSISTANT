"""FastAPI application entry point."""
import uuid
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api.routes import analytics_routes, coaching_routes, learning_routes, user_routes, features_routes
from backend.database.db import engine, Base
import backend.models  # tüm modelleri Base'e kaydet

logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Learning Coach API",
    version="1.0.0",
    description="Kişiselleştirilmiş AI destekli öğrenme koçu backend API'si.",
)


@app.on_event("startup")
async def create_tables() -> None:
    """Uygulama başlarken veritabanı tablolarını oluştur."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Veritabanı tabloları hazır.")

# ── CORS (development: allow all origins) ────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(user_routes.router)
app.include_router(learning_routes.router)
app.include_router(coaching_routes.router)
app.include_router(analytics_routes.router)
app.include_router(features_routes.router)


# ── Global exception handler ─────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all handler: returns HTTP 500 with a unique error reference ID."""
    error_ref = str(uuid.uuid4())
    logger.exception("Unhandled error [ref=%s]: %s", error_ref, exc)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error_ref": error_ref,
        },
    )


@app.get("/health", tags=["health"])
async def health_check() -> dict:
    return {"status": "ok"}
