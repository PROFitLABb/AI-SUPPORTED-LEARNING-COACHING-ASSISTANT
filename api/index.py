import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="AI Learning Coach API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lazy import — Vercel'de import hatalarını önlemek için
try:
    from backend.api.routes import (
        analytics_routes,
        coaching_routes,
        learning_routes,
        user_routes,
    )
    app.include_router(user_routes.router)
    app.include_router(learning_routes.router)
    app.include_router(coaching_routes.router)
    app.include_router(analytics_routes.router)
except Exception as e:
    @app.get("/import-error")
    def import_error():
        return {"error": str(e)}

@app.get("/health")
def health():
    return {"status": "ok"}
