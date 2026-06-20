import os
import warnings
from pathlib import Path

from dotenv import load_dotenv

# Always load .env from the backend/ directory so CWD doesn't matter
_backend_dir = Path(__file__).resolve().parent
_dotenv_path = _backend_dir / ".env"
load_dotenv(_dotenv_path)

# ── Environment ─────────────────────────────────────────────────────────────
APP_ENV = os.getenv("APP_ENV", "").lower() or os.getenv("ENV", "").lower() or "development"
IS_PRODUCTION = APP_ENV == "production"

# ── Database ────────────────────────────────────────────────────────────────
# Default to an absolute path so the DB always lands in backend/ regardless of CWD
_default_db_path = _backend_dir / "exam_system.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{_default_db_path.as_posix()}")

# ── JWT ─────────────────────────────────────────────────────────────────────
_DEFAULT_SECRET = "change-this-secret-key-in-production"
_SECRET_KEY_ENV = os.getenv("SECRET_KEY", "")

if not _SECRET_KEY_ENV:
    # SECRET_KEY not set at all — use default (dev) or empty (will fail in prod)
    SECRET_KEY = _DEFAULT_SECRET
    _IS_DEFAULT_SECRET = True
else:
    SECRET_KEY = _SECRET_KEY_ENV
    _IS_DEFAULT_SECRET = _SECRET_KEY_ENV == _DEFAULT_SECRET

if IS_PRODUCTION and _IS_DEFAULT_SECRET:
    raise RuntimeError(
        "Refusing to start: SECRET_KEY is not set or still uses the default value. "
        "Set the SECRET_KEY environment variable to a long random string in production. "
        'Generate one with: python -c "import secrets; print(secrets.token_urlsafe(48))"'
    )

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24h

# ── CORS ────────────────────────────────────────────────────────────────────
# Read comma-separated origins from env.  When unset / empty → ["*"] (dev).
# Set to e.g. "http://localhost:5173,http://192.168.1.8:5173" for production.
_raw_cors = os.getenv("CORS_ORIGINS", "")
if _raw_cors.strip():
    CORS_ORIGINS = [o.strip() for o in _raw_cors.split(",") if o.strip()]
else:
    CORS_ORIGINS = ["*"]

# ── Auth ────────────────────────────────────────────────────────────────────
INVITE_CODE = os.getenv("INVITE_CODE", "dev-invite")

# ── AI / Chat ───────────────────────────────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
