# Phase 2 — 架构升级 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Prerequisite:** Phase 1 (`docs/superpowers/plans/2026-06-27-phase1-code-quality.md`) fully merged — `GenericCRUD`/`apply_pagination` exist, imports 包已就位, Pinia 已引入, 路由已懒加载。

**Goal:** 将架构从"学生项目"升级为"生产级工程" —— 后端建立三层架构（api/services/repositories）+ 依赖注入，前端引入 shadcn-vue + Tailwind v4 + 完整 Pinia 体系，新增 Phase 3/4 所需的数据模型。

**Architecture:** 后端逐 router 迁移到三层架构，旧 CRUD 函数保留可用直到迁移完成；前端先搭 Tailwind/shadcn 基础设施再按页面迁移；数据模型通过 Alembic 增量 migration 添加。全程行为不变，300+ 后端测试 + 前端测试作为回归保护网。

**Tech Stack:** FastAPI / SQLAlchemy 2.0 / Alembic / pytest（后端）；Vue 3 / Tailwind v4 / shadcn-vue / Pinia / Vitest（前端）。

**Spec:** `docs/superpowers/specs/2026-06-27-major-refactor-design.md` §4

---

## 文件结构总览

### 后端新增 / 修改

| 文件 | 责任 | 操作 |
|---|---|---|
| `backend/repositories/__init__.py` | 包占位 | 新建 |
| `backend/repositories/base.py` | `BaseRepository`（基于 Phase 1 的 GenericCRUD） | 新建 |
| `backend/repositories/user_repo.py` | User 数据访问 | 新建 |
| `backend/repositories/course_repo.py` | QuestionBank 数据访问 | 新建 |
| `backend/repositories/question_repo.py` | Question 数据访问 | 新建 |
| `backend/repositories/practice_repo.py` | PracticeRecord / UserQuestionReview | 新建 |
| `backend/repositories/wrongbook_repo.py` | WrongRecord | 新建 |
| `backend/services/__init__.py` | 包占位 | 修改 |
| `backend/services/auth_service.py` | 认证业务逻辑 | 新建 |
| `backend/services/course_service.py` | 课程业务逻辑 + 编排 | 新建 |
| `backend/services/practice_service.py` | 练习业务逻辑 | 新建 |
| `backend/services/permission_service.py` | 角色权限（为 Phase 3 预铺路） | 新建 |
| `backend/api/__init__.py` | 包占位 | 新建 |
| `backend/api/deps.py` | 依赖注入工厂 | 新建 |
| `backend/api/courses.py` | 薄路由层（从 routers/ 迁移） | 新建 |
| `backend/models.py` | 新增 7 个模型 | 修改 |
| `backend/migrations/versions/0003_*.py` | 新模型 migration | 新建 |
| `backend/main.py` | 改为 include api/ 路由 | 修改 |

### 前端新增 / 修改

| 文件 | 责任 | 操作 |
|---|---|---|
| `frontend/package.json` | 加 tailwindcss / class-variance-authority / clsx / tailwind-merge | 修改 |
| `frontend/tailwind.config.js` | Tailwind 配置 + 主题映射 | 新建 |
| `frontend/src/styles/tokens.css` | 设计 token（迁移自 style.css :root） | 新建 |
| `frontend/src/lib/utils.ts` | `cn()` class 合并工具 | 新建 |
| `frontend/src/components/ui/*` | shadcn-vue 基础组件 | 新建 |
| `frontend/src/stores/course.ts` | 课程 store + 缓存 | 新建 |
| `frontend/src/stores/theme.ts` | 暗色模式 | 新建 |
| `frontend/src/stores/ui.ts` | 侧边栏/UI 状态 | 新建 |
| `frontend/src/views/auth/LoginView.vue` | 迁移到 shadcn-vue | 修改 |
| `frontend/src/layouts/AppLayout.vue` | 迁移到 shadcn-vue Sidebar | 修改 |

---

## 执行顺序

分 5 个里程碑（M1–M5）。

- **M1（后端模型）**: Task 1–2 — 7 个新模型 + Alembic migration
- **M2（后端三层架构）**: Task 3–6 — repositories + services + api + deps + 逐 router 迁移
- **M3（前端 Tailwind 基石）**: Task 7–9 — Tailwind v4 + shadcn-vue 基础组件 + token
- **M4（前端 store 完善）**: Task 10–12 — course/theme/ui store + 暗色模式
- **M5（前端页面迁移 + 规范工具链）**: Task 13–16 — 5 核心页面迁移 + ESLint/Ruff + Docker 优化

---

# 里程碑 M1：后端 — 新增数据模型

## Task 1: 新增 7 个数据模型

**Files:**
- Modify: `backend/models.py`
- Test: `backend/tests/test_models_new.py`

- [ ] **Step 1: 写模型测试**

Create `backend/tests/test_models_new.py`:

```python
"""Tests for the Phase 2 models (Exam, Role, Collaboration, etc.)."""
from datetime import datetime, timezone

from backend import models


class TestRoleModel:
    def test_role_has_name_field(self):
        assert hasattr(models.Role, "name")

    def test_role_can_be_instantiated(self):
        role = models.Role(name="teacher")
        assert role.name == "teacher"


class TestExamModel:
    def test_exam_has_required_fields(self):
        assert hasattr(models.Exam, "title")
        assert hasattr(models.Exam, "course_id")
        assert hasattr(models.Exam, "time_limit")
        assert hasattr(models.Exam, "status")

    def test_exam_default_status_is_draft(self):
        exam = models.Exam(
            title="t", course_id=1, creator_id=1, time_limit=60, total_score=100,
        )
        # 默认状态通过 Column default 设置，实例化后未 flush 前可能为 None；
        # 检查 Column 定义本身
        col = models.Exam.__table__.c.status
        assert col.default.arg == "draft"


class TestExamSubmissionModel:
    def test_submission_has_score_and_passed(self):
        assert hasattr(models.ExamSubmission, "score")
        assert hasattr(models.ExamSubmission, "is_passed")


class TestCollaborationModel:
    def test_collaboration_has_role_field(self):
        assert hasattr(models.Collaboration, "role")


class TestTagModel:
    def test_tag_supports_hierarchy(self):
        assert hasattr(models.Tag, "parent_id")

    def test_question_tag_is_association(self):
        assert hasattr(models.QuestionTag, "question_id")
        assert hasattr(models.QuestionTag, "tag_id")


class TestBookmarkModel:
    def test_bookmark_has_folder_name(self):
        assert hasattr(models.Bookmark, "folder_name")


class TestStudyGoalModel:
    def test_goal_has_target_and_deadline(self):
        assert hasattr(models.StudyGoal, "target_count")
        assert hasattr(models.StudyGoal, "deadline")
        assert hasattr(models.StudyGoal, "progress")
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd backend && python -m pytest tests/test_models_new.py -v`
Expected: FAIL — `AttributeError: module 'backend.models' has no attribute 'Role'`

- [ ] **Step 3: 在 models.py 末尾添加 7 个模型**

在 `backend/models.py` 末尾追加。先在 `User` 模型中添加 `role_id` 字段（为 Phase 3 权限预铺路，默认 NULL 不破坏现有数据）。

修改 `User` 类，在 `password_hash` 字段后添加：
```python
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="SET NULL"), nullable=True, index=True)
    role = relationship("Role", back_populates="users")
```
并在 `User` 的 relationships 区添加：
```python
    bookmarks = relationship("Bookmark", cascade="all, delete-orphan")
    study_goals = relationship("StudyGoal", cascade="all, delete-orphan")
```

在文件末尾追加新模型（在 `UserQuestionReview` 之后）：

