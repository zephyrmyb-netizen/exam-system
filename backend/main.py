import logging
import sys
import warnings
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import (
    CORS_IS_WILDCARD,
    CORS_ORIGINS,
    IS_PRODUCTION,
    _IS_DEFAULT_INVITE,
    _IS_DEFAULT_SECRET,
    _RAW_CORS,
)
from .database import Base, engine
from .logging_config import configure_logging
from .middleware import RequestIDMiddleware
from .routers import auth, chat, courses, health, imports, library, practice, questions, wrongbook

configure_logging()
logger = structlog.get_logger("exam_system")


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Exam System API", version="1.0.0", lifespan=lifespan)
app.add_middleware(RequestIDMiddleware)

# ── Startup warnings (development only — production errors are raised in config.py) ─
if not IS_PRODUCTION:
    _warnings = []

    if _IS_DEFAULT_SECRET:
        _warnings.append(
            "SECRET_KEY is using the default value. "
            "This is fine for local development, but set a unique key for production.\n"
            "  Generate a random key: python -c \"import secrets; print(secrets.token_urlsafe(48))\"\n"
            "  Add to backend/.env: SECRET_KEY=<your-generated-key>\n"
            "  Set APP_ENV=production when deploying."
        )

    if _IS_DEFAULT_INVITE:
        _warnings.append(
            "INVITE_CODE is using the default value ('dev-invite'). "
            "Anyone who knows this can register. "
            "Set a unique INVITE_CODE in backend/.env for production."
        )

    # CORS: warn if using wildcard (dev convenience)
    if not _RAW_CORS.strip() or CORS_ORIGINS == ["*"]:
        _warnings.append(
            "CORS_ORIGINS is not set (allowing all origins). "
            "This is fine for local development. "
            "For production, set CORS_ORIGINS to your real frontend domain(s)."
        )

    for msg in _warnings:
        logger.warning(msg)
        warnings.warn(msg)

# CORS — origins read from config (env CORS_ORIGINS, fallback ["*"])
# When origins is a wildcard, credentials MUST be disabled — browsers
# reject credentialed requests paired with Access-Control-Allow-Origin: *.
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=not CORS_IS_WILDCARD,
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
