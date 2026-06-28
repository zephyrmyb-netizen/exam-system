from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator

from .utils import VALID_QUESTION_TYPES, normalize_answer

# -- Shared question validators (mixin) ---------------------------------------


class QuestionValidatorMixin:
    """Shared validators for QuestionCreate and QuestionManualCreate."""

    @field_validator("question")
    @classmethod
    def question_not_empty(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("题目题干不能为空")
        return stripped

    @field_validator("type")
    @classmethod
    def type_must_be_valid(cls, v: str) -> str:
        if v not in VALID_QUESTION_TYPES:
            type_list = ", ".join(sorted(VALID_QUESTION_TYPES))
            raise ValueError(f"无效的题目类型 '{v}'，仅支持：{type_list}")
        return v

    @field_validator("options")
    @classmethod
    def options_required_for_choice(cls, v: dict | None, info):
        if info.data.get("type") in ("single_choice", "multiple_choice") and not v:
            raise ValueError("选择题（single_choice / multiple_choice）必须提供 options")
        return v

    @field_validator("answer")
    @classmethod
    def answer_not_empty(cls, v: str, info):
        stripped = v.strip()
        if not stripped:
            raise ValueError("答案不能为空")
        q_type = info.data.get("type", "")
        if q_type in VALID_QUESTION_TYPES:
            return normalize_answer(stripped, q_type)
        return stripped


# -- Auth -------------------------------------------------------------------


class UserCreate(BaseModel):
    username: str
    password: str
    invite_code: str


class UserOut(BaseModel):
    id: int
    username: str
    role: str = "student"
    permissions: list[str] = []

    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token: str  # duplicate for frontend compatibility
    token_type: str = "bearer"


# -- Question Bank / Course --------------------------------------------------


class CourseCreate(BaseModel):
    name: str
    description: str = ""
    subject: str = ""
    visibility: str = "private"


class CourseOut(BaseModel):
    id: int
    owner_id: int
    name: str
    description: str
    subject: str
    visibility: str
    created_at: str | None = None
    question_count: int = 0
    practice_count: int = 0
    last_practiced_at: str | None = None

    model_config = ConfigDict(from_attributes=True)


class CourseUpdate(BaseModel):
    """Fields allowed when editing a course."""

    name: str | None = None
    description: str | None = None
    subject: str | None = None


# -- Question ---------------------------------------------------------------


class QuestionCreate(QuestionValidatorMixin, BaseModel):
    subject: str = "默认科目"
    chapter: str = "默认章节"
    type: str  # single_choice, multiple_choice, true_false, fill_blank, short_answer
    question: str
    options: dict[str, Any] | None = None
    answer: str
    analysis: str = ""
    difficulty: str = "normal"
    course_id: int | None = None  # optional: add to a course


class QuestionManualCreate(QuestionValidatorMixin, BaseModel):
    """Manual single-question creation — course_id is required."""

    course_id: int
    subject: str = "默认科目"
    chapter: str = "默认章节"
    type: str  # single_choice, multiple_choice, true_false, fill_blank, short_answer
    question: str
    options: dict[str, Any] | None = None
    answer: str
    analysis: str = ""
    difficulty: str = "normal"


class QuestionUpdate(BaseModel):
    """Fields allowed when editing a question. All optional."""

    course_id: int | None = None
    subject: str | None = None
    chapter: str | None = None
    type: str | None = None
    question: str | None = None
    options: dict[str, Any] | None = None
    answer: str | None = None
    analysis: str | None = None
    difficulty: str | None = None

    @field_validator("type")
    @classmethod
    def type_must_be_valid_if_set(cls, v: str | None) -> str | None:
        if v is not None and v not in VALID_QUESTION_TYPES:
            type_list = ", ".join(sorted(VALID_QUESTION_TYPES))
            raise ValueError(f"无效的题目类型 '{v}'，仅支持：{type_list}")
        return v

    @field_validator("answer")
    @classmethod
    def answer_normalize_if_set(cls, v: str | None, info) -> str | None:
        if v is None:
            return v
        stripped = v.strip()
        if not stripped:
            raise ValueError("答案不能为空")
        q_type = info.data.get("type")
        if q_type and q_type in VALID_QUESTION_TYPES:
            return normalize_answer(stripped, q_type)
        return stripped


class QuestionOut(BaseModel):
    id: int
    owner_id: int | None = None
    course_id: int | None = None
    visibility: str = "private"
    source: str = "import"
    created_at: str | None = None
    subject: str
    chapter: str
    type: str
    question: str
    options: dict[str, Any] | None = None
    answer: str
    analysis: str
    difficulty: str

    model_config = ConfigDict(from_attributes=True)


class BatchImportResponse(BaseModel):
    imported_count: int
    course_id: int | None = None
    course_name: str = "未分类题库"


# -- Practice ---------------------------------------------------------------


class SubmitRequest(BaseModel):
    question_id: int
    user_answer: str


class SubmitResponse(BaseModel):
    is_correct: bool
    correct_answer: str
    analysis: str
    wrongbook_recorded: bool = False


# -- Wrong Book -------------------------------------------------------------


class WrongRecordOut(BaseModel):
    id: int
    question_id: int
    question: QuestionOut
    wrong_count: int
    last_wrong_answer: str

    model_config = ConfigDict(from_attributes=True)


# -- File Import ------------------------------------------------------------


class ImportTiming(BaseModel):
    """Safe performance summary for file import stages, in milliseconds."""

    extract_ms: int = 0
    chunk_ms: int = 0
    ai_ms: int = 0
    total_ms: int = 0
    chunks: int = 0
    ai_chunks: list[int] = []


class FileExtractResponse(BaseModel):
    text: str
    filename: str
    suggested_course_name: str = "未分类题库"
    timing: ImportTiming | None = None


class FileAutoResponse(BaseModel):
    imported_count: int
    course_id: int | None = None
    course_name: str = "未分类题库"
    timing: ImportTiming | None = None


class ImportedQuestion(BaseModel):
    """A single question as parsed by AI, used in preview and confirm flows."""

    type: str = "fill_blank"
    question: str = ""
    options: dict[str, Any] | None = None
    answer: str = ""
    analysis: str = ""
    subject: str = "默认科目"
    chapter: str = "默认章节"
    difficulty: str = "normal"
    line_number: int | None = None  # source position hint


class PreviewImportResponse(BaseModel):
    """Response from /imports/file/preview — no DB writes happened."""

    questions: list[ImportedQuestion] = []
    suggested_course_name: str = "未分类题库"
    warnings: list[str] = []
    total_parsed: int = 0
    total_valid: int = 0
    total_invalid: int = 0
    timing: ImportTiming | None = None


class ConfirmImportRequest(BaseModel):
    """User-edited questions ready for final import."""

    questions: list[ImportedQuestion]
    course_id: int | None = None
    course_name: str = ""


class ConfirmImportResponse(BaseModel):
    imported_count: int
    course_id: int | None = None
    course_name: str = "未分类题库"
    warnings: list[str] = []


# -- Practice Stats & History -----------------------------------------------


class PracticeStatsOut(BaseModel):
    today_count: int = 0
    total_count: int = 0
    correct_count: int = 0
    wrong_count: int = 0
    accuracy_rate: float = 0.0  # 0.0–1.0, 0 when no records
    recent_count_7d: int = 0


class PracticeRecordOut(BaseModel):
    id: int
    question_id: int | None = None
    course_id: int | None = None
    question_type: str | None = None
    question_text: str = ""  # 题干摘要
    is_correct: bool = False
    user_answer: str = ""
    correct_answer: str = ""
    answered_at: str | None = None

    model_config = ConfigDict(from_attributes=True)


class PracticeHistoryOut(BaseModel):
    """Paginated practice history response."""

    items: list[PracticeRecordOut] = []
    total: int = 0
    page: int = 1
    page_size: int = 20


# -- Exam --------------------------------------------------------------------


class ExamCreate(BaseModel):
    title: str
    course_id: int
    description: str = ""
    time_limit: int = 60
    total_score: int = 100
    is_shuffle: bool = False
    is_blind: bool = True
    question_ids: list[int] = []


class ExamOut(BaseModel):
    id: int
    title: str
    description: str = ""
    course_id: int
    creator_id: int
    time_limit: int = 60
    total_score: int = 100
    is_shuffle: bool = False
    is_blind: bool = True
    status: str = "draft"
    question_count: int = 0
    created_at: str | None = None


class ExamQuestionOut(BaseModel):
    id: int
    question_id: int
    question_type: str
    question: str
    options: dict[str, str] | None = None
    score: int = 1
    order_index: int = 0


class ExamDetailOut(ExamOut):
    questions: list[ExamQuestionOut] = []


class ExamAttemptOut(BaseModel):
    id: int
    exam_id: int
    user_id: int
    started_at: str | None = None
    submitted_at: str | None = None
    score: int | None = None


class ExamSubmissionCreate(BaseModel):
    answers: dict[str, str] = {}


class ExamResultOut(BaseModel):
    exam_id: int
    submission_id: int
    score: int = 0
    total_score: int = 0
    correct_count: int = 0
    wrong_count: int = 0
    accuracy_rate: float = 0.0
    submitted_at: str | None = None


class ExamListOut(BaseModel):
    items: list[ExamOut] = []
    total: int = 0
    page: int = 1
    page_size: int = 20


# -- Admin -------------------------------------------------------------------


class AdminUserOut(BaseModel):
    id: int
    username: str
    role: str = "student"


class AdminUserListOut(BaseModel):
    items: list[AdminUserOut] = []
    total: int = 0


class AdminRoleUpdate(BaseModel):
    role: str


class AdminStatsOut(BaseModel):
    user_count: int = 0
    course_count: int = 0
    question_count: int = 0
    exam_count: int = 0
    submission_count: int = 0


# -- Review & Insights ------------------------------------------------------


class WeakTypeOut(BaseModel):
    """A question type with elevated error rate."""

    question_type: str = ""
    total_attempts: int = 0
    wrong_attempts: int = 0
    error_rate: float = 0.0  # 0.0–1.0


class TodayReviewOut(BaseModel):
    """Today's review suggestion based on wrong records and practice history."""

    due_count: int = 0  # wrong questions not yet mastered
    wrong_count: int = 0  # total wrong records
    weak_types: list[WeakTypeOut] = []
    recommended_modes: list[str] = []  # e.g. ["wrong_review", "type_practice"]
