import json
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)

    question_banks = relationship("QuestionBank", back_populates="owner", cascade="all, delete-orphan")
    wrong_records = relationship("WrongRecord", back_populates="user", cascade="all, delete-orphan")
    practice_records = relationship("PracticeRecord", cascade="all, delete-orphan")
    question_reviews = relationship("UserQuestionReview", back_populates="user", cascade="all, delete-orphan")


class QuestionBank(Base):
    """A named collection of questions (a "course" or "question bank")."""

    __tablename__ = "question_banks"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True, default="")
    subject = Column(String(200), nullable=True, default="")
    visibility = Column(String(20), nullable=False, default="private", index=True)  # public / private
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    owner = relationship("User", back_populates="question_banks")
    questions = relationship("Question", back_populates="course", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "owner_id": self.owner_id,
            "name": self.name,
            "description": self.description or "",
            "subject": self.subject or "",
            "visibility": self.visibility,
            "question_count": len(self.questions) if self.questions else 0,
        "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    course_id = Column(Integer, ForeignKey("question_banks.id", ondelete="SET NULL"), nullable=True, index=True)
    visibility = Column(String(20), nullable=False, default="private", index=True)  # public / private
    source = Column(String(20), nullable=False, default="import")  # public / private / import / manual
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    subject = Column(String(200), default="默认科目")
    chapter = Column(String(200), default="默认章节")
    type = Column(String(50), nullable=False)  # single_choice, multiple_choice, true_false, fill_blank, short_answer
    question = Column(Text, nullable=False)
    options = Column(Text, nullable=True)  # JSON string
    answer = Column(String(500), nullable=False)
    analysis = Column(Text, nullable=True, default="")
    difficulty = Column(String(20), nullable=True, default="normal")

    course = relationship("QuestionBank", back_populates="questions")
    wrong_records = relationship("WrongRecord", back_populates="question", cascade="all, delete-orphan")

    def get_options_dict(self):
        if not self.options:
            return None
        try:
            return json.loads(self.options)
        except (json.JSONDecodeError, TypeError):
            return None

    def set_options_dict(self, options_dict):
        self.options = json.dumps(options_dict, ensure_ascii=False) if options_dict else None

    def to_dict(self):
        return {
            "id": self.id,
            "owner_id": self.owner_id,
            "course_id": self.course_id,
            "visibility": self.visibility,
            "source": self.source,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "subject": self.subject,
            "chapter": self.chapter,
            "type": self.type,
            "question": self.question,
            "options": self.get_options_dict(),
            "answer": self.answer,
            "analysis": self.analysis or "",
            "difficulty": self.difficulty or "normal",
        }


class WrongRecord(Base):
    __tablename__ = "wrong_records"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    wrong_count = Column(Integer, default=1, nullable=False)
    last_wrong_answer = Column(String(500), nullable=True, default="")

    question = relationship("Question", back_populates="wrong_records")
    user = relationship("User", back_populates="wrong_records")


class PracticeRecord(Base):
    """A single attempt at answering a question — correct or incorrect.

    Unlike WrongRecord (which aggregates repeated mistakes), this table
    records every attempt independently.
    """

    __tablename__ = "practice_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="SET NULL"), nullable=True, index=True)
    course_id = Column(Integer, ForeignKey("question_banks.id", ondelete="SET NULL"), nullable=True)
    question_type = Column(String(50), nullable=True)  # single_choice, multiple_choice, true_false, fill_blank, short_answer
    is_correct = Column(Integer, nullable=False, default=0)  # 0=False, 1=True
    user_answer = Column(String(500), nullable=True, default="")
    correct_answer = Column(String(500), nullable=True, default="")
    answered_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="practice_records")
    question = relationship("Question")


class UserQuestionReview(Base):
    """Per-user-per-question review state for spaced repetition and wrong-question review.

    Tracks when a question was last reviewed, when it should be reviewed next,
    and the user's performance streak for that question.
    """

    __tablename__ = "user_question_reviews"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="SET NULL"), nullable=True, index=True)
    course_id = Column(Integer, ForeignKey("question_banks.id", ondelete="SET NULL"), nullable=True)

    last_reviewed_at = Column(DateTime, nullable=True)
    next_review_at = Column(DateTime, nullable=True, index=True)
    review_level = Column(Integer, nullable=False, default=0)  # 0=not started, 1-5 mastery levels
    review_mode = Column(String(20), nullable=True, default="")  # wrong_review / spaced_repeat / suggested
    consecutive_correct = Column(Integer, nullable=False, default=0)
    consecutive_wrong = Column(Integer, nullable=False, default=0)
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="question_reviews")
    question = relationship("Question")

