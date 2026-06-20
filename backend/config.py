import os
import warnings
from pathlib import Path

from dotenv import load_dotenv

# Always load .env from the backend/ directory so CWD doesn't matter
_backend_dir = Path(__file__).resolve().parent
_dotenv_path = _backend_dir / ".env"
if os.getenv("SKIP_DOTENV", "").lower() not in {"1", "true", "yes"}:
    load_dotenv(_dotenv_path)

# ── Environment ─────────────────────────────────────────────────────────────
APP_ENV = os.getenv("APP_ENV", "").lower() or os.getenv("ENV", "").lower() or "development"
IS_PRODUCTION = APP_ENV == "production"

# ── Timezone ────────────────────────────────────────────────────────────────
# All "today" stats are computed in this timezone.  Default Asia/Shanghai.
APP_TIMEZONE = os.getenv("APP_TIMEZONE", "Asia/Shanghai")

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

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24h

# ── CORS ────────────────────────────────────────────────────────────────────
# Read comma-separated origins from env.  When unset / empty → ["*"] (dev).
# Set to e.g. "https://example.com" for production.
_RAW_CORS = os.getenv("CORS_ORIGINS", "")
if _RAW_CORS.strip():
    CORS_ORIGINS = [o.strip() for o in _RAW_CORS.split(",") if o.strip()]
else:
    CORS_ORIGINS = ["*"]

# ── Auth ────────────────────────────────────────────────────────────────────
_INVITE_CODE_ENV = os.getenv("INVITE_CODE", "")
INVITE_CODE = _INVITE_CODE_ENV if _INVITE_CODE_ENV else "dev-invite"
_IS_DEFAULT_INVITE = not _INVITE_CODE_ENV or _INVITE_CODE_ENV == "dev-invite"

# ── AI / Chat ───────────────────────────────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Chat rate limiting (per user, in-memory)
CHAT_RATE_LIMIT_PER_HOUR = int(os.getenv("CHAT_RATE_LIMIT_PER_HOUR", "20"))
CHAT_MAX_MESSAGE_LENGTH = int(os.getenv("CHAT_MAX_MESSAGE_LENGTH", "4000"))
CHAT_MAX_HISTORY_MESSAGES = int(os.getenv("CHAT_MAX_HISTORY_MESSAGES", "20"))
CHAT_MAX_HISTORY_TOTAL_LENGTH = int(os.getenv("CHAT_MAX_HISTORY_TOTAL_LENGTH", "20000"))
CHAT_UPSTREAM_TIMEOUT = float(os.getenv("CHAT_UPSTREAM_TIMEOUT", "30"))

# CORS safety: when origins is wildcard, credentials must be disabled
# (browsers reject credentialed requests with Access-Control-Allow-Origin: *)
CORS_IS_WILDCARD = CORS_ORIGINS == ["*"]

# ═══════════════════════════════════════════════════════════════════════════════
# Production safety checks — block startup if any required value is unset or
# still using its public default.  All checks are collected so the developer
# sees every issue in a single error instead of fixing one at a time.
# ═══════════════════════════════════════════════════════════════════════════════

if IS_PRODUCTION:
    _prod_errors = []

    # ── SECRET_KEY ─────────────────────────────────────────────────────────
    if _IS_DEFAULT_SECRET:
        _prod_errors.append(
            "SECRET_KEY is not set or still uses the default value "
            "('change-this-secret-key-in-production'). "
            "Set SECRET_KEY in backend/.env to a long random string. "
            'Generate one with: python -c "import secrets; print(secrets.token_urlsafe(48))"'
        )

    # ── INVITE_CODE ────────────────────────────────────────────────────────
    if _IS_DEFAULT_INVITE:
        _prod_errors.append(
            "INVITE_CODE is not set or still uses the default value ('dev-invite'). "
            "Set a unique invite code in backend/.env, e.g. INVITE_CODE=<your-private-code>"
        )

    # ── CORS_ORIGINS ───────────────────────────────────────────────────────
    _cors_bad = False
    _cors_reason = ""
    if not _RAW_CORS.strip():
        _cors_bad = True
        _cors_reason = "CORS_ORIGINS is empty"
    else:
        _origins = [o.strip() for o in _RAW_CORS.split(",") if o.strip()]
        if _origins == ["*"]:
            _cors_bad = True
            _cors_reason = "CORS_ORIGINS is set to '*'"
        elif any("localhost" in o.lower() or "127.0.0.1" in o for o in _origins):
            _cors_bad = True
            _cors_reason = "CORS_ORIGINS contains localhost or 127.0.0.1"

    if _cors_bad:
        _prod_errors.append(
            f"{_cors_reason}. "
            "In production you must set CORS_ORIGINS to your real frontend domain(s), "
            "e.g. CORS_ORIGINS=https://example.com"
        )

    if _prod_errors:
        raise RuntimeError(
            "Production configuration errors - fix the following in backend/.env:\n  - "
            + "\n  - ".join(_prod_errors)
        )
