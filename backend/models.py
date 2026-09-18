import json
import secrets
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(100), nullable=False, default="")
    is_guest = Column(Integer, nullable=False, default=0, index=True)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="SET NULL"), nullable=True, index=True)

    role_ref = relationship("Role", back_populates="users")
    question_banks = relationship("QuestionBank", back_populates="owner", cascade="all, delete-orphan")
    wrong_records = relationship("WrongRecord", back_populates="user", cascade="all, delete-orphan")
    practice_records = relationship("PracticeRecord", cascade="all, delete-orphan")
    question_reviews = relationship("UserQuestionReview", back_populates="user", cascade="all, delete-orphan")
    bookmarks = relationship("Bookmark", cascade="all, delete-orphan")
    feedback_entries = relationship("FeedbackEntry", back_populates="user", cascade="all, delete-orphan")
    study_goals = relationship("StudyGoal", cascade="all, delete-orphan")

    @property
    def role(self) -> str:
        """Public role name used by API schemas; missing roles behave as students."""
        if self.role_ref is None:
            return "student"
        return self.role_ref.name

    @property
    def permissions(self) -> list[str]:
        """Effective permission list for this user's role.

        Single source of truth is PermissionService.ROLE_PERMISSIONS, so the
        /auth/me payload and `require_permission` guards can never disagree.
        Imported lazily because permission_service imports this module.
        """
        from .services.permission_service import ROLE_PERMISSIONS

        return sorted(ROLE_PERMISSIONS.get(self.role, ROLE_PERMISSIONS["student"]))


class QuestionBank(Base):
    """A named collection of questions (a "course" or "question bank")."""

    __tablename__ = "question_banks"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True, default="")
    subject = Column(String(200), nullable=True, default="")
    visibility = Column(String(20), nullable=False, default="private", index=True)  # public / private
    share_token = Column(String(64), nullable=True, unique=True, index=True, default=lambda: secrets.token_urlsafe(32))
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))

    owner = relationship("User", back_populates="question_banks")
    questions = relationship("Question", back_populates="course", cascade="all, delete-orphan")


class CourseFavorite(Base):
    """A user's saved public question bank."""

    __tablename__ = "course_favorites"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("question_banks.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))

    __table_args__ = (UniqueConstraint("course_id", "user_id", name="uq_course_favorite_user"),)


class CourseReport(Base):
    """A report about a public question bank, reviewable by administrators."""

    __tablename__ = "course_reports"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("question_banks.id", ondelete="CASCADE"), nullable=False, index=True)
    reporter_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    reason = Column(String(80), nullable=False, default="other")
    detail = Column(Text, nullable=False, default="")
    status = Column(String(20), nullable=False, default="new", index=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))

    course = relationship("QuestionBank")
    reporter = relationship("User")




class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    course_id = Column(Integer, ForeignKey("question_banks.id", ondelete="SET NULL"), nullable=True, index=True)
    visibility = Column(String(20), nullable=False, default="private", index=True)  # public / private
    source = Column(String(20), nullable=False, default="import")  # import / manual
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))

    subject = Column(String(200), default="默认科目")
    chapter = Column(String(200), default="默认章节")
    type = Column(String(50), nullable=False)  # single_choice, multiple_choice, true_false, fill_blank, short_answer
    question = Column(Text, nullable=False)
    options = Column(Text, nullable=True)  # JSON string
    answer = Column(String(500), nullable=False)
    analysis = Column(Text, nullable=True, default="")
    image_urls = Column(Text, nullable=False, default="[]")
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

    def get_image_urls(self) -> list[str]:
        try:
            value = json.loads(self.image_urls or "[]")
        except (json.JSONDecodeError, TypeError):
            return []
        return [item for item in value if isinstance(item, str)] if isinstance(value, list) else []

    def set_image_urls(self, image_urls: list[str] | None) -> None:
        self.image_urls = json.dumps([item for item in (image_urls or []) if isinstance(item, str)], ensure_ascii=False)


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
    question_type = Column(
        String(50), nullable=True
    )  # single_choice, multiple_choice, true_false, fill_blank, short_answer
    is_correct = Column(Integer, nullable=False, default=0)  # 0=False, 1=True
    user_answer = Column(String(500), nullable=True, default="")
    correct_answer = Column(String(500), nullable=True, default="")
    client_submission_id = Column(String(64), nullable=True)
    answered_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))

    __table_args__ = (
        UniqueConstraint("user_id", "client_submission_id", name="uq_practice_records_user_submission"),
    )

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

    __table_args__ = (UniqueConstraint("user_id", "question_id", name="uq_user_question_review"),)

    last_reviewed_at = Column(DateTime, nullable=True)
    next_review_at = Column(DateTime, nullable=True, index=True)
    review_level = Column(Integer, nullable=False, default=0)  # 0=not started, 1-5 mastery levels
    review_mode = Column(String(20), nullable=True, default="")  # wrong_review / spaced_repeat / suggested
    consecutive_correct = Column(Integer, nullable=False, default=0)
    consecutive_wrong = Column(Integer, nullable=False, default=0)
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))

    user = relationship("User", back_populates="question_reviews")
    question = relationship("Question")


class Role(Base):
    """User role for future RBAC flows."""

    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True)

    users = relationship("User", back_populates="role_ref")


