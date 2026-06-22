from urllib.parse import urlparse

from fastapi import APIRouter

from ..config import (
    CHAT_UPSTREAM_TIMEOUT,
    DOTENV_LOADED,
    DOTENV_PATH,
    IMPORT_CHUNK_SIZE,
    IMPORT_MAX_CHUNKS,
    IMPORT_UPSTREAM_TIMEOUT,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OPENAI_MODEL,
    PRESERVE_SYSTEM_ENV,
)

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/health/ai")
def ai_health():
    parsed = urlparse(OPENAI_BASE_URL)
    return {
        "status": "configured" if bool(OPENAI_API_KEY) else "missing_api_key",
        "api_key_configured": bool(OPENAI_API_KEY),
        "base_url_host": parsed.netloc or OPENAI_BASE_URL,
        "model": OPENAI_MODEL,
        "chat_timeout_seconds": CHAT_UPSTREAM_TIMEOUT,
        "import_timeout_seconds": IMPORT_UPSTREAM_TIMEOUT,
        "import_chunk_size": IMPORT_CHUNK_SIZE,
        "import_max_chunks": IMPORT_MAX_CHUNKS,
        "dotenv_loaded": DOTENV_LOADED,
        "dotenv_path": DOTENV_PATH,
        "preserve_system_env": PRESERVE_SYSTEM_ENV,
    }
