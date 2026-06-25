import os
import warnings
from pathlib import Path

from dotenv import dotenv_values

# ── Load .env ───────────────────────────────────────────────────────────────
_backend_dir = Path(__file__).resolve().parent
_dotenv_path = _backend_dir / ".env"
DOTENV_PATH = str(_dotenv_path)
DOTENV_LOADED = False
PRESERVE_SYSTEM_ENV = os.getenv("PRESERVE_SYSTEM_ENV", "").lower() in {"1", "true", "yes"}


def _load_dotenv_values(path: Path) -> dict[str, str | None]:
    """Read .env file at *path*, returning a dict of variable → value.

    Uses utf-8-sig encoding so UTF-8 files with or without BOM work.
    Returns an empty dict if the file is missing or unreadable.
    """
    try:
        return dotenv_values(path, encoding="utf-8-sig") or {}
    except Exception:
        return {}


def _apply_env_values(values: dict[str, str | None], preserve_existing: bool | None = None) -> None:
    """Apply dotenv values to os.environ.

    By default, project .env values are authoritative for this local app. This
    prevents stale Windows user/system environment variables from breaking AI
    after a reboot. Set PRESERVE_SYSTEM_ENV=1 only when a deployment platform
    must override .env values.
    """
    if preserve_existing is None:
        preserve_existing = PRESERVE_SYSTEM_ENV

    # Defaults that config.py itself would use when the variable is absent.
    # Matching these in os.environ likely means a previous run leaked its
    # fallback value, not a deliberate system setting.
    _APP_DEFAULTS = {
        "INVITE_CODE": "dev-invite",
        "SECRET_KEY": "change-this-secret-key-in-production",
        "OPENAI_BASE_URL": "https://api.openai.com/v1",
        "OPENAI_MODEL": "gpt-4o-mini",
        "APP_ENV": "development",
        "APP_TIMEZONE": "Asia/Shanghai",
        "ACCESS_TOKEN_EXPIRE_MINUTES": "1440",
        "CHAT_RATE_LIMIT_PER_HOUR": "20",
        "CHAT_MAX_MESSAGE_LENGTH": "4000",
        "CHAT_MAX_HISTORY_MESSAGES": "20",
        "CHAT_MAX_HISTORY_TOTAL_LENGTH": "20000",
        "CHAT_UPSTREAM_TIMEOUT": "30",
        "IMPORT_UPSTREAM_TIMEOUT": "90",
        "IMPORT_CHUNK_SIZE": "5000",
        "IMPORT_MAX_CHUNKS": "3",
        "IMPORT_RATE_LIMIT_PER_HOUR": "10",
        "REDIS_URL": "",
    }

    for key, value in values.items():
        if value is None:
            continue
        existing = os.environ.get(key)
        if not preserve_existing:
            os.environ[key] = value
        elif existing is None or existing == "":
            os.environ[key] = value
        elif key in _APP_DEFAULTS and existing == _APP_DEFAULTS[key]:
            # Stale app default from a previous run — let .env override it
            os.environ[key] = value


if os.getenv("SKIP_DOTENV", "").lower() not in {"1", "true", "yes"}:
    _dotenv_values = _load_dotenv_values(_dotenv_path)
    DOTENV_LOADED = bool(_dotenv_values)
    _apply_env_values(_dotenv_values)

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

# Chat rate limiting (per user). The backend is Redis-backed when REDIS_URL is
# set, otherwise an in-memory fixed-window limiter is used (accurate only
# within a single worker process).
CHAT_RATE_LIMIT_PER_HOUR = int(os.getenv("CHAT_RATE_LIMIT_PER_HOUR", "20"))
CHAT_MAX_MESSAGE_LENGTH = int(os.getenv("CHAT_MAX_MESSAGE_LENGTH", "4000"))
CHAT_MAX_HISTORY_MESSAGES = int(os.getenv("CHAT_MAX_HISTORY_MESSAGES", "20"))
CHAT_MAX_HISTORY_TOTAL_LENGTH = int(os.getenv("CHAT_MAX_HISTORY_TOTAL_LENGTH", "20000"))
CHAT_UPSTREAM_TIMEOUT = float(os.getenv("CHAT_UPSTREAM_TIMEOUT", "90"))

# AI import is usually slower than chat because one file may need several
# sequential model calls. Keep these limits aligned with the frontend timeout.
IMPORT_UPSTREAM_TIMEOUT = float(os.getenv("IMPORT_UPSTREAM_TIMEOUT", "90"))
IMPORT_CHUNK_SIZE = int(os.getenv("IMPORT_CHUNK_SIZE", "5000"))
IMPORT_MAX_CHUNKS = int(os.getenv("IMPORT_MAX_CHUNKS", "3"))
# Per-user limit for AI import calls (each call may cost several model requests).
IMPORT_RATE_LIMIT_PER_HOUR = int(os.getenv("IMPORT_RATE_LIMIT_PER_HOUR", "10"))

# ── Rate limiting backend ───────────────────────────────────────────────────
# When set, rate limits are enforced via Redis (accurate across workers and
# instances). When empty, an in-memory limiter is used (single-worker only).
REDIS_URL = os.getenv("REDIS_URL", "").strip()

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