```python
class Role(Base):
    """User role for RBAC (Phase 3). admin / teacher / student."""
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True)

    users = relationship("User", back_populates="role")


class Exam(Base):
    """A formal exam created from a course's questions (Phase 3)."""
    __tablename__ = "exams"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True, default="")
    course_id = Column(Integer, ForeignKey("question_banks.id", ondelete="CASCADE"), nullable=False, index=True)
    creator_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    time_limit = Column(Integer, nullable=False, default=60)  # minutes
    total_score = Column(Integer, nullable=False, default=100)
    is_shuffle = Column(Integer, nullable=False, default=0)  # 0=no, 1=yes
    is_blind = Column(Integer, nullable=False, default=1)  # 0=can review, 1=blind
    status = Column(String(20), nullable=False, default="draft", index=True)  # draft/published/closed
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    questions = relationship("ExamQuestion", back_populates="exam", cascade="all, delete-orphan")
    submissions = relationship("ExamSubmission", back_populates="exam", cascade="all, delete-orphan")


class ExamQuestion(Base):
    """Association between an exam and its questions, with per-question score."""
    __tablename__ = "exam_questions"

    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True)
    score = Column(Integer, nullable=False, default=1)
    order_index = Column(Integer, nullable=False, default=0)

    exam = relationship("Exam", back_populates="questions")
    question = relationship("Question")


class ExamSubmission(Base):
    """A student's submission of an exam (Phase 3)."""
    __tablename__ = "exam_submissions"

    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    started_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    submitted_at = Column(DateTime, nullable=True)
    score = Column(Integer, nullable=True)
    is_passed = Column(Integer, nullable=False, default=0)  # 0/1
    answers = Column(Text, nullable=True)  # JSON string of {question_id: answer}

    exam = relationship("Exam", back_populates="submissions")


class Collaboration(Base):
    """Collaboration relation between a user and a course (Phase 3)."""
    __tablename__ = "collaborations"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("question_banks.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False, default="viewer")  # owner/editor/viewer
    invited_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("course_id", "user_id", name="uq_course_user_collab"),
    )


class Tag(Base):
    """Knowledge-point tag, supports hierarchy (Phase 4)."""
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    color = Column(String(20), nullable=True, default="")
    parent_id = Column(Integer, ForeignKey("tags.id", ondelete="CASCADE"), nullable=True, index=True)

    parent = relationship("Tag", remote_side=[id], backref="children")


class QuestionTag(Base):
    """Association between a question and a tag (Phase 4)."""
    __tablename__ = "question_tags"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True)
    tag_id = Column(Integer, ForeignKey("tags.id", ondelete="CASCADE"), nullable=False, index=True)

    __table_args__ = (
        UniqueConstraint("question_id", "tag_id", name="uq_question_tag"),
    )


class Bookmark(Base):
    """A user's bookmarked question, optionally in a folder (Phase 4)."""
    __tablename__ = "bookmarks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True)
    folder_name = Column(String(100), nullable=True, default="默认收藏")
    note = Column(Text, nullable=True, default="")
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("user_id", "question_id", name="uq_user_question_bookmark"),
    )


class StudyGoal(Base):
    """A user's study goal (Phase 4)."""
    __tablename__ = "study_goals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    target_count = Column(Integer, nullable=False, default=10)
    deadline = Column(DateTime, nullable=True)
    progress = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd backend && python -m pytest tests/test_models_new.py -v`
Expected: PASS

- [ ] **Step 5: 运行全量后端测试（注意：User 加了 role_id 字段，需确认无回归）**

Run: `cd backend && python -m pytest -q`
Expected: PASS。若失败，检查是否某处直接构造 User 时缺少字段（role_id 有 default/nullable，应无影响）。

- [ ] **Step 6: 提交**

```bash
git add backend/models.py backend/tests/test_models_new.py
git commit -m "feat(models): add Role, Exam, Collaboration, Tag, Bookmark, StudyGoal for Phase 3/4"
```

---

## Task 2: 创建 Alembic migration

**Files:**
- Create: `backend/migrations/versions/0003_add_phase2_models.py`

- [ ] **Step 1: 用 alembic 自动生成 migration（推荐方式）**

Run: `cd backend && python -m alembic revision --autogenerate -m "add phase2 models"`
Expected: 生成新的 migration 文件，类似 `0003_add_phase2_models.py`

- [ ] **Step 2: 检查生成的 migration**

打开生成的 migration 文件，确认 `upgrade()` 包含：
- 创建表：`roles`、`exams`、`exam_questions`、`exam_submissions`、`collaborations`、`tags`、`question_tags`、`bookmarks`、`study_goals`
- 在 `users` 表添加列：`role_id`（含外键）
- 所有外键约束、唯一约束

⚠️ **关键检查**：autogenerate 有时会遗漏或误判。逐一对照 `models.py` 中的 7 个新表 + 1 个新列，确保都在 upgrade() 中。

- [ ] **Step 3: 在 migration 的 upgrade() 开头添加 roles 种子数据**

在 `upgrade()` 函数末尾（创建表之后）添加默认角色数据：

```python
    # Seed default roles
    op.bulk_insert(sa.table('roles',
        sa.column('id', sa.Integer),
        sa.column('name', sa.String(50)),
    ), [
        {'id': 1, 'name': 'student'},
        {'id': 2, 'name': 'teacher'},
        {'id': 3, 'name': 'admin'},
    ])
```

- [ ] **Step 4: 在测试库上验证 migration 可执行**

先确认测试用 in-memory DB（conftest 用 `create_all`，不走 migration）。但需验证 migration 在真实 SQLite 上可跑：

Run: `cd backend && python -c "
from alembic.config import Config
from alembic import command
import tempfile, os
# 用临时 DB 验证
tmp = tempfile.mktemp(suffix='.db')
os.environ['DATABASE_URL'] = f'sqlite:///{tmp}'
cfg = Config('alembic.ini')
command.upgrade(cfg, 'head')
print('migration applied ok')
os.unlink(tmp)
"`
Expected: 输出 `migration applied ok`，无异常。

注意：`alembic.ini` 的 sqlalchemy.url 会被 env.py 用 `DATABASE_URL` 覆盖。若此命令报错，检查 env.py 读取 DATABASE_URL 的逻辑。

- [ ] **Step 5: 验证 downgrade 也可执行**

Run: `cd backend && python -c "
from alembic.config import Config
from alembic import command
import tempfile, os
tmp = tempfile.mktemp(suffix='.db')
os.environ['DATABASE_URL'] = f'sqlite:///{tmp}'
cfg = Config('alembic.ini')
command.upgrade(cfg, 'head')
command.downgrade(cfg, 'base')
print('downgrade ok')
os.unlink(tmp)
"`
Expected: 输出 `downgrade ok`

- [ ] **Step 6: 运行全量后端测试确认无回归**

Run: `cd backend && python -m pytest -q`
Expected: PASS

- [ ] **Step 7: 提交**

```bash
git add backend/migrations/versions/0003_*.py
git commit -m "feat(db): migration for Phase 2 models + default roles seed"
```

---

# 里程碑 M2：后端 — 三层架构

## Task 3: 创建 repositories 层

**Files:**
- Create: `backend/repositories/__init__.py`
- Create: `backend/repositories/base.py`
- Create: `backend/repositories/user_repo.py`
- Create: `backend/repositories/course_repo.py`
- Test: `backend/tests/repositories/test_course_repo.py`

- [ ] **Step 1: 写 course_repo 测试**

Create `backend/tests/repositories/__init__.py`（空文件）.

Create `backend/tests/repositories/test_course_repo.py`:

```python
from backend.repositories.course_repo import CourseRepository


class TestCourseRepository:
    def test_get_by_id_returns_bank(self, db_session, sample_bank):
        repo = CourseRepository(db_session)
        result = repo.get_by_id(sample_bank.id)
        assert result is not None
        assert result.id == sample_bank.id

    def test_get_by_id_returns_none_when_missing(self, db_session):
        repo = CourseRepository(db_session)
        assert repo.get_by_id(999999) is None

    def test_get_visible_banks_filters_private_for_other_user(self, db_session, sample_bank):
        repo = CourseRepository(db_session)
        # sample_bank is private, owned by user 1
        banks, total = repo.get_visible(user_id=999)
        assert sample_bank.id not in [b.id for b in banks]

    def test_get_owned_banks(self, db_session, sample_bank):
        repo = CourseRepository(db_session)
        banks, total = repo.get_owned(owner_id=sample_bank.owner_id)
        assert any(b.id == sample_bank.id for b in banks)
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd backend && python -m pytest tests/repositories/test_course_repo.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: 创建 base.py**

Create `backend/repositories/__init__.py`（空文件）.

Create `backend/repositories/base.py`:

```python
"""Base repository providing common data-access operations.

Wraps a SQLAlchemy session. Subclasses bind to a specific model and add
entity-specific queries. This is the data-access layer — no business logic.
"""
from __future__ import annotations

from typing import Any, Generic, Optional, Type, TypeVar

from sqlalchemy.orm import Session, Query

