# Database Migration Guide

> ⚠️ **安全提示**：迁移过程不涉及 API Key，但请确保 `backend/.env` 中的密钥不被提交到 Git（已在 `.gitignore` 中忽略）。详见根目录 [README.md](../README.md) 的安全检查清单。

## Why `create_all` Doesn't Fix Old Databases

`Base.metadata.create_all(bind=engine)` **creates tables that don't exist**, but it never modifies
existing tables. If `questions` already exists with 9 columns and your model now wants 14,
`create_all` does nothing — you get `no such column` errors at runtime.

The same applies to *new tables* if the database was created before the model existed:
`create_all` only creates the `practice_records` table on a **brand new** database file.
If the database file already exists, `create_all` skips it silently (because `users` already
exists and the engine considers the "schema" already set up).

**The solution:** run `migrate_sqlite.py` after any model change.

## Quick: Development Migration (Recommended)

```bash
cd "D:\File\exam system"
backend\.venv\Scripts\python.exe backend\migrate_sqlite.py
```

This script:
1. **Backs up** the database to `backend/xuexibao.backup-<timestamp>.db`
2. Adds missing columns to the `questions` table via `ALTER TABLE`
3. Creates the `question_banks` table if missing
4. Creates the `practice_records` table if missing
5. Creates the `user_question_reviews` table if missing
6. Assigns old questions (NULL owner_id) to the first user under a "旧数据" bank
7. Reports what was changed — what tables/columns were created, what data was backfilled

**Run this every time you modify `models.py` fields and want to keep your existing data.**

Phase 4 note: the script also creates the `tags` and `question_tags` tables when they are missing.

## Restoring From Backup

```bash
cd "D:\File\exam system"
copy backend\xuexibao.backup-<timestamp>.db backend\xuexibao.db
```

## Alternative: Full Rebuild (Wipes All Data)

If data isn't important during development:

```bash
cd "D:\File\exam system"
del backend\xuexibao.db
# Then restart the backend — it auto-creates a fresh DB with all models
# Daily use should not include --reload, so long AI imports are not interrupted
backend\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

This works because `create_all` runs on a file that doesn't exist yet, so SQLite creates a fresh
database and `create_all` builds every table from scratch with the latest column definitions.

## Formal: Alembic (Production)

For production environments, use [Alembic](https://alembic.sqlalchemy.org/) for versioned migrations:

### Install
```bash
pip install alembic
```

### Initialize
```bash
cd "D:\File\exam system"
alembic init backend\alembic
```

### Configure `backend\alembic.ini`
```ini
sqlalchemy.url = sqlite:///./backend/xuexibao.db
```

### Configure `backend\alembic\env.py`
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from backend.database import Base
import backend.models  # ensure all models are loaded
target_metadata = Base.metadata
```

### Generate and apply migrations
```bash
cd "D:\File\exam system"
alembic revision --autogenerate -m "add owner_id to questions"
alembic upgrade head
```

## Common Schema Changes

| Change Type | Development | Production |
|---|---|---|
| New table | `create_all` (only works on fresh DB!) or `migrate_sqlite.py` | `alembic --autogenerate` |
| New column (nullable) | `migrate_sqlite.py` | `alembic --autogenerate` |
| New column (NOT NULL) | `migrate_sqlite.py` + backfill | Two-step: add nullable → backfill data → add NOT NULL |
| Rename column | Rebuild DB | Manual alembic script with `ALTER COLUMN RENAME` |
| Delete column | Rebuild DB | Manual alembic script |

## When to Run Migration

After **any** change to `backend/models.py` that:
- Adds a new model class (e.g., `PracticeRecord`)
- Adds/modifies/removes column definitions on an existing model
- Changes relationships between models

**Symptom:** backend returns 500 errors with `no such table` or `no such column` in the logs.

**Fix:** run `migrate_sqlite.py` — it's idempotent, so running it again is harmless.

## Production Deployment Checklist

Before deploying to production, ensure these environment variables are set in `backend/.env`:

```env
APP_ENV=production
SECRET_KEY=<your-random-secret>
CORS_ORIGINS=<your-frontend-origin>
```

### SECRET_KEY

Generate a cryptographically secure random key:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Copy the output and set it as `SECRET_KEY` in `backend/.env`. If `APP_ENV=production` and `SECRET_KEY` is missing or still uses the default value, the backend **refuses to start** with a clear error message.

> ⚠️ **Never commit `backend/.env` to Git** — it is already listed in `.gitignore`.
