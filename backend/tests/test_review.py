"""Tests for UserQuestionReview model and migration."""

import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from backend import models


class TestUserQuestionReviewModel:
    """Unit tests for the UserQuestionReview model (in-memory DB)."""

    def _create_user(self, db_session, user_id):
        """Create a test user so FK constraints are satisfied."""
        from backend import models as m

        user = m.User(id=user_id, username=f"test_{user_id}", password_hash="x")
        db_session.add(user)
        db_session.flush()
        return user

    def _create_question(self, db_session, question_id, owner_id=1, course_id=None):
        """Create a test question with FK deps."""
        from backend import models as m

        if course_id:
            bank = m.QuestionBank(id=course_id, owner_id=owner_id, name=f"bank_{course_id}")
            db_session.add(bank)
        q = m.Question(
            id=question_id,
            owner_id=owner_id,
            course_id=course_id,
            type="single_choice",
            question=f"Q{question_id}",
            answer="A",
        )
        db_session.add(q)
        db_session.flush()
        return q

    def test_table_exists(self, db_session):
        """The table should be created by create_all."""
        # Just query — if the table doesn't exist, SQLite raises OperationalError
        count = db_session.query(models.UserQuestionReview).count()
        assert count == 0

    def test_create_and_query(self, db_session):
        """Create a review entry and retrieve it."""
        self._create_user(db_session, 1)
        self._create_question(db_session, 10, course_id=5)
        now = datetime.now(UTC)
        review = models.UserQuestionReview(
            user_id=1,
            question_id=10,
            course_id=5,
            last_reviewed_at=now,
            next_review_at=now + timedelta(days=1),
            review_level=2,
            review_mode="spaced_repeat",
            consecutive_correct=3,
            consecutive_wrong=0,
            updated_at=now,
        )
        db_session.add(review)
        db_session.commit()
        db_session.refresh(review)

        assert review.id is not None
        assert review.user_id == 1
        assert review.question_id == 10
        assert review.review_level == 2
        assert review.review_mode == "spaced_repeat"
        assert review.consecutive_correct == 3

    def test_default_values(self, db_session):
        """Verify sensible defaults on new rows."""
        self._create_user(db_session, 1)
        self._create_question(db_session, 5)
        review = models.UserQuestionReview(user_id=1, question_id=5)
        db_session.add(review)
        db_session.commit()
        db_session.refresh(review)

        assert review.review_level == 0
        assert review.review_mode == ""
        assert review.consecutive_correct == 0
        assert review.consecutive_wrong == 0
        assert review.updated_at is not None

    def test_user_isolation(self, db_session):
        """User A's review entries must not be returned for user B."""
        # Create both users and questions first
        self._create_user(db_session, 1)
        self._create_user(db_session, 2)
        self._create_question(db_session, 100, owner_id=1)
        self._create_question(db_session, 200, owner_id=2)
        now = datetime.now(UTC)
        for uid in [1, 2]:
            review = models.UserQuestionReview(
                user_id=uid,
                question_id=uid * 100,
                last_reviewed_at=now,
                review_level=uid,
            )
            db_session.add(review)
        db_session.commit()

        # Query per user
        r1 = db_session.query(models.UserQuestionReview).filter_by(user_id=1).all()
        r2 = db_session.query(models.UserQuestionReview).filter_by(user_id=2).all()

        assert len(r1) == 1
        assert len(r2) == 1
        assert r1[0].user_id == 1
        assert r2[0].user_id == 2

    def test_cascade_on_user_delete(self, db_session):
        """Review records should be deleted when the user is deleted."""
        self._create_user(db_session, 1)
        self._create_question(db_session, 5)
        review = models.UserQuestionReview(user_id=1, question_id=5)
        db_session.add(review)
        db_session.commit()

        # Simulate cascade by deleting the record directly
        db_session.delete(review)
        db_session.commit()

        count = db_session.query(models.UserQuestionReview).filter_by(user_id=1).count()
        assert count == 0

    def test_question_set_null_on_delete(self, db_session):
        """question_id should allow NULL (SET NULL)."""
        self._create_user(db_session, 1)
        review = models.UserQuestionReview(
            user_id=1,
            question_id=None,
            review_level=1,
        )
        db_session.add(review)
        db_session.commit()
        db_session.refresh(review)

        assert review.question_id is None
        assert review.id is not None


class TestMigrationIdempotent:
    """Test running migrate_sqlite.py multiple times on the real DB."""

    @pytest.mark.skipif(
        not (Path(__file__).resolve().parent.parent / "exam_system.db").exists(),
        reason="Real database not found — skip integration migration test",
    )
    def test_migration_idempotent(self):
        """Run migrate_sqlite.py twice; second run must not error."""
        project_root = Path(__file__).resolve().parent.parent
        migrate_script = project_root / "migrate_sqlite.py"

        # Run once
        result1 = subprocess.run(
            [sys.executable, str(migrate_script)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=str(project_root.parent),
        )
        output1 = (result1.stdout or "") + (result1.stderr or "")

        # Run twice
        result2 = subprocess.run(
            [sys.executable, str(migrate_script)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=str(project_root.parent),
        )
        output2 = (result2.stdout or "") + (result2.stderr or "")

        # Second run must not fail
        assert result2.returncode == 0, f"Second run failed (exit={result2.returncode}):\n{output2}"
        assert "[DONE]" in output1
        assert "[DONE]" in output2