from ..crud_common import apply_pagination

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    model: Type[ModelType]

    def __init__(self, db: Session):
        self.db = db

    def _query(self) -> Query:
        return self.db.query(self.model)

    def get_by_id(self, id: int) -> Optional[ModelType]:
        return self._query().filter(self.model.id == id).first()

    def get_all(self) -> list[ModelType]:
        return self._query().all()

    def add(self, obj: ModelType) -> ModelType:
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete(self, obj: ModelType) -> None:
        self.db.delete(obj)
        self.db.commit()

    def paginate(self, query: Query, *, page: int = 0, page_size: int = 0):
        """Apply pagination to a query. Returns (items, total)."""
        return apply_pagination(query, page, page_size)
```

- [ ] **Step 4: 创建 course_repo.py**

Create `backend/repositories/course_repo.py`:

```python
"""Repository for QuestionBank (courses)."""
from typing import Optional

from sqlalchemy import or_
from sqlalchemy.orm import selectinload

from .. import models
from ..crud_common import _add_bank_visibility_filter
from .base import BaseRepository


class CourseRepository(BaseRepository[models.QuestionBank]):
    model = models.QuestionBank

    def get_visible(self, *, user_id: int | None, page: int = 0, page_size: int = 0):
        """Banks visible to the user (own private + all public)."""
        query = _add_bank_visibility_filter(self._query(), user_id)
        query = query.order_by(models.QuestionBank.created_at.desc())
        return self.paginate(query, page=page, page_size=page_size)

    def get_owned(self, *, owner_id: int, page: int = 0, page_size: int = 0):
        query = (
            self._query()
            .filter(models.QuestionBank.owner_id == owner_id)
            .options(selectinload(models.QuestionBank.questions))
            .order_by(models.QuestionBank.created_at.desc())
        )
        return self.paginate(query, page=page, page_size=page_size)

    def get_public(self, *, keyword: str = "", subject: str = "", page: int = 0, page_size: int = 0):
        query = self._query().filter(models.QuestionBank.visibility == "public")
        if keyword:
            like = f"%{keyword}%"
            query = query.filter(
                or_(
                    models.QuestionBank.name.like(like),
                    models.QuestionBank.description.like(like),
                    models.QuestionBank.subject.like(like),
                )
            )
        if subject:
            query = query.filter(models.QuestionBank.subject == subject)
        query = query.order_by(models.QuestionBank.created_at.desc())
        return self.paginate(query, page=page, page_size=page_size)

    def find_owned_by_name(self, owner_id: int, name: str) -> Optional[models.QuestionBank]:
        return (
            self._query()
            .filter(models.QuestionBank.owner_id == owner_id, models.QuestionBank.name == name)
            .first()
        )

    def update_visibility(self, bank_id: int, visibility: str) -> Optional[models.QuestionBank]:
        bank = self.get_by_id(bank_id)
        if bank is None:
            return None
        bank.visibility = visibility
        self.db.commit()
        self.db.refresh(bank)
        return bank
```

- [ ] **Step 5: 运行测试**

Run: `cd backend && python -m pytest tests/repositories/test_course_repo.py -v`
Expected: PASS

- [ ] **Step 6: 提交**

```bash
git add backend/repositories/ backend/tests/repositories/
git commit -m "feat(repos): add BaseRepository and CourseRepository"
```

---

## Task 4: 创建其余 repositories（user/question/practice/wrongbook）

**Files:**
- Create: `backend/repositories/user_repo.py`
- Create: `backend/repositories/question_repo.py`
- Create: `backend/repositories/practice_repo.py`
- Create: `backend/repositories/wrongbook_repo.py`
- Test: `backend/tests/repositories/test_question_repo.py`

- [ ] **Step 1: 写 question_repo 测试**

Create `backend/tests/repositories/test_question_repo.py`:

```python
from backend.repositories.question_repo import QuestionRepository


class TestQuestionRepository:
    def test_get_by_id_returns_question(self, db_session, sample_question):
        repo = QuestionRepository(db_session)
        result = repo.get_by_id(sample_question.id)
        assert result is not None
        assert result.id == sample_question.id

    def test_get_by_id_returns_none_when_missing(self, db_session):
        repo = QuestionRepository(db_session)
        assert repo.get_by_id(999999) is None
```

注意：`sample_question` fixture 若不存在，在 `conftest.py` 中添加（构造一个 Question，course_id 指向 sample_bank）。先 grep 确认：`grep -n "sample_question" backend/tests/conftest.py`。

- [ ] **Step 2: 运行测试确认失败**

Run: `cd backend && python -m pytest tests/repositories/test_question_repo.py -v`
Expected: FAIL

- [ ] **Step 3: 创建 user_repo.py**

Create `backend/repositories/user_repo.py`:

```python
"""Repository for User."""
from typing import Optional

from .. import models
from .base import BaseRepository


class UserRepository(BaseRepository[models.User]):
    model = models.User

    def get_by_username(self, username: str) -> Optional[models.User]:
        return self._query().filter(models.User.username == username).first()
```

- [ ] **Step 4: 创建 question_repo.py**

Create `backend/repositories/question_repo.py`:

```python
"""Repository for Question."""
from typing import Optional

from .. import models
from ..crud_common import _add_question_visibility_filter
from .base import BaseRepository


class QuestionRepository(BaseRepository[models.Question]):
    model = models.Question

    def get_visible(self, *, user_id: int | None, course_id: int | None = None,
                    page: int = 0, page_size: int = 0):
        query = _add_question_visibility_filter(self._query(), user_id)
        if course_id is not None:
            query = query.filter(models.Question.course_id == course_id)
        query = query.order_by(models.Question.created_at.desc())
        return self.paginate(query, page=page, page_size=page_size)

    def get_visible_by_id(self, question_id: int, user_id: int | None) -> Optional[models.Question]:
        q = self.get_by_id(question_id)
        if q is None:
            return None
        if q.visibility == "public" or q.owner_id == user_id or q.owner_id is None:
            return q
        return None
```

- [ ] **Step 5: 创建 practice_repo.py 和 wrongbook_repo.py**

Create `backend/repositories/practice_repo.py`:

```python
"""Repository for PracticeRecord and UserQuestionReview."""
from typing import Optional

from .. import models
from .base import BaseRepository


class PracticeRepository(BaseRepository[models.PracticeRecord]):
    model = models.PracticeRecord

    def get_by_user(self, user_id: int, *, page: int = 0, page_size: int = 0):
        query = self._query().filter(models.PracticeRecord.user_id == user_id)
        query = query.order_by(models.PracticeRecord.answered_at.desc())
        return self.paginate(query, page=page, page_size=page_size)


class ReviewRepository(BaseRepository[models.UserQuestionReview]):
    model = models.UserQuestionReview

    def get_by_user_question(self, user_id: int, question_id: int) -> Optional[models.UserQuestionReview]:
        return (
            self._query()
            .filter(
                models.UserQuestionReview.user_id == user_id,
                models.UserQuestionReview.question_id == question_id,
            )
            .first()
        )
```

Create `backend/repositories/wrongbook_repo.py`:

```python
"""Repository for WrongRecord."""
from typing import Optional

from .. import models
from .base import BaseRepository


class WrongRecordRepository(BaseRepository[models.WrongRecord]):
    model = models.WrongRecord

    def get_by_user_question(self, user_id: int, question_id: int) -> Optional[models.WrongRecord]:
        return (
            self._query()
            .filter(
                models.WrongRecord.user_id == user_id,
                models.WrongRecord.question_id == question_id,
            )
            .first()
        )

    def get_by_user(self, user_id: int, *, page: int = 0, page_size: int = 0):
        query = self._query().filter(models.WrongRecord.user_id == user_id)
        return self.paginate(query, page=page, page_size=page_size)
```

- [ ] **Step 6: 运行测试**

Run: `cd backend && python -m pytest tests/repositories/ -v`
Expected: PASS

- [ ] **Step 7: 运行全量后端测试**

Run: `cd backend && python -m pytest -q`
Expected: PASS

- [ ] **Step 8: 提交**

```bash
git add backend/repositories/ backend/tests/repositories/ backend/tests/conftest.py
git commit -m "feat(repos): add user, question, practice, wrongbook repositories"
```

---

## Task 5: 创建 service 层 + 依赖注入

**Files:**
- Create: `backend/services/course_service.py`
- Create: `backend/services/practice_service.py`
- Create: `backend/services/permission_service.py`
- Create: `backend/api/__init__.py`（空）
- Create: `backend/api/deps.py`
- Test: `backend/tests/services/test_course_service.py`

- [ ] **Step 1: 写 course_service 测试**

Create `backend/tests/services/__init__.py`（空文件）.

Create `backend/tests/services/test_course_service.py`:

```python
from backend.services.course_service import CourseService