class Exam(Base):
    """Formal exam container planned for the exam mode."""

    __tablename__ = "exams"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True, default="")
    course_id = Column(Integer, ForeignKey("question_banks.id", ondelete="CASCADE"), nullable=False, index=True)
    creator_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    time_limit = Column(Integer, nullable=False, default=60)
    total_score = Column(Integer, nullable=False, default=100)
    is_shuffle = Column(Integer, nullable=False, default=0)
    is_blind = Column(Integer, nullable=False, default=1)
    status = Column(String(20), nullable=False, default="draft", index=True)
    share_code = Column(String(16), nullable=True, unique=True, index=True)
    start_at = Column(DateTime, nullable=True, index=True)
    end_at = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))

    course = relationship("QuestionBank")
    creator = relationship("User")
    questions = relationship("ExamQuestion", back_populates="exam", cascade="all, delete-orphan")
    submissions = relationship("ExamSubmission", back_populates="exam", cascade="all, delete-orphan")


class ExamQuestion(Base):
    """Question selected into an exam with scoring metadata."""

    __tablename__ = "exam_questions"

    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True)
    score = Column(Integer, nullable=False, default=1)
    order_index = Column(Integer, nullable=False, default=0)

    exam = relationship("Exam", back_populates="questions")
    question = relationship("Question")


class ExamSubmission(Base):
    """A user's submitted exam answers and score."""

    __tablename__ = "exam_submissions"

    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    started_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))
    submitted_at = Column(DateTime, nullable=True)
    score = Column(Integer, nullable=True)
    is_passed = Column(Integer, nullable=False, default=0)
    answers = Column(Text, nullable=True)

    exam = relationship("Exam", back_populates="submissions")
    user = relationship("User")


class Collaboration(Base):
    """User collaboration permission on a question bank."""

    __tablename__ = "collaborations"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("question_banks.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False, default="viewer")
    invited_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))

    __table_args__ = (UniqueConstraint("course_id", "user_id", name="uq_course_user_collab"),)

    course = relationship("QuestionBank")
    user = relationship("User", foreign_keys=[user_id])
    inviter = relationship("User", foreign_keys=[invited_by])


class StudyGroup(Base):
    __tablename__ = "study_groups"
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    invite_code = Column(String(16), nullable=False, unique=True, index=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))


class StudyGroupMember(Base):
    __tablename__ = "study_group_members"
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("study_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    joined_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))
    __table_args__ = (UniqueConstraint("group_id", "user_id", name="uq_study_group_member"),)


class StudyGroupCourse(Base):
    __tablename__ = "study_group_courses"
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("study_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    course_id = Column(Integer, ForeignKey("question_banks.id", ondelete="CASCADE"), nullable=False, index=True)
    __table_args__ = (UniqueConstraint("group_id", "course_id", name="uq_study_group_course"),)


class StudyGroupExam(Base):
    __tablename__ = "study_group_exams"
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("study_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id", ondelete="CASCADE"), nullable=False, index=True)
    __table_args__ = (UniqueConstraint("group_id", "exam_id", name="uq_study_group_exam"),)


class Tag(Base):
    """Knowledge-point tag with optional hierarchy."""

    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    color = Column(String(20), nullable=True, default="")
    parent_id = Column(Integer, ForeignKey("tags.id", ondelete="CASCADE"), nullable=True, index=True)

    parent = relationship("Tag", remote_side=[id], backref="children")


class QuestionTag(Base):
    """Many-to-many relation between questions and knowledge tags."""

    __tablename__ = "question_tags"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True)
    tag_id = Column(Integer, ForeignKey("tags.id", ondelete="CASCADE"), nullable=False, index=True)

    __table_args__ = (UniqueConstraint("question_id", "tag_id", name="uq_question_tag"),)

    question = relationship("Question")
    tag = relationship("Tag")


class Bookmark(Base):
    """A user's bookmarked question."""

    __tablename__ = "bookmarks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True)
    folder_name = Column(String(100), nullable=True, default="默认收藏")
    note = Column(Text, nullable=True, default="")
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))

    __table_args__ = (UniqueConstraint("user_id", "question_id", name="uq_user_question_bookmark"),)

    user = relationship("User", back_populates="bookmarks")
    question = relationship("Question")


class FeedbackEntry(Base):
    """A help or product-feedback message submitted by an authenticated user."""

    __tablename__ = "feedback_entries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    category = Column(String(32), nullable=False, default="suggestion")
    content = Column(Text, nullable=False)
    contact = Column(String(120), nullable=False, default="")
    status = Column(String(20), nullable=False, default="new", index=True)
    admin_reply = Column(Text, nullable=False, default="")
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC), index=True)
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))

    user = relationship("User", back_populates="feedback_entries")


class StudyGoal(Base):
    """A user's study goal for later analytics and planning."""

    __tablename__ = "study_goals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    target_count = Column(Integer, nullable=False, default=10)
    deadline = Column(DateTime, nullable=True)
    progress = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))

    user = relationship("User", back_populates="study_goals")


class ImportTask(Base):
    """Durable AI import work item.

    A task stores only metadata and a temporary file path while parsing. The
    parsed preview is persisted so a user can leave the import view and later
    return to review or confirm the same result.
    """

    __tablename__ = "import_tasks"

    id = Column(String(36), primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="queued", index=True)
    source_filename = Column(String(255), nullable=False)
    file_path = Column(Text, nullable=True)
    course_id = Column(Integer, ForeignKey("question_banks.id", ondelete="SET NULL"), nullable=True)
    course_name = Column(String(200), nullable=False, default="")
    progress_current = Column(Integer, nullable=False, default=0)
    progress_total = Column(Integer, nullable=False, default=0)
    preview_questions_json = Column(Text, nullable=True, default="[]")
    warnings_json = Column(Text, nullable=True, default="[]")
    timing_json = Column(Text, nullable=True, default="{}")
    total_valid = Column(Integer, nullable=False, default=0)
    total_invalid = Column(Integer, nullable=False, default=0)
    error_message = Column(Text, nullable=True, default="")
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)

    owner = relationship("User")
    course = relationship("QuestionBank")
