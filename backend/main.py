import logging
import sys
import warnings
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import CORS_ORIGINS, IS_PRODUCTION, _IS_DEFAULT_SECRET
from .database import Base, engine
from .routers import auth, chat, courses, health, imports, library, practice, questions, wrongbook

logger = logging.getLogger("exam_system")

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Exam System API", version="1.0.0", lifespan=lifespan)

# ── Startup warnings ────────────────────────────────────────────────────────
if _IS_DEFAULT_SECRET:
    if IS_PRODUCTION:
        # Should have been caught in config.py already; safeguard here.
        raise RuntimeError(
            "SECRET_KEY is still the default value. "
            "Production requires a unique SECRET_KEY set via environment variable."
        )
    else:
        msg = (
            "WARNING: SECRET_KEY is using the default value. "
            "This is fine for local development, but set a unique key for production.\n"
            "  Generate a random key: python -c \"import secrets; print(secrets.token_urlsafe(48))\"\n"
            "  Add to backend/.env: SECRET_KEY=<your-generated-key>\n"
            "  Set APP_ENV=production when deploying."
        )
        logger.warning(msg)
        warnings.warn(msg)

# Ensure tables are created (both at import time and via lifespan)
Base.metadata.create_all(bind=engine)

# CORS — origins read from config (env CORS_ORIGINS, fallback ["*"])
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(questions.router)
app.include_router(practice.router)
app.include_router(wrongbook.router)
app.include_router(imports.router)
app.include_router(courses.router)
app.include_router(library.router)
app.include_router(chat.router)