class TestCourseService:
    def test_list_visible_courses(self, db_session, sample_bank):
        service = CourseService(db_session)
        items, total = service.list_visible(user_id=sample_bank.owner_id)
        assert total >= 1

    def test_get_course_owned(self, db_session, sample_bank):
        service = CourseService(db_session)
        bank = service.get_course_if_accessible(sample_bank.id, sample_bank.owner_id)
        assert bank is not None
        assert bank.id == sample_bank.id

    def test_get_course_inaccessible_returns_none(self, db_session, sample_bank):
        service = CourseService(db_session)
        # private bank, accessed by a different user
        bank = service.get_course_if_accessible(sample_bank.id, user_id=999)
        assert bank is None
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd backend && python -m pytest tests/services/test_course_service.py -v`
Expected: FAIL

- [ ] **Step 3: 创建 course_service.py**

Create `backend/services/course_service.py`:

```python
"""Business logic for courses (question banks).

Coordinates repositories and enforces access rules. No HTTP concerns here.
"""
from typing import Optional

from sqlalchemy.orm import Session

from .. import models, schemas
from ..repositories.course_repo import CourseRepository
from ..repositories.question_repo import QuestionRepository


class CourseService:
    def __init__(self, db: Session):
        self.db = db
        self.courses = CourseRepository(db)
        self.questions = QuestionRepository(db)

    def list_visible(self, *, user_id: int, page: int = 0, page_size: int = 0):
        return self.courses.get_visible(user_id=user_id, page=page, page_size=page_size)

    def list_owned(self, *, owner_id: int, page: int = 0, page_size: int = 0):
        return self.courses.get_owned(owner_id=owner_id, page=page, page_size=page_size)

    def get_course_if_accessible(
        self, course_id: int, user_id: int
    ) -> Optional[models.QuestionBank]:
        """Return the course if it exists and the user can access it."""
        bank = self.courses.get_by_id(course_id)
        if bank is None:
            return None
        if bank.visibility == "private" and bank.owner_id != user_id:
            return None
        return bank

    def get_course_if_owned(
        self, course_id: int, user_id: int
    ) -> Optional[models.QuestionBank]:
        bank = self.courses.get_by_id(course_id)
        if bank is None:
            return None
        if bank.owner_id != user_id:
            return None
        return bank

    def create_course(self, course_in: schemas.CourseCreate, owner_id: int) -> models.QuestionBank:
        from datetime import datetime, timezone
        bank = models.QuestionBank(
            owner_id=owner_id,
            name=course_in.name,
            description=course_in.description,
            subject=course_in.subject,
            visibility=course_in.visibility,
            created_at=datetime.now(timezone.utc),
        )
        return self.courses.add(bank)
```

- [ ] **Step 4: 创建 practice_service.py 和 permission_service.py**

Create `backend/services/practice_service.py`:

```python
"""Business logic for practice sessions and review state."""
from sqlalchemy.orm import Session

from ..repositories.practice_repo import PracticeRepository, ReviewRepository


class PracticeService:
    def __init__(self, db: Session):
        self.db = db
        self.records = PracticeRepository(db)
        self.reviews = ReviewRepository(db)
```

（Phase 2 只搭骨架 + 注入 repo；具体练习业务逻辑从 crud_practice.py 逐步迁入，可后续任务追加。本任务确保依赖注入链路通。）

Create `backend/services/permission_service.py`:

```python
"""Role-based permission checks (Phase 3 will expand this)."""
from sqlalchemy.orm import Session

from .. import models


class PermissionService:
    """Placeholder for Phase 3 RBAC. Exposes the permission constants now
    so routers can start referencing them."""

    # Permission constants (Phase 3 will enforce these)
    COURSE_CREATE = "course:create"
    COURSE_EDIT = "course:edit"
    COURSE_DELETE = "course:delete"
    EXAM_CREATE = "exam:create"
    EXAM_PUBLISH = "exam:publish"
    USER_MANAGE = "user:manage"

    def __init__(self, db: Session):
        self.db = db

    def get_role_name(self, user: models.User) -> str:
        """Return the user's role name, defaulting to 'student'."""
        if user.role is None:
            return "student"
        return user.role.name

    def can(self, user: models.User, permission: str) -> bool:
        """Check whether the user has a permission. Phase 2 stub: all
        authenticated users can do everything (preserves current behavior).
        Phase 3 will implement real checks."""
        return True
```

- [ ] **Step 5: 创建 api/deps.py（依赖注入工厂）**

Create `backend/api/__init__.py`（空文件）.

Create `backend/api/deps.py`:

```python
"""FastAPI dependency factories.

Routes depend on these to get wired-up services instead of constructing
repositories directly. This is the seam that makes the layered architecture
testable.
"""
from fastapi import Depends
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import User
from ..services.course_service import CourseService
from ..services.practice_service import PracticeService
from ..services.permission_service import PermissionService


def get_course_service(db: Session = Depends(get_db)) -> CourseService:
    return CourseService(db)


def get_practice_service(db: Session = Depends(get_db)) -> PracticeService:
    return PracticeService(db)


def get_permission_service(db: Session = Depends(get_db)) -> PermissionService:
    return PermissionService(db)
```

- [ ] **Step 6: 运行 service 测试**

Run: `cd backend && python -m pytest tests/services/test_course_service.py -v`
Expected: PASS

- [ ] **Step 7: 运行全量后端测试**

Run: `cd backend && python -m pytest -q`
Expected: PASS

- [ ] **Step 8: 提交**

```bash
git add backend/services/ backend/api/ backend/tests/services/
git commit -m "feat(services): add CourseService, PracticeService, PermissionService + DI deps"
```

---

## Task 6: 迁移 courses router 到三层架构（示范迁移，其余 router 留后续）

**Files:**
- Create: `backend/api/courses.py`（薄路由层）
- Modify: `backend/main.py`（include api 路由）

> **说明**：本任务示范如何把一个 router 迁移到三层架构。其余 router（auth/practice/wrongbook/questions/imports/library/chat）采用相同模式在后续迭代迁移，不在本 Phase 强制完成全部 —— 避免一次性大改引入风险。courses 是最典型的 CRUD router，作为样板。

- [ ] **Step 1: 先跑现有 courses 测试，确认基线**

Run: `cd backend && python -m pytest tests/test_courses.py -v`
Expected: PASS — 记录测试数

- [ ] **Step 2: 创建 api/courses.py 薄路由层**

Create `backend/api/courses.py`:

```python
"""Thin router layer for courses. Delegates all business logic to
CourseService. Only handles HTTP concerns (params, status codes, response
shape)."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import schemas
from ..auth import get_current_user
from ..database import get_db
from ..models import User
from ..services.course_service import CourseService
from .deps import get_course_service

router = APIRouter(prefix="/courses", tags=["courses"])


@router.get("/")
def list_courses(
    page: int = Query(0, ge=0),
    page_size: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    service: CourseService = Depends(get_course_service),
):
    banks, total = service.list_visible(user_id=current_user.id, page=page, page_size=page_size)
    items = [b.to_dict() for b in banks]
    if page <= 0 or page_size <= 0:
        return items
    return {"total": total, "page": page, "page_size": page_size, "items": items}


@router.get("/mine")
def list_my_courses(
    page: int = Query(0, ge=0),
    page_size: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    service: CourseService = Depends(get_course_service),
):
    banks, total = service.list_owned(owner_id=current_user.id, page=page, page_size=page_size)
    items = [b.to_dict() for b in banks]
    if page <= 0 or page_size <= 0:
        return items
    return {"total": total, "page": page, "page_size": page_size, "items": items}


@router.get("/{course_id}")
def get_course(
    course_id: int,
    current_user: User = Depends(get_current_user),
    service: CourseService = Depends(get_course_service),
):
    bank = service.get_course_if_accessible(course_id, current_user.id)
    if bank is None:
        raise HTTPException(status_code=404, detail="课程不存在")
    return bank.to_dict()
```

注意：本任务先迁移 3 个只读端点（list / mine / get）作为样板。写操作（create/update/delete/publish）保留在旧 `routers/courses.py` 不动，避免冲突。这意味着新旧 courses 路由会共存 —— **必须避免路由前缀冲突**。

- [ ] **Step 3: 处理路由冲突 —— 旧 router 暂时去掉已迁移的端点**

由于新旧都用 `prefix="/courses"`，会冲突。方案：**本 Phase 不实际切换 main.py 的 include**。api/courses.py 作为"已就绪但未挂载"的新代码，待所有端点迁移完后统一切换。

因此本任务：
- 创建 `api/courses.py`（完成）
- **不修改 main.py**
- 旧 `routers/courses.py` 保持不变，继续工作

这保证了零风险。完整切换留到所有 router 迁移完毕的后续 Phase。

- [ ] **Step 4: 写一个测试验证 api/courses.py 可独立工作（用 TestClient + 依赖覆盖）**

Create `backend/tests/api/__init__.py`（空）.

Create `backend/tests/api/test_courses_api.py`:

```python
"""Tests for the new layered api/courses.py router.

