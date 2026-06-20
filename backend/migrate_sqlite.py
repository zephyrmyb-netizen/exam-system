"""
Development migration script for SQLite database.

Usage:
    cd "D:\File\exam system"
    backend\.venv\Scripts\python.exe backend\migrate_sqlite.py

What it does:
1. Backs up backend/exam_system.db to backend/exam_system.backup-<timestamp>.db
2. Adds missing columns to the questions table if needed
3. Creates the question_banks table if missing
4. Creates the practice_records table if missing
5. Creates the user_question_reviews table if missing
6. Assigns old questions (with NULL owner_id) to an "旧数据" default bank
7. Reports what was changed
"""

import os
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "exam_system.db"


def main():
    if not DB_PATH.exists():
        print(f"[ERROR] Database not found: {DB_PATH}")
        print("Nothing to migrate. The backend will create a fresh DB on startup.")
        return

    # ── 1. Backup ───────────────────────────────────────────────────────
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = DB_PATH.parent / f"exam_system.backup-{timestamp}.db"
    shutil.copy2(DB_PATH, backup_path)
    print(f"[INFO] Backup created: {backup_path}")

    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()

    try:
        # ── 2. Detect current questions columns ─────────────────────────
        cur.execute("PRAGMA table_info(questions)")
        existing_cols = {r[1] for r in cur.fetchall()}
        print(f"[INFO] Existing questions columns: {sorted(existing_cols)}")

        needed_cols = {
            "owner_id": "INTEGER REFERENCES users(id) ON DELETE SET NULL",
            "course_id": "INTEGER REFERENCES question_banks(id) ON DELETE SET NULL",
            "visibility": "TEXT NOT NULL DEFAULT 'private'",
            "source": "TEXT NOT NULL DEFAULT 'import'",
            "created_at": "TEXT",  # SQLite ALTER can't use non-constant default; backfill later
        }

        added = []
        for col_name, col_def in needed_cols.items():
            if col_name not in existing_cols:
                try:
                    cur.execute(f"ALTER TABLE questions ADD COLUMN {col_name} {col_def}")
                    conn.commit()
                    added.append(col_name)
                    print(f"[INFO] Added column: questions.{col_name}")
                except sqlite3.OperationalError as e:
                    print(f"[WARN] Failed to add column {col_name}: {e}")

        if not added:
            print("[INFO] questions table already has all required columns.")
        else:
            added_str = ", ".join(added)
            print(f"[INFO] Added {len(added)} columns to questions: {added_str}")

        # ── 3. Create question_banks table if missing ───────────────────
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='question_banks'")
        if not cur.fetchone():
            cur.execute("""
                CREATE TABLE question_banks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    owner_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    name VARCHAR(200) NOT NULL,
                    description TEXT DEFAULT '',
                    subject VARCHAR(200) DEFAULT '',
                    visibility VARCHAR(20) NOT NULL DEFAULT 'private',
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("""
                CREATE INDEX ix_question_banks_owner_id ON question_banks(owner_id)
            """)
            cur.execute("""
                CREATE INDEX ix_question_banks_visibility ON question_banks(visibility)
            """)
            conn.commit()
            print("[INFO] Created question_banks table (was missing).")
        else:
            print("[INFO] question_banks table already exists.")

        # ── 4. Create practice_records table if missing ─────────────────
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='practice_records'")
        if not cur.fetchone():
            cur.execute("""
                CREATE TABLE practice_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    question_id INTEGER REFERENCES questions(id) ON DELETE SET NULL,
                    course_id INTEGER REFERENCES question_banks(id) ON DELETE SET NULL,
                    question_type VARCHAR(50),
                    is_correct INTEGER NOT NULL DEFAULT 0,
                    user_answer VARCHAR(500) DEFAULT '',
                    correct_answer VARCHAR(500) DEFAULT '',
                    answered_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("""
                CREATE INDEX ix_practice_records_user_id ON practice_records(user_id)
            """)
            cur.execute("""
                CREATE INDEX ix_practice_records_question_id ON practice_records(question_id)
            """)
            conn.commit()
            print("[INFO] Created practice_records table (was missing).")
        else:
            print("[INFO] practice_records table already exists.")

        # ── 5. Create user_question_reviews table if missing ─────────────
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_question_reviews'")
        if not cur.fetchone():
            cur.execute("""
                CREATE TABLE user_question_reviews (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    question_id INTEGER REFERENCES questions(id) ON DELETE SET NULL,
                    course_id INTEGER REFERENCES question_banks(id) ON DELETE SET NULL,
                    last_reviewed_at DATETIME,
                    next_review_at DATETIME,
                    review_level INTEGER NOT NULL DEFAULT 0,
                    review_mode VARCHAR(20) DEFAULT '',
                    consecutive_correct INTEGER NOT NULL DEFAULT 0,
                    consecutive_wrong INTEGER NOT NULL DEFAULT 0,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cur.execute("""
                CREATE INDEX ix_user_question_reviews_user_id ON user_question_reviews(user_id)
            """)
            cur.execute("""
                CREATE INDEX ix_user_question_reviews_question_id ON user_question_reviews(question_id)
            """)
            cur.execute("""
                CREATE INDEX ix_user_question_reviews_next_review_at ON user_question_reviews(next_review_at)
            """)
            conn.commit()
            print("[INFO] Created user_question_reviews table (was missing).")
        else:
            print("[INFO] user_question_reviews table already exists.")

        # ── 6. Handle old questions with NULL owner_id ─────────────────
        cur.execute("SELECT COUNT(*) FROM questions WHERE owner_id IS NULL")
        unowned = cur.fetchone()[0]
        print(f"[INFO] Questions without owner_id: {unowned}")

        if unowned > 0:
            # Find the first user to assign ownership
            cur.execute("SELECT id, username FROM users ORDER BY id LIMIT 1")
            first_user = cur.fetchone()

            if first_user:
                uid, uname = first_user
                # Create a "旧数据" bank if it doesn't exist
                cur.execute(
                    "SELECT id FROM question_banks WHERE owner_id=? AND name='旧数据' LIMIT 1",
                    (uid,),
                )
                row = cur.fetchone()
                if row:
                    bank_id = row[0]
                else:
                    now = datetime.now(timezone.utc).isoformat()
                    cur.execute(
                        "INSERT INTO question_banks (owner_id, name, description, visibility, created_at) "
                        "VALUES (?, '旧数据', '升级前导入的旧题目', 'private', ?)",
                        (uid, now),
                    )
                    bank_id = cur.lastrowid
                    conn.commit()
                    print(f"[INFO] Created '旧数据' question bank (id={bank_id}) for user '{uname}'")

                # Update old questions: assign owner, course, and fill defaults
                # (don't include created_at yet — SQLite ALTER can't have non-constant default)
                cur.execute(
                    "UPDATE questions SET "
                    "owner_id=?, "
                    "course_id=?, "
                    "visibility='private', "
                    "source='import' "
                    "WHERE owner_id IS NULL",
                    (uid, bank_id),
                )
                # Backfill created_at for these rows
                cur.execute(
                    "UPDATE questions SET created_at=? WHERE created_at IS NULL",
                    (now,),
                )
                conn.commit()
                print(f"[INFO] Assigned {unowned} old questions to user '{uname}' (id={uid}), bank '旧数据' (id={bank_id})")
            else:
                print("[WARN] No user exists. Old questions will remain with NULL owner_id.")
                print("       They will be visible to all users until they are assigned.")
        else:
            print("[INFO] All questions have owner_id — nothing to backfill.")

        # ── 7. Verify final state ─────────────────────────────────────
        print("\n=== Migration Summary ===")
        cur.execute("PRAGMA table_info(questions)")
        final_cols = [r[1] for r in cur.fetchall()]
        print(f"questions columns ({len(final_cols)}): {final_cols}")

        cur.execute("SELECT COUNT(*) FROM questions")
        print(f"questions rows: {cur.fetchone()[0]}")

        cur.execute("SELECT COUNT(*) FROM question_banks")
        print(f"question_banks rows: {cur.fetchone()[0]}")

        cur.execute("SELECT COUNT(*) FROM practice_records")
        print(f"practice_records rows: {cur.fetchone()[0]}")

        cur.execute("SELECT COUNT(*) FROM user_question_reviews")
        print(f"user_question_reviews rows: {cur.fetchone()[0]}")

        cur.execute("SELECT COUNT(*) FROM questions WHERE owner_id IS NOT NULL")
        assigned = cur.fetchone()[0]
        print(f"questions with owner_id: {assigned}")

        print("\n[DONE] Migration completed successfully.")
        print(f"Backup saved to: {backup_path}")

    except Exception as e:
        print(f"\n[ERROR] Migration failed: {e}")
        print(f"Your original database is unchanged, backup is at: {backup_path}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