Mounted on a standalone app to avoid clashing with the legacy router.
"""
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.courses import router as courses_router
from backend.database import get_db


def _make_app(db_session):
    app = FastAPI()
    app.include_router(courses_router)

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    return app


class TestCoursesApiLayered:
    def test_list_courses_requires_auth(self, db_session):
        app = _make_app(db_session)
        client = TestClient(app)
        resp = client.get("/courses/")
        assert resp.status_code in (401, 403)

    def test_get_course_404_when_missing(self, db_session, auth_headers_factory):
        """auth_headers_factory is a helper that returns headers + overrides
        get_current_user. If it doesn't exist, build the override inline."""
        from backend.auth import get_current_user
        from backend.models import User

        app = _make_app(db_session)

        # Create a user and override auth
        user = User(username="tester", password_hash="x")
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        app.dependency_overrides[get_current_user] = lambda: user
        client = TestClient(app)
        resp = client.get("/courses/999999")
        assert resp.status_code == 404
```

注意：`auth_headers_factory` 在现有 conftest 中可能不存在。用 `app.dependency_overrides[get_current_user]` 直接注入假用户更简单可靠（如上）。

- [ ] **Step 5: 运行新 API 测试**

Run: `cd backend && python -m pytest tests/api/test_courses_api.py -v`
Expected: PASS

- [ ] **Step 6: 运行全量后端测试（确认旧 router 未受影响）**

Run: `cd backend && python -m pytest -q`
Expected: PASS（新旧共存，无冲突）

- [ ] **Step 7: 提交**

```bash
git add backend/api/courses.py backend/tests/api/
git commit -m "feat(api): layered courses router (read endpoints) as migration template"
```

---

# 里程碑 M3：前端 — Tailwind v4 + shadcn-vue 基石

## Task 7: 引入 Tailwind v4 + 设计 token

**Files:**
- Modify: `frontend/package.json`
- Create: `frontend/postcss.config.js`
- Create: `frontend/src/styles/tokens.css`
- Modify: `frontend/vite.config.ts`
- Modify: `frontend/src/main.ts`

- [ ] **Step 1: 安装 Tailwind v4 及配套工具**

Run: `cd frontend && npm install -D tailwindcss@^4.0.0 @tailwindcss/postcss postcss autoprefixer && npm install class-variance-authority clsx tailwind-merge lucide-vue-next`

注意：Tailwind v4 使用 `@tailwindcss/postcss` 插件，配置方式与 v3 不同。

- [ ] **Step 2: 创建 postcss.config.js**

Create `frontend/postcss.config.js`:

```javascript
export default {
  plugins: {
    "@tailwindcss/postcss": {},
  },
};
```

- [ ] **Step 3: 创建 tokens.css（迁移自 style.css :root）**

Create `frontend/src/styles/tokens.css`，从 `frontend/src/style.css` 的 `:root { ... }` 块**完整复制**所有 CSS 变量（约 80 个变量：palette、brand、typography、spacing、radii、shadows）。

先定位：Run `grep -n ":root" frontend/src/style.css` 找到起始行，Run `grep -n "^}" frontend/src/style.css | head -1` 找到结束行，把整块复制。

在 `tokens.css` 顶部添加 Tailwind v4 引入：

```css
@import "tailwindcss";

/* ── Design tokens (migrated from style.css :root) ── */
:root {
  /* ... 粘贴所有变量 ... */
  --page-bg: #f4f6fb;
  /* ... 其余变量 ... */
}
```

- [ ] **Step 4: 创建暗色模式 token 覆盖**

在 `tokens.css` 的 `:root` 块之后添加：

```css
/* ── Dark mode tokens ── */
html.dark {
  --page-bg: #0f172a;
  --surface: #1e293b;
  --surface-soft: #1a2538;
  --surface-strong: #273449;
  --text-main: #f1f5f9;
  --text-secondary: #cbd5e1;
  --text-muted: #94a3b8;
  --text-placeholder: #64748b;
  --line-soft: #334155;
  --line-strong: #475569;
}
```

- [ ] **Step 5: 在 main.ts 引入 tokens.css**

修改 `frontend/src/main.ts`，在 `import "./style.css";` **之前**添加：

```typescript
import "./styles/tokens.css";
import "./styles/base.css";
import "./styles/transitions.css";
import "./styles/utilities.css";
import "./style.css";  // legacy; will be removed as pages migrate to Tailwind
```

- [ ] **Step 6: typecheck + build 验证不破坏现有样式**

Run: `cd frontend && npm run build`
Expected: build 成功。用浏览器打开 dev server，**逐页检查样式无破损**（变量被 tokens.css 重新提供，style.css 仍加载，应无视觉变化）。

- [ ] **Step 7: 运行前端测试**

Run: `cd frontend && npm run test`
Expected: PASS

- [ ] **Step 8: 提交**

```bash
git add frontend/package.json frontend/package-lock.json frontend/postcss.config.js frontend/src/styles/tokens.css frontend/src/main.ts
git commit -m "feat(styles): introduce Tailwind v4 + design tokens (dark mode ready)"
```

---

## Task 8: 创建 cn() 工具 + shadcn-vue 基础组件

**Files:**
- Create: `frontend/src/lib/utils.ts`
- Create: `frontend/src/components/ui/button/Button.vue`
- Create: `frontend/src/components/ui/button/index.ts`
- Create: `frontend/src/components/ui/card/Card.vue` 等
- Test: `frontend/src/lib/__tests__/utils.spec.ts`

- [ ] **Step 1: 写 cn() 测试**

Create `frontend/src/lib/__tests__/utils.spec.ts`:

```typescript
import { describe, expect, it } from "vitest";
import { cn } from "../utils";

describe("cn", () => {
  it("joins class names", () => {
    expect(cn("a", "b")).toBe("a b");
  });

  it("ignores falsy values", () => {
    expect(cn("a", false, null, undefined, "b")).toBe("a b");
  });

  it("dedupes conflicting tailwind classes via tailwind-merge", () => {
    // tailwind-merge should keep the last conflicting class
    expect(cn("p-2", "p-4")).toBe("p-4");
  });

  it("handles objects (clsx syntax)", () => {
    expect(cn({ active: true, disabled: false })).toBe("active");
  });
});
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd frontend && npx vitest run src/lib/__tests__/utils.spec.ts`
Expected: FAIL

- [ ] **Step 3: 创建 lib/utils.ts**

Create `frontend/src/lib/utils.ts`:

```typescript
import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}
```

- [ ] **Step 4: 运行测试**

Run: `cd frontend && npx vitest run src/lib/__tests__/utils.spec.ts`
Expected: PASS

- [ ] **Step 5: 创建 Button 组件（shadcn-vue 风格，手写而非 CLI，避免 CLI 交互）**

Create `frontend/src/components/ui/button/Button.vue`:

```vue
<script setup lang="ts">
import type { HTMLAttributes } from "vue";
import { cn } from "@/lib/utils";

const props = withDefaults(defineProps<{
  variant?: "default" | "secondary" | "outline" | "ghost" | "destructive";
  size?: "default" | "sm" | "lg" | "icon";
  class?: HTMLAttributes["class"];
}>(), {
  variant: "default",
  size: "default",
});

const variantClasses: Record<string, string> = {
  default: "bg-[var(--primary)] text-white hover:bg-[var(--primary-strong)]",
  secondary: "bg-[var(--surface-soft)] text-[var(--text-main)] hover:bg-[var(--surface-strong)]",
  outline: "border border-[var(--line-strong)] bg-transparent hover:bg-[var(--surface-soft)]",
  ghost: "hover:bg-[var(--surface-soft)]",
  destructive: "bg-[var(--rose)] text-white hover:opacity-90",
};

const sizeClasses: Record<string, string> = {
  default: "h-10 px-4 py-2 text-sm",
  sm: "h-9 px-3 text-sm",
  lg: "h-11 px-8 text-base",
  icon: "h-10 w-10",
};
</script>

<template>
  <button
    :class="cn(
      'inline-flex items-center justify-center gap-2 rounded-[var(--radius-md)] font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 disabled:pointer-events-none disabled:opacity-50',
      variantClasses[props.variant],
      sizeClasses[props.size],
      props.class,
    )"
  >
    <slot />
  </button>
</template>
```

Create `frontend/src/components/ui/button/index.ts`:

```typescript
export { default as Button } from "./Button.vue";
```

- [ ] **Step 6: 创建 Card 组件族**

Create `frontend/src/components/ui/card/Card.vue`:

```vue
<script setup lang="ts">
import type { HTMLAttributes } from "vue";
import { cn } from "@/lib/utils";

const props = defineProps<{ class?: HTMLAttributes["class"] }>();
</script>

<template>
  <div :class="cn('rounded-[var(--radius-lg)] border border-[var(--line-soft)] bg-[var(--surface)] shadow-[var(--shadow-card)]', props.class)">
    <slot />
  </div>
</template>
```

Create `frontend/src/components/ui/card/CardHeader.vue`, `CardTitle.vue`, `CardContent.vue`, `CardFooter.vue`（结构类似，用 cn 合并基础 class + slot）。为简洁，每个文件结构相同，仅基础 class 不同：

- `CardHeader.vue`: `p-6 pb-0`
- `CardTitle.vue`: `text-lg font-semibold leading-none tracking-tight`
- `CardContent.vue`: `p-6`
- `CardFooter.vue`: `p-6 pt-0 flex items-center`

Create `frontend/src/components/ui/card/index.ts`:

```typescript
export { default as Card } from "./Card.vue";
export { default as CardHeader } from "./CardHeader.vue";
export { default as CardTitle } from "./CardTitle.vue";
export { default as CardContent } from "./CardContent.vue";
export { default as CardFooter } from "./CardFooter.vue";
```

- [ ] **Step 7: typecheck + build + test**

Run: `cd frontend && npm run typecheck && npm run build && npm run test`
Expected: PASS

- [ ] **Step 8: 提交**

```bash
git add frontend/src/lib/ frontend/src/components/ui/
git commit -m "feat(ui): add cn() util and shadcn-vue Button + Card components"
```

---

# 里程碑 M4：前端 — Pinia store 完善

## Task 9: 创建 course store（带缓存）

**Files:**
- Create: `frontend/src/stores/course.ts`
- Test: `frontend/src/stores/__tests__/course.spec.ts`

- [ ] **Step 1: 写 course store 测试**

Create `frontend/src/stores/__tests__/course.spec.ts`:

```typescript
import { setActivePinia, createPinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../../api/courses", () => ({
  getCourses: vi.fn(),
  getMyCourses: vi.fn(),
}));

import { useCourseStore } from "../course";
import * as coursesApi from "../../api/courses";

describe("useCourseStore", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  it("starts with empty list", () => {
    const store = useCourseStore();
    expect(store.myCourses).toHaveLength(0);
    expect(store.loading).toBe(false);
  });

  it("fetchMyCourses populates list", async () => {
    const fake = [{ id: 1, name: "课程 A" }];
    vi.mocked(coursesApi.getMyCourses).mockResolvedValue(fake as any);
    const store = useCourseStore();
    await store.fetchMyCourses();
    expect(store.myCourses).toEqual(fake);
  });

  it("uses cache when not stale", async () => {
    const fake = [{ id: 1, name: "课程 A" }];
    vi.mocked(coursesApi.getMyCourses).mockResolvedValue(fake as any);
    const store = useCourseStore();
    await store.fetchMyCourses();
    await store.fetchMyCourses(); // second call should use cache
    expect(coursesApi.getMyCourses).toHaveBeenCalledTimes(1);
  });
});
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd frontend && npx vitest run src/stores/__tests__/course.spec.ts`
Expected: FAIL

- [ ] **Step 3: 实现 course store**

Create `frontend/src/stores/course.ts`:

```typescript
import { ref } from "vue";
import { defineStore } from "pinia";
import { getMyCourses, getCourses } from "../api/courses";

const CACHE_TTL_MS = 60_000; // 1 minute

export const useCourseStore = defineStore("course", () => {
  const myCourses = ref<any[]>([]);
  const allCourses = ref<any[]>([]);
  const loading = ref(false);
  const error = ref("");

  let lastMyFetch = 0;
  let lastAllFetch = 0;

  async function fetchMyCourses(force = false): Promise<void> {
    const now = Date.now();
    if (!force && now - lastMyFetch < CACHE_TTL_MS && myCourses.value.length > 0) {
      return; // use cache
    }
    loading.value = true;
    error.value = "";
    try {
      myCourses.value = await getMyCourses();
      lastMyFetch = now;
    } catch (e: any) {
      error.value = e?.message || "加载课程失败";
    } finally {
      loading.value = false;
    }
  }

  async function fetchAllCourses(force = false): Promise<void> {
    const now = Date.now();
    if (!force && now - lastAllFetch < CACHE_TTL_MS && allCourses.value.length > 0) {
      return;
    }
    loading.value = true;
    error.value = "";
    try {
      allCourses.value = await getCourses();
      lastAllFetch = now;
    } catch (e: any) {
      error.value = e?.message || "加载课程失败";
    } finally {
      loading.value = false;
    }
  }

  function clearCache(): void {
    myCourses.value = [];
    allCourses.value = [];
    lastMyFetch = 0;
    lastAllFetch = 0;
  }

  return { myCourses, allCourses, loading, error, fetchMyCourses, fetchAllCourses, clearCache };
});
```

注意：`getMyCourses` / `getCourses` 的实际签名需对照 `frontend/src/api/courses.ts` 确认。若返回值是 `{ items, total }` 而非数组，调整 store 和测试（取 `.items`）。

- [ ] **Step 4: 运行测试**

Run: `cd frontend && npx vitest run src/stores/__tests__/course.spec.ts`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add frontend/src/stores/course.ts frontend/src/stores/__tests__/course.spec.ts
git commit -m "feat(store): add course store with stale-while-revalidate cache"
```

---

## Task 10: 创建 theme + ui store（暗色模式 + UI 状态）

**Files:**
- Create: `frontend/src/stores/theme.ts`
- Create: `frontend/src/stores/ui.ts`
- Test: `frontend/src/stores/__tests__/theme.spec.ts`

- [ ] **Step 1: 写 theme store 测试**

Create `frontend/src/stores/__tests__/theme.spec.ts`:

```typescript
import { setActivePinia, createPinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: vi.fn((k: string) => store[k] ?? null),
    setItem: vi.fn((k: string, v: string) => { store[k] = v; }),
    clear: () => { store = {}; },
  };
})();
Object.defineProperty(window, "localStorage", { value: localStorageMock });

import { useThemeStore } from "../theme";

describe("useThemeStore", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    localStorageMock.clear();
    document.documentElement.classList.remove("dark");
  });

  it("defaults to light theme", () => {
    const theme = useThemeStore();
    theme.init();
    expect(theme.mode).toBe("light");
  });

  it("toggle switches to dark and sets class", () => {
    const theme = useThemeStore();
    theme.init();
    theme.toggle();
    expect(theme.mode).toBe("dark");
    expect(document.documentElement.classList.contains("dark")).toBe(true);
  });

  it("persists to localStorage", () => {
    const theme = useThemeStore();
    theme.init();
    theme.toggle();
    expect(localStorageMock.setItem).toHaveBeenCalledWith("theme", "dark");
  });

  it("restores from localStorage", () => {
    localStorageMock.getItem.mockReturnValue("dark");
    const theme = useThemeStore();
    theme.init();
    expect(theme.mode).toBe("dark");
  });
});
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd frontend && npx vitest run src/stores/__tests__/theme.spec.ts`
Expected: FAIL

- [ ] **Step 3: 实现 theme store**

Create `frontend/src/stores/theme.ts`:

```typescript
import { ref } from "vue";
import { defineStore } from "pinia";

export type ThemeMode = "light" | "dark";
const STORAGE_KEY = "theme";

export const useThemeStore = defineStore("theme", () => {
  const mode = ref<ThemeMode>("light");

  function applyToDom(m: ThemeMode): void {
    if (m === "dark") {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  }

  function init(): void {
    const saved = localStorage.getItem(STORAGE_KEY) as ThemeMode | null;
    mode.value = saved ?? "light";
    applyToDom(mode.value);
  }

  function toggle(): void {
    mode.value = mode.value === "dark" ? "light" : "dark";
    applyToDom(mode.value);
    localStorage.setItem(STORAGE_KEY, mode.value);
  }

  function setMode(m: ThemeMode): void {
    mode.value = m;
    applyToDom(m);
    localStorage.setItem(STORAGE_KEY, m);
  }

  return { mode, init, toggle, setMode };
});
```

- [ ] **Step 4: 实现 ui store**

Create `frontend/src/stores/ui.ts`:

```typescript
import { ref } from "vue";
import { defineStore } from "pinia";

export const useUiStore = defineStore("ui", () => {
  const sidebarOpen = ref(false);
  const globalLoading = ref(false);

  function toggleSidebar(): void {
    sidebarOpen.value = !sidebarOpen.value;
  }

  function setSidebar(open: boolean): void {
    sidebarOpen.value = open;
  }

  function setGlobalLoading(loading: boolean): void {
    globalLoading.value = loading;
  }

  return { sidebarOpen, globalLoading, toggleSidebar, setSidebar, setGlobalLoading };
});
```

- [ ] **Step 5: 在 App.vue 中初始化 theme**

修改 `frontend/src/App.vue`，在 setup 中调用 `theme.init()`：

```vue
<script setup lang="ts">
import { onMounted } from "vue";
import { useThemeStore } from "@/stores/theme";

const theme = useThemeStore();
onMounted(() => theme.init());
</script>

<template>
  <RouterView />
</template>
```

（对照现有 App.vue 内容合并，保留原有逻辑。）

- [ ] **Step 6: 运行测试**

Run: `cd frontend && npm run test`
Expected: PASS

- [ ] **Step 7: 提交**

```bash
git add frontend/src/stores/theme.ts frontend/src/stores/ui.ts frontend/src/stores/__tests__/theme.spec.ts frontend/src/App.vue
git commit -m "feat(store): add theme (dark mode) and ui stores"
```

---

# 里程碑 M5：前端页面迁移 + 规范工具链

## Task 11: 迁移 LoginView 到 shadcn-vue（样板）

**Files:**
- Modify: `frontend/src/views/auth/LoginView.vue`

> **说明**：LoginView 是最简单的页面，作为迁移样板。其余页面（Register、Home、CourseList、CourseDetail）按相同模式后续迁移。

- [ ] **Step 1: 读取现有 LoginView.vue**

Run: `cat frontend/src/views/auth/LoginView.vue`
记录其结构：表单字段、按钮、错误提示、与 auth store 的交互。

- [ ] **Step 2: 迁移 template 到 shadcn-vue 组件**

将 LoginView.vue 的 template 中：
- 外层容器 → `<Card>` + `<CardHeader>` + `<CardContent>` + `<CardFooter>`
- 按钮 → `<Button variant="default">`
- 表单保持原生 `<input>`，但用 Tailwind class 替换原有 class（`h-10 w-full rounded-[var(--radius-md)] border ...`）

**script 部分保持不变**（仍用 `useAuthStore`）。只改 template 的 class 和组件引用。

示例迁移后结构：
```vue
<script setup lang="ts">
// 保持原有逻辑不变
import { useAuthStore } from "@/stores/auth";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from "@/components/ui/card";
const auth = useAuthStore();
// ...原有 ref 和方法...
</script>

<template>
  <Card class="mx-auto max-w-md">
    <CardHeader>
      <CardTitle>登录</CardTitle>
    </CardHeader>
    <CardContent>
      <!-- 表单字段，input 用 Tailwind class -->
    </CardContent>
    <CardFooter class="flex-col gap-2">
      <Button class="w-full" :disabled="auth.loading" @click="handleLogin">
        {{ auth.loading ? "登录中…" : "登录" }}
      </Button>
      <!-- 注册链接 -->
    </CardFooter>
  </Card>
</template>
```

- [ ] **Step 3: typecheck + build**

Run: `cd frontend && npm run typecheck && npm run build`
Expected: PASS

- [ ] **Step 4: 手动验证**

Run: `cd frontend && npm run dev`
打开登录页，验证：表单可输入、登录按钮可点、错误提示正常显示、注册链接跳转。视觉与重构前基本一致（用 Card 组件后应更整洁）。

- [ ] **Step 5: 运行前端测试**

Run: `cd frontend && npm run test`
Expected: PASS

- [ ] **Step 6: 提交**

```bash
git add frontend/src/views/auth/LoginView.vue
git commit -m "refactor(ui): migrate LoginView to shadcn-vue components"
```

---

## Task 12: 迁移 RegisterView + Home + CourseList（按相同模式）

**Files:**
- Modify: `frontend/src/views/auth/RegisterView.vue`
- Modify: `frontend/src/views/Home.vue`
- Modify: `frontend/src/views/CourseList.vue`

- [ ] **Step 1: 迁移 RegisterView**

按 Task 11 的模式迁移 RegisterView（与 Login 结构几乎相同）。完成后 typecheck + build + 手动验证。

- [ ] **Step 2: 迁移 Home**

迁移 Home.vue：用 `Card` 组件替换欢迎卡片、数据卡片区域。按钮用 `Button`。保留所有数据获取逻辑不变。

- [ ] **Step 3: 迁移 CourseList**

迁移 CourseList.vue：用 `Card` 包裹每个课程项。列表布局用 Tailwind grid (`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4`)。分页用 `Button`。

- [ ] **Step 4: 每个页面迁移后立即验证**

每个文件改完后：
Run: `cd frontend && npm run typecheck && npm run build`
打开对应页面手动验证视觉和功能正常。

- [ ] **Step 5: 运行前端测试**

Run: `cd frontend && npm run test`
Expected: PASS

- [ ] **Step 6: 提交**

```bash
git add frontend/src/views/auth/RegisterView.vue frontend/src/views/Home.vue frontend/src/views/CourseList.vue
git commit -m "refactor(ui): migrate RegisterView, Home, CourseList to shadcn-vue"
```

---

## Task 13: 引入 ESLint flat config + Prettier

**Files:**
- Modify: `frontend/package.json`
- Create: `frontend/eslint.config.js`
- Create: `frontend/.prettierrc`

- [ ] **Step 1: 安装 ESLint + Prettier**

Run: `cd frontend && npm install -D eslint@^9 eslint-plugin-vue @vue/eslint-config-typescript @vue/eslint-config-prettier prettier`

- [ ] **Step 2: 创建 eslint.config.js（flat config）**

Create `frontend/eslint.config.js`:

```javascript
import pluginVue from "eslint-plugin-vue";
import vueTsEslintConfig from "@vue/eslint-config-typescript";
import skipFormatting from "@vue/eslint-config-prettier/skip-formatting";

export default [
  {
    name: "app/files-to-lint",
    files: ["**/*.{ts,mts,tsx,vue}"],
  },
  {
    name: "app/files-to-ignore",
    ignores: ["**/dist/**", "**/node_modules/**", "**/coverage/**"],
  },
  ...pluginVue.configs["flat/essential"],
  ...vueTsEslintConfig(),
  skipFormatting,
];
```

- [ ] **Step 3: 创建 .prettierrc**

Create `frontend/.prettierrc`:

```json
{
  "semi": true,
  "singleQuote": false,
  "tabWidth": 2,
  "trailingComma": "all",
  "printWidth": 100
}
```

注意：现有代码用双引号 + 分号，prettier 配置应与之匹配以减少首次格式化的 diff。若现有代码混用，先跑一次 `prettier --write` 统一。

- [ ] **Step 4: 在 package.json 添加 scripts**

修改 `frontend/package.json` 的 scripts，添加：

```json
{
  "scripts": {
    "lint": "eslint .",
    "lint:fix": "eslint . --fix",
    "format": "prettier --write ."
  }
}
```

- [ ] **Step 5: 首次运行 lint，修复可自动修复的问题**

Run: `cd frontend && npx eslint . 2>&1 | head -50`
Expected: 列出错误（首次运行可能有较多）。运行 `npm run lint:fix` 自动修复。

- [ ] **Step 6: 确认 lint 通过（或仅剩需手动处理的）**

Run: `cd frontend && npm run lint`
Expected: 0 errors（warnings 可接受）

- [ ] **Step 7: 提交（含格式化后的代码）**

```bash
git add frontend/
git commit -m "chore: add ESLint flat config + Prettier, format codebase"
```

---

## Task 14: 引入后端 Ruff + pre-commit

**Files:**
- Modify: `backend/requirements.txt`
- Create: `pyproject.toml`（项目根）
- Modify: `.pre-commit-config.yaml`

- [ ] **Step 1: 安装 Ruff**

Run: `cd backend && pip install ruff`

- [ ] **Step 2: 创建 pyproject.toml（项目根）**

Create `pyproject.toml`:

```toml
[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "UP", "B"]
ignore = ["E501"]  # line length handled by formatter

[tool.ruff.lint.per-file-ignores]
"backend/migrations/*" = ["E", "F"]

[tool.ruff.format]
quote-style = "double"
```

- [ ] **Step 3: 运行 Ruff 检查**

Run: `cd "D:/File/exam system" && ruff check backend/`
Expected: 列出问题。运行 `ruff check backend/ --fix` 自动修复（import 排序等）。

- [ ] **Step 4: 运行 Ruff format**

Run: `cd "D:/File/exam system" && ruff format backend/`
Expected: 格式化代码。注意检查 diff 是否合理（现有代码用 BOM 和双引号，ruff format 应保持）。

- [ ] **Step 5: 运行全量后端测试确认格式化无破坏**

Run: `cd backend && python -m pytest -q`
Expected: PASS

- [ ] **Step 6: 更新 .pre-commit-config.yaml**

修改 `.pre-commit-config.yaml`，添加 ruff hooks：

```yaml
- repo: https://github.com/astral-sh/ruff-pre-commit
  rev: v0.8.0
  hooks:
    - id: ruff
      args: [--fix]
    - id: ruff-format
```

（保留现有 pre-commit hooks，仅追加。先读现有文件内容再合并。）

- [ ] **Step 7: 提交**

```bash
git add pyproject.toml .pre-commit-config.yaml backend/
git commit -m "chore: add Ruff linter/formatter + pre-commit hooks"
```

---

## Task 15: Docker 镜像优化（缓存层）

**Files:**
- Modify: `Dockerfile.backend`
- Modify: `Dockerfile.frontend`

- [ ] **Step 1: 读取现有 Dockerfile**

Run: `cat Dockerfile.backend && echo "---" && cat Dockerfile.frontend`
记录现有结构。

- [ ] **Step 2: 优化后端 Dockerfile —— 先装依赖再拷代码**

修改 `Dockerfile.backend`，把 `COPY requirements.txt` + `RUN pip install` 放在 `COPY .` 之前，利用 Docker 缓存层（依赖不变时跳过重装）：

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install deps first (cached unless requirements.txt changes)
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy source (changes frequently)
COPY backend/ ./backend/

EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

（对照现有 Dockerfile 调整，保留原有的系统依赖安装等步骤。）

- [ ] **Step 3: 优化前端 Dockerfile —— 分离依赖安装与构建**

修改 `Dockerfile.frontend`，确保 npm install 层独立：

```dockerfile
# Stage 1: build
FROM node:20-alpine AS build
WORKDIR /app

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# Stage 2: serve
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 8080
```

- [ ] **Step 4: 验证 Dockerfile 语法（不构建，只 lint）**

Run: `cd "D:/File/exam system" && docker build --check -f Dockerfile.backend . 2>&1 | head` （若有 hadolint 更好，否则跳过）

若无 docker 环境，至少做语法肉眼检查。

- [ ] **Step 5: 提交**

```bash
git add Dockerfile.backend Dockerfile.frontend
git commit -m "perf(docker): optimize layer caching in backend and frontend Dockerfiles"
```

---

## Task 16: Phase 2 完整性验证

**Files:** 无（纯验证）

- [ ] **Step 1: 后端全量测试**

Run: `cd backend && python -m pytest -q`
Expected: PASS（含新增的 models/repos/services/api 测试）

- [ ] **Step 2: 前端全量测试 + typecheck + build**

Run: `cd frontend && npm run typecheck && npm run test && npm run build`
Expected: 全部 PASS

- [ ] **Step 3: 验证 migration 可执行**

Run: `cd backend && python -c "
from alembic.config import Config
from alembic import command
import tempfile, os
tmp = tempfile.mktemp(suffix='.db')
os.environ['DATABASE_URL'] = f'sqlite:///{tmp}'
cfg = Config('alembic.ini')
command.upgrade(cfg, 'head')
print('migration ok')
os.unlink(tmp)
"`
Expected: 输出 `migration ok`

- [ ] **Step 4: 验证暗色模式**

Run: `cd frontend && npm run dev`
在浏览器打开，通过控制台 `localStorage.setItem('theme','dark')` 刷新，验证暗色样式生效。

- [ ] **Step 5: 验证 lint 全通过**

Run: `cd frontend && npm run lint && cd ../backend && ruff check ../backend`
Expected: 0 errors

- [ ] **Step 6: 对照 spec 验收标准（§4.6）逐项确认**

对照 `docs/superpowers/specs/2026-06-27-major-refactor-design.md` §4.6：
- [ ] Tailwind v4 配置完成，shadcn-vue Button + Card 就位
- [ ] LoginView/RegisterView/Home/CourseList/CourseDetail 中至少 5 页迁移完成
- [ ] 暗色模式可用并持久化
- [ ] 后端三层架构（api/services/repositories）建立，courses 已迁移
- [ ] 依赖注入工作正常（api/deps.py）
- [ ] 7 个新模型通过 Alembic migration 创建 + roles 种子
- [ ] ESLint + Ruff + Prettier 全量通过
- [ ] Docker 镜像缓存层优化

- [ ] **Step 7: 最终提交（如有遗漏改动）**

```bash
git add -A && git status
```

---

## 完成标准（对照 Spec §4.6）

- [x] Tailwind v4 配置完成，shadcn-vue 基础组件（Button + Card）就位
- [x] LoginView/RegisterView/Home/CourseList 迁移到 shadcn-vue
- [x] 暗色模式可用并持久化（theme store + tokens.css html.dark）
- [x] 后端三层架构（api/services/repositories）建立，courses read 端点迁移完成
- [x] 依赖注入工作正常（api/deps.py）
- [x] 7 个新模型通过 Alembic migration 创建 + 默认 roles 种子
- [x] ESLint flat config + Ruff + Prettier 全量通过
- [x] Docker 镜像缓存层优化

---

## 自查备注（Self-Review）

**Spec 覆盖**: Spec §4 的 4.1–4.5 全部映射到任务：
- 4.1 shadcn-vue + Tailwind → Task 7, 8, 11, 12
- 4.2 完整 Pinia store 体系 → Task 9, 10（auth/import/notification 已在 Phase 1 完成）
- 4.3 三层架构 + 依赖注入 → Task 3, 4, 5, 6
- 4.4 数据库模型扩展 → Task 1, 2
- 4.5 基础设施升级 → Task 13, 14, 15

**类型一致性**: `BaseRepository`/`CourseRepository`/`CourseService` 命名跨任务一致。`useCourseStore`/`useThemeStore`/`useUiStore` 与 Phase 1 的 `useAuthStore` 命名风格一致。`get_course_if_accessible`/`list_visible` 方法名在 service 和测试间一致。

**范围说明（重要）**:
- 后端三层架构迁移：本 Phase 仅迁移 **courses router 的只读端点** 作为样板，其余 7 个 router 留后续迭代。理由：一次性迁移所有 router 风险高、回归测试压力大；courses 是最典型的样板，建立模式后其余 router 可按相同模式增量迁移。新代码（api/courses.py）不挂载到 main.py，与旧 router 零冲突。这是有意的阶段划分，符合"渐进式"原则。
- 前端页面迁移：本 Phase 迁移 5 个核心页面（Login/Register/Home/CourseList + 样板），其余 12 个页面后续按相同模式迁移。
- `style.css`（43KB）：本 Phase 引入 Tailwind 但**保留** style.css，迁移后的页面逐步不再依赖它，最终在所有页面迁移完后删除。

**注**: Task 6 的 `auth_headers_factory` 在测试中改用 `app.dependency_overrides[get_current_user]` 直接注入，更简单可靠，避免依赖不存在的 fixture。
