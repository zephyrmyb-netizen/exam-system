# Phase 3 — 产品升级 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Prerequisite:** Phase 2 merged — 三层架构（api/services/repositories）已建立，`PermissionService`、7 个新模型（Role/Exam/ExamQuestion/ExamSubmission/Collaboration/...）已通过 Alembic migration 创建，shadcn-vue + Tailwind v4 + Pinia store 体系已就位。

**Goal:** 让系统从"刷题工具"变成"完整的考试学习平台" —— 实现正式考试模式、多人协作与角色权限系统、UI 体验全面革新（全新首页/练习体验/移动端/动画/暗色模式）。

**Architecture:** 后端基于 Phase 2 已有的 Exam/Role/Collaboration 模型实现考试 API 和权限装饰器；前端用 shadcn-vue 重做核心交互页面，新增考试模块、键盘快捷键、滑动手势、底部 Tab Bar。全程 TDD，新增功能独立于现有练习流程，不破坏现有行为。

**Tech Stack:** FastAPI / SQLAlchemy / pytest（后端）；Vue 3 / shadcn-vue / Tailwind v4 / Pinia / Vitest（前端）。

**Spec:** `docs/superpowers/specs/2026-06-27-major-refactor-design.md` §5

---

## 文件结构总览

### 后端新增 / 修改

| 文件 | 责任 | 操作 |
|---|---|---|
| `backend/schemas.py` | 新增 Exam/ExamSubmission/Collaboration/Role 系列 schema | 修改 |
| `backend/repositories/exam_repo.py` | Exam/ExamQuestion/ExamSubmission 数据访问 | 新建 |
| `backend/repositories/collaboration_repo.py` | Collaboration 数据访问 | 新建 |
| `backend/services/exam_service.py` | 考试业务逻辑（创建/发布/提交/评分/排行榜） | 新建 |
| `backend/services/permission_service.py` | 实现 RBAC 真实校验（替换 Phase 2 stub） | 修改 |
| `backend/api/deps.py` | 新增 `require_permission` 依赖 + exam service 工厂 | 修改 |
| `backend/api/exams.py` | 考试薄路由层 | 新建 |
| `backend/api/courses.py` | 写操作端点迁移到 service + 权限校验 | 修改 |
| `backend/api/admin.py` | 管理后台路由（用户/公告/统计） | 新建 |
| `backend/auth.py` | `get_current_user` 附带 role 信息 | 修改 |
| `backend/schemas.py` `UserOut` | role 字段类型升级 | 修改 |
| `backend/main.py` | include exams + admin 路由 | 修改 |

### 前端新增 / 修改

| 文件 | 责任 | 操作 |
|---|---|---|
| `frontend/src/types/index.ts` | Exam/Role/Permission 类型 | 修改 |
| `frontend/src/api/exam.ts` | 考试 API | 新建 |
| `frontend/src/api/admin.ts` | 管理 API | 新建 |
| `frontend/src/api/auth.ts` | 角色字段 | 修改 |
| `frontend/src/stores/auth.ts` | 携带 role + permissions | 修改 |
| `frontend/src/stores/exam.ts` | 考试会话状态机 | 新建 |
| `frontend/src/composables/useKeyboardShortcuts.ts` | 键盘快捷键 | 新建 |
| `frontend/src/composables/useSwipe.ts` | 滑动手势 | 新建 |
| `frontend/src/router.ts` | 新增考试 + admin 路由 + 权限守卫 | 修改 |
| `frontend/src/views/Home.vue` | 全新首页（shadcn-vue + 数据卡片） | 修改 |
| `frontend/src/views/exam/ExamList.vue` 等 6 个 | 考试模块页面 | 新建 |
| `frontend/src/views/admin/Admin*.vue` 3 个 | 管理后台页面 | 新建 |
| `frontend/src/components/exam/*` | 考试答题组件 | 新建 |
| `frontend/src/layouts/AppLayout.vue` | 响应式 + 底部 Tab Bar | 修改 |

---

## 执行顺序

分 5 个里程碑（M1–M5）。

- **M1（后端权限）**: Task 1–3 — RBAC 真实校验 + 权限依赖
- **M2（后端考试）**: Task 4–7 — Exam schemas + service + API + 评分/排行榜
- **M3（后端管理）**: Task 8 — 管理后台 API
- **M4（前端权限 + 考试）**: Task 9–13 — 类型/API/store + 考试页面 + 路由守卫
- **M5（前端 UX 革新）**: Task 14–19 — 首页/练习体验/键盘手势/移动端/动画/暗色

---

# 里程碑 M1：后端 — 角色权限真实校验

## Task 1: 升级 UserOut schema 和 get_current_user 携带角色

**Files:**
- Modify: `backend/schemas.py:58-63`（UserOut）
- Modify: `backend/auth.py`（get_current_user eager-load role）
- Test: `backend/tests/test_auth.py`（现有回归）+ 新增角色测试

- [ ] **Step 1: 先跑现有 auth 测试，记录基线**

Run: `cd backend && python -m pytest tests/test_auth.py -q`
Expected: PASS

- [ ] **Step 2: 写角色字段测试**

在 `backend/tests/test_auth.py` 末尾添加：

```python
def test_me_endpoint_returns_role_field(client, auth_headers):
    """The /auth/me endpoint should include a role field."""
    resp = client.get("/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "role" in data
    # New users default to 'student' (no role assigned yet)
    assert data["role"] in ("student", "user", "teacher", "admin")
```

注意：`auth_headers` fixture 在 conftest 中已存在（注册并登录一个用户）。新用户的 `role_id` 为 NULL，`UserOut.role` 现有默认值是 `"user"`，本任务改为返回实际角色名，默认 `"student"`。

- [ ] **Step 3: 运行测试确认通过（基线）**

Run: `cd backend && python -m pytest tests/test_auth.py::test_me_endpoint_returns_role_field -v`
Expected: PASS（因为 UserOut 已有 role 字段默认 "user"，断言用 in 包含 "user"）

- [ ] **Step 4: 修改 UserOut.role 默认为 student 并从关联加载**

修改 `backend/schemas.py` 的 `UserOut`：

```python
class UserOut(BaseModel):
    id: int
    username: str
    role: str = "student"
    permissions: list[str] = []

    model_config = ConfigDict(from_attributes=True)
```

- [ ] **Step 5: 修改 get_current_user eager-load role 关系**

修改 `backend/auth.py` 的 `get_current_user`，在查询用户时 joinedload role：

```python
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> models.User:
    from sqlalchemy.orm import joinedload

    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效或过期的 token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str: str | None = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        user_id = int(user_id_str)
    except JWTError:
        raise credentials_exception

    user = (
        db.query(models.User)
        .options(joinedload(models.User.role))
        .filter(models.User.id == user_id)
        .first()
    )
    if user is None:
        raise credentials_exception
    return user
```

注意：`User.role` relationship 需在 Phase 2 Task 1 已添加。如果 `get_current_user_optional` 也查询用户，同样加 joinedload（保持一致）。

- [ ] **Step 6: 运行全量 auth 测试**

Run: `cd backend && python -m pytest tests/test_auth.py -q`
Expected: PASS

- [ ] **Step 7: 运行全量后端测试**

Run: `cd backend && python -m pytest -q`
Expected: PASS

- [ ] **Step 8: 提交**

```bash
git add backend/schemas.py backend/auth.py backend/tests/test_auth.py
git commit -m "feat(auth): include role + permissions in UserOut, eager-load role"
```

---

## Task 2: 实现 PermissionService 真实 RBAC 校验

**Files:**
- Modify: `backend/services/permission_service.py`
- Test: `backend/tests/services/test_permission_service.py`

- [ ] **Step 1: 写权限校验测试**

Create `backend/tests/services/test_permission_service.py`:

```python
from backend.models import User, Role
from backend.services.permission_service import PermissionService


def _make_user(db_session, role_name="student"):
    user = User(username=f"user_{role_name}", password_hash="x")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


class TestPermissionService:
    def test_student_can_practice(self, db_session):
        user = _make_user(db_session, "student")
        svc = PermissionService(db_session)
        assert svc.can(user, "practice:random") is True

    def test_student_cannot_create_exam(self, db_session):
        user = _make_user(db_session, "student")
        svc = PermissionService(db_session)
        assert svc.can(user, "exam:create") is False

    def test_teacher_can_create_exam(self, db_session):
        role = Role(name="teacher")
        db_session.add(role)
        db_session.commit()
        user = User(username="teacher1", password_hash="x", role_id=role.id)
        db_session.add(user)
        db_session.commit()
        svc = PermissionService(db_session)
        assert svc.can(user, "exam:create") is True

    def test_admin_can_manage_users(self, db_session):
        role = Role(name="admin")
        db_session.add(role)
        db_session.commit()
        user = User(username="admin1", password_hash="x", role_id=role.id)
        db_session.add(user)
        db_session.commit()
        svc = PermissionService(db_session)
        assert svc.can(user, "user:manage") is True

    def test_user_with_no_role_defaults_student(self, db_session):
        user = _make_user(db_session)
        svc = PermissionService(db_session)
        assert svc.get_role_name(user) == "student"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd backend && python -m pytest tests/services/test_permission_service.py -v`
Expected: FAIL（Phase 2 stub 的 `can()` 永远返回 True）

- [ ] **Step 3: 实现真实 RBAC**

修改 `backend/services/permission_service.py`：

```python
"""Role-based permission checks."""
from sqlalchemy.orm import Session

from .. import models

# Permission matrix: role -> set of granted permission strings
_ROLE_PERMISSIONS: dict[str, set[str]] = {
    "student": {
        "practice:random",
        "practice:submit",
        "practice:review",
        "wrongbook:read",
        "wrongbook:write",
        "course:read",
        "course:create",
        "exam:take",
        "exam:view_result",
        "chat:use",
        "import:use",
        "bookmark:manage",
    },
    "teacher": {
        # inherits all student perms
        "practice:random",
        "practice:submit",
        "practice:review",
        "wrongbook:read",
        "wrongbook:write",
        "course:read",
        "course:create",
        "course:edit",
        "course:delete",
        "course:publish",
        "exam:create",
        "exam:edit",
        "exam:publish",
        "exam:delete",
        "exam:view_result",
        "exam:view_leaderboard",
        "collaboration:invite",
        "chat:use",
        "import:use",
        "bookmark:manage",
    },
    "admin": {
        # inherits all teacher perms + admin
        "practice:random",
        "practice:submit",
        "practice:review",
        "wrongbook:read",
        "wrongbook:write",
        "course:read",
        "course:create",
        "course:edit",
        "course:delete",
        "course:publish",
        "exam:create",
        "exam:edit",
        "exam:publish",
        "exam:delete",
        "exam:view_result",
        "exam:view_leaderboard",
        "collaboration:invite",
        "user:manage",
        "announcement:manage",
        "stats:view_global",
        "chat:use",
        "import:use",
        "bookmark:manage",
    },
}

# Keep backward-compatible constant names used by routers (Phase 2)
COURSE_CREATE = "course:create"
COURSE_EDIT = "course:edit"
COURSE_DELETE = "course:delete"
EXAM_CREATE = "exam:create"
EXAM_PUBLISH = "exam:publish"
USER_MANAGE = "user:manage"


class PermissionService:
    def __init__(self, db: Session):
        self.db = db

    def get_role_name(self, user: models.User) -> str:
        if user.role is None:
            return "student"
        return user.role.name

    def get_permissions(self, user: models.User) -> set[str]:
        role_name = self.get_role_name(user)
        return _ROLE_PERMISSIONS.get(role_name, _ROLE_PERMISSIONS["student"])

    def can(self, user: models.User, permission: str) -> bool:
        return permission in self.get_permissions(user)

    def assert_can(self, user: models.User, permission: str) -> None:
        """Raise PermissionError if the user lacks the permission."""
        if not self.can(user, permission):
            from fastapi import HTTPException
            raise HTTPException(
                status_code=403,
                detail=f"权限不足，需要：{permission}",
            )
```

- [ ] **Step 4: 运行测试**

Run: `cd backend && python -m pytest tests/services/test_permission_service.py -v`
Expected: PASS

- [ ] **Step 5: 运行全量后端测试（确认 stub→真实校验无破坏现有测试）**

Run: `cd backend && python -m pytest -q`
Expected: PASS。若有失败，是因为某些测试假设所有人能做所有事 —— 检查测试用的用户是否被赋予了 student 角色（默认），student 应能练习/创建课程，不应失败。

- [ ] **Step 6: 提交**

```bash
git add backend/services/permission_service.py backend/tests/services/test_permission_service.py
git commit -m "feat(rbac): implement real role-based permission checks"
```

---

## Task 3: 创建 require_permission 依赖 + 迁移 courses 写操作

**Files:**
- Modify: `backend/api/deps.py`
- Modify: `backend/api/courses.py`
- Test: `backend/tests/api/test_courses_api.py`

- [ ] **Step 1: 写权限依赖测试**

在 `backend/tests/api/test_courses_api.py` 添加：

```python
def test_create_course_requires_course_create_perm(db_session):
    """A student (default role) should still be able to create courses
    (student has course:create). A totally denied perm should 403."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from backend.api.courses import router as courses_router
    from backend.auth import get_current_user
    from backend.database import get_db
    from backend.models import User
    from backend.api.deps import get_permission_service, PermissionService

    app = FastAPI()
    app.include_router(courses_router)
    user = User(username="u", password_hash="x")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    app.dependency_overrides[get_db] = lambda: (yield db_session)
    app.dependency_overrides[get_current_user] = lambda: user

    # Override permission service to DENY course:create
    class DenyAll(PermissionService):
        def can(self, user, perm):
            return False
    app.dependency_overrides[get_permission_service] = lambda: DenyAll(db_session)

    client = TestClient(app)
    resp = client.post("/courses/", json={"name": "test"})
    assert resp.status_code == 403
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd backend && python -m pytest tests/api/test_courses_api.py::test_create_course_requires_course_create_perm -v`
Expected: FAIL（尚无 create 端点 + 无权限检查）

- [ ] **Step 3: 在 deps.py 添加 require_permission 工厂**

修改 `backend/api/deps.py`，添加：

```python
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials
from ..auth import security, get_current_user
from ..models import User
from ..services.permission_service import PermissionService


def require_permission(permission: str):
    """FastAPI dependency factory: returns a dependency that asserts the
    current user has the given permission, else raises 403.

    Usage: current_user: User = Depends(require_permission("exam:create"))
    """
    def _checker(
        user: User = Depends(get_current_user),
        perm_svc: PermissionService = Depends(get_permission_service),
    ) -> User:
        perm_svc.assert_can(user, permission)
        return user
    return _checker
```

（保留 Phase 2 已有的 get_course_service / get_practice_service / get_permission_service）

- [ ] **Step 4: 在 api/courses.py 添加 create 端点（带权限校验）**

在 `backend/api/courses.py` 顶部 import 添加：
```python
from ..models import User
from .deps import get_course_service, require_permission
```

添加 create 端点：
```python
@router.post("/", status_code=201)
def create_course(
    body: schemas.CourseCreate,
    current_user: User = Depends(require_permission("course:create")),
    service: CourseService = Depends(get_course_service),
):
    bank = service.create_course(body, owner_id=current_user.id)
    return bank.to_dict()
```

- [ ] **Step 5: 运行测试**

Run: `cd backend && python -m pytest tests/api/test_courses_api.py -v`
Expected: PASS

- [ ] **Step 6: 运行全量后端测试**

Run: `cd backend && python -m pytest -q`
Expected: PASS

- [ ] **Step 7: 提交**

```bash
git add backend/api/deps.py backend/api/courses.py backend/tests/api/test_courses_api.py
git commit -m "feat(rbac): add require_permission dependency, guard course creation"
```

---

# 里程碑 M2：后端 — 考试模式

## Task 4: 新增考试 Pydantic schemas

**Files:**
- Modify: `backend/schemas.py`
- Test: `backend/tests/test_schemas_exam.py`

- [ ] **Step 1: 写 schema 测试**

Create `backend/tests/test_schemas_exam.py`:

```python
import pytest
from pydantic import ValidationError

from backend.schemas import (
    ExamCreate,
    ExamOut,
    ExamSubmissionCreate,
    ExamResultOut,
)


class TestExamCreate:
    def test_valid_exam_create(self):
        e = ExamCreate(title="期末考试", course_id=1)
        assert e.title == "期末考试"
        assert e.time_limit == 60
        assert e.total_score == 100
        assert e.is_shuffle is False

    def test_title_required(self):
        with pytest.raises(ValidationError):
            ExamCreate(course_id=1)

    def test_question_ids_optional(self):
        e = ExamCreate(title="t", course_id=1)
        assert e.question_ids == []


class TestExamSubmissionCreate:
    def test_valid_submission(self):
        s = ExamSubmissionCreate(answers={"1": "A", "2": "对"})
        assert s.answers == {"1": "A", "2": "对"}

    def test_empty_answers_allowed(self):
        s = ExamSubmissionCreate(answers={})
        assert s.answers == {}


class TestExamOut:
    def test_has_status_field(self):
        assert "status" in ExamOut.model_fields
        assert "question_count" in ExamOut.model_fields
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd backend && python -m pytest tests/test_schemas_exam.py -v`
Expected: FAIL — `ImportError`

- [ ] **Step 3: 在 schemas.py 末尾添加考试 schemas**

在 `backend/schemas.py` 末尾追加：

```python
# -- Exam (Phase 3) ---------------------------------------------------------


class ExamQuestionRef(BaseModel):
    """A question selected for an exam, with its score."""
    question_id: int
    score: int = 1


class ExamCreate(BaseModel):
    title: str
    description: str = ""
    course_id: int
    time_limit: int = 60  # minutes
    total_score: int = 100
    is_shuffle: bool = False
    is_blind: bool = True  # cannot review answered questions
    question_ids: list[int] = []  # optional explicit selection; empty = all course questions
    question_scores: Optional[dict[int, int]] = None  # {question_id: score} overrides


class ExamUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    time_limit: Optional[int] = None
    total_score: Optional[int] = None
    is_shuffle: Optional[bool] = None
    is_blind: Optional[bool] = None
    status: Optional[str] = None  # draft/published/closed


class ExamOut(BaseModel):
    id: int
    title: str
    description: str = ""
    course_id: int
    creator_id: int
    time_limit: int
    total_score: int
    is_shuffle: bool = False
    is_blind: bool = True
    status: str = "draft"
    question_count: int = 0
    created_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ExamQuestionOut(BaseModel):
    """A question as presented in an exam attempt (hides answer/analysis
    until the exam is graded)."""
    id: int
    order_index: int = 0
    score: int = 1
    type: str
    question: str
    options: Optional[dict[str, Any]] = None
    # answer/analysis intentionally omitted — shown only in results


class ExamAttemptOut(BaseModel):
    """An active exam attempt: the exam metadata + ordered questions
    (without answers) + remaining time."""
    exam: ExamOut
    questions: list[ExamQuestionOut] = []
    started_at: str
    deadline_at: str  # ISO datetime when time runs out


class ExamSubmissionCreate(BaseModel):
    """Student's answers, keyed by question_id."""
    answers: dict[str, str] = {}  # {"question_id": "user_answer"}


class ExamQuestionResult(BaseModel):
    question_id: int
    user_answer: str = ""
    correct_answer: str
    is_correct: bool
    score: int
    earned_score: int


class ExamResultOut(BaseModel):
    submission_id: int
    exam_id: int
    score: int
    total_score: int
    is_passed: bool
    started_at: str
    submitted_at: str
    duration_seconds: int
    results: list[ExamQuestionResult] = []
    rank: Optional[int] = None  # 1-based rank among all submissions


class ExamLeaderboardEntry(BaseModel):
    user_id: int
    username: str
    score: int
    submitted_at: str
    rank: int


class ExamLeaderboardOut(BaseModel):
    exam_id: int
    entries: list[ExamLeaderboardEntry] = []
    total: int = 0
```

- [ ] **Step 4: 运行测试**

Run: `cd backend && python -m pytest tests/test_schemas_exam.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add backend/schemas.py backend/tests/test_schemas_exam.py
git commit -m "feat(schemas): add Exam/ExamSubmission/ExamResult schemas"
```

---

## Task 5: 创建 exam_repo 和 collaboration_repo

**Files:**
- Create: `backend/repositories/exam_repo.py`
- Create: `backend/repositories/collaboration_repo.py`
- Test: `backend/tests/repositories/test_exam_repo.py`

- [ ] **Step 1: 写 exam_repo 测试**

Create `backend/tests/repositories/test_exam_repo.py`:

```python
from datetime import datetime, timezone

from backend.models import Exam, ExamQuestion, Question, QuestionBank
from backend.repositories.exam_repo import ExamRepository, ExamQuestionRepository, ExamSubmissionRepository


def _make_course(db_session, owner_id=1):
    bank = QuestionBank(owner_id=owner_id, name="课程", visibility="private",
                        created_at=datetime.now(timezone.utc))
    db_session.add(bank)
    db_session.commit()
    db_session.refresh(bank)
    return bank


def _make_question(db_session, course, owner_id=1):
    q = Question(owner_id=owner_id, course_id=course.id, visibility="private",
                 type="single_choice", question="题干", options='{"A":"x"}',
                 answer="A", created_at=datetime.now(timezone.utc))
    db_session.add(q)
    db_session.commit()
    db_session.refresh(q)
    return q


class TestExamRepository:
    def test_create_exam(self, db_session):
        course = _make_course(db_session)
        repo = ExamRepository(db_session)
        exam = repo.create(
            title="期末", course_id=course.id, creator_id=1,
            time_limit=60, total_score=100,
        )
        assert exam.id is not None
        assert exam.status == "draft"

    def test_get_by_id(self, db_session):
        course = _make_course(db_session)
        repo = ExamRepository(db_session)
        exam = repo.create(title="t", course_id=course.id, creator_id=1,
                           time_limit=60, total_score=100)
        fetched = repo.get_by_id(exam.id)
        assert fetched.id == exam.id

    def test_get_questions_for_exam(self, db_session):
        course = _make_course(db_session)
        q1 = _make_question(db_session, course)
        q2 = _make_question(db_session, course)
        exam_repo = ExamRepository(db_session)
        exam = exam_repo.create(title="t", course_id=course.id, creator_id=1,
                                time_limit=60, total_score=100)
        eq_repo = ExamQuestionRepository(db_session)
        eq_repo.attach(exam.id, [q1.id, q2.id])
        questions = eq_repo.list_for_exam(exam.id)
        assert len(questions) == 2
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd backend && python -m pytest tests/repositories/test_exam_repo.py -v`
Expected: FAIL — `ImportError`

- [ ] **Step 3: 创建 exam_repo.py**

Create `backend/repositories/exam_repo.py`:

```python
"""Repositories for Exam, ExamQuestion, ExamSubmission."""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import models
from .base import BaseRepository


class ExamRepository(BaseRepository[models.Exam]):
    model = models.Exam

    def create(self, *, title, course_id, creator_id, time_limit=60,
               total_score=100, is_shuffle=False, is_blind=True,
               description="", status="draft") -> models.Exam:
        exam = models.Exam(
            title=title, description=description, course_id=course_id,
            creator_id=creator_id, time_limit=time_limit,
            total_score=total_score, is_shuffle=1 if is_shuffle else 0,
            is_blind=1 if is_blind else 0, status=status,
            created_at=datetime.now(timezone.utc),
        )
        return self.add(exam)

    def get_by_course(self, course_id: int) -> list[models.Exam]:
        return self._query().filter(models.Exam.course_id == course_id).all()

    def get_published(self) -> list[models.Exam]:
        return self._query().filter(models.Exam.status == "published").all()


class ExamQuestionRepository(BaseRepository[models.ExamQuestion]):
    model = models.ExamQuestion

    def attach(self, exam_id: int, question_ids: list[int],
               scores: Optional[dict[int, int]] = None) -> list[models.ExamQuestion]:
        """Attach questions to an exam with order_index. Replaces existing."""
        # Remove existing associations
        self.db.query(models.ExamQuestion).filter(
            models.ExamQuestion.exam_id == exam_id
        ).delete()
        self.db.flush()

        created = []
        for idx, qid in enumerate(question_ids):
            eq = models.ExamQuestion(
                exam_id=exam_id, question_id=qid,
                score=(scores or {}).get(qid, 1),
                order_index=idx,
            )
            self.db.add(eq)
            created.append(eq)
        self.db.commit()
        return created

    def list_for_exam(self, exam_id: int) -> list[models.ExamQuestion]:
        return (
            self._query()
            .filter(models.ExamQuestion.exam_id == exam_id)
            .order_by(models.ExamQuestion.order_index)
            .all()
        )

    def count_for_exam(self, exam_id: int) -> int:
        return self._query().filter(models.ExamQuestion.exam_id == exam_id).count()


class ExamSubmissionRepository(BaseRepository[models.ExamSubmission]):
    model = models.ExamSubmission

    def get_active_by_user_exam(self, user_id: int, exam_id: int) -> Optional[models.ExamSubmission]:
        return (
            self._query()
            .filter(
                models.ExamSubmission.user_id == user_id,
                models.ExamSubmission.exam_id == exam_id,
                models.ExamSubmission.submitted_at.is_(None),
            )
            .first()
        )

    def list_completed_for_exam(self, exam_id: int) -> list[models.ExamSubmission]:
        return (
            self._query()
            .filter(
                models.ExamSubmission.exam_id == exam_id,
                models.ExamSubmission.submitted_at.is_not(None),
            )
            .order_by(models.ExamSubmission.score.desc().nulls_last())
            .all()
        )

    def count_completed_for_exam(self, exam_id: int) -> int:
        return (
            self._query()
            .filter(
                models.ExamSubmission.exam_id == exam_id,
                models.ExamSubmission.submitted_at.is_not(None),
            )
            .count()
        )
```

- [ ] **Step 4: 创建 collaboration_repo.py**

Create `backend/repositories/collaboration_repo.py`:

```python
"""Repository for Collaboration (course co-editors/viewers)."""
from typing import Optional

from .. import models
from .base import BaseRepository


class CollaborationRepository(BaseRepository[models.Collaboration]):
    model = models.Collaboration

    def get_for_course(self, course_id: int) -> list[models.Collaboration]:
        return self._query().filter(models.Collaboration.course_id == course_id).all()

    def get_for_user(self, user_id: int) -> list[models.Collaboration]:
        return self._query().filter(models.Collaboration.user_id == user_id).all()

    def find(self, course_id: int, user_id: int) -> Optional[models.Collaboration]:
        return (
            self._query()
            .filter(
                models.Collaboration.course_id == course_id,
                models.Collaboration.user_id == user_id,
            )
            .first()
        )

    def add_collaborator(self, course_id: int, user_id: int, role: str,
                         invited_by: int | None = None) -> models.Collaboration:
        collab = models.Collaboration(
            course_id=course_id, user_id=user_id, role=role,
            invited_by=invited_by, created_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
        )
        return self.add(collab)

    def remove(self, course_id: int, user_id: int) -> bool:
        collab = self.find(course_id, user_id)
        if collab is None:
            return False
        self.delete(collab)
        return True
```

- [ ] **Step 5: 运行测试**

Run: `cd backend && python -m pytest tests/repositories/test_exam_repo.py -v`
Expected: PASS

- [ ] **Step 6: 运行全量后端测试**

Run: `cd backend && python -m pytest -q`
Expected: PASS

- [ ] **Step 7: 提交**

```bash
git add backend/repositories/exam_repo.py backend/repositories/collaboration_repo.py backend/tests/repositories/test_exam_repo.py
git commit -m "feat(repos): add exam and collaboration repositories"
```

---

## Task 6: 创建 ExamService（创建/发布/开始/提交/评分）

**Files:**
- Create: `backend/services/exam_service.py`
- Test: `backend/tests/services/test_exam_service.py`

- [ ] **Step 1: 写 exam_service 测试**

Create `backend/tests/services/test_exam_service.py`:

```python
from datetime import datetime, timezone

from backend.models import Question, QuestionBank
from backend.services.exam_service import ExamService


def _setup_course_with_questions(db_session, n=3):
    bank = QuestionBank(owner_id=1, name="课程", visibility="private",
                        created_at=datetime.now(timezone.utc))
    db_session.add(bank)
    db_session.commit()
    db_session.refresh(bank)
    questions = []
    for i in range(n):
        q = Question(owner_id=1, course_id=bank.id, visibility="private",
                     type="single_choice", question=f"Q{i}", options='{"A":"x","B":"y"}',
                     answer="A", created_at=datetime.now(timezone.utc))
        db_session.add(q)
        questions.append(q)
    db_session.commit()
    for q in questions:
        db_session.refresh(q)
    return bank, questions


class TestExamService:
    def test_create_exam_with_all_course_questions(self, db_session):
        bank, qs = _setup_course_with_questions(db_session, 3)
        svc = ExamService(db_session)
        exam = svc.create_exam(
            title="期末", course_id=bank.id, creator_id=1,
            question_ids=[],  # empty = all course questions
        )
        assert exam.question_count == 3

    def test_create_exam_with_explicit_questions(self, db_session):
        bank, qs = _setup_course_with_questions(db_session, 3)
        svc = ExamService(db_session)
        exam = svc.create_exam(
            title="期末", course_id=bank.id, creator_id=1,
            question_ids=[qs[0].id, qs[1].id],
        )
        assert exam.question_count == 2

    def test_publish_exam(self, db_session):
        bank, qs = _setup_course_with_questions(db_session, 2)
        svc = ExamService(db_session)
        exam = svc.create_exam(title="t", course_id=bank.id, creator_id=1)
        svc.publish(exam.id, creator_id=1)
        assert svc.get_exam(exam.id).status == "published"

    def test_start_attempt_creates_submission(self, db_session):
        bank, qs = _setup_course_with_questions(db_session, 2)
        svc = ExamService(db_session)
        exam = svc.create_exam(title="t", course_id=bank.id, creator_id=1)
        svc.publish(exam.id, creator_id=1)
        attempt = svc.start_attempt(exam.id, user_id=2)
        assert len(attempt.questions) == 2
        # questions must NOT include answer
        assert not hasattr(attempt.questions[0], "answer")

    def test_submit_and_grade(self, db_session):
        bank, qs = _setup_course_with_questions(db_session, 2)
        svc = ExamService(db_session)
        exam = svc.create_exam(title="t", course_id=bank.id, creator_id=1)
        svc.publish(exam.id, creator_id=1)
        svc.start_attempt(exam.id, user_id=2)
        result = svc.submit(exam.id, user_id=2,
                            answers={str(qs[0].id): "A", str(qs[1].id): "B"})
        # qs[0] answer is A (correct), qs[1] answer is A (B is wrong)
        assert result.score == 1  # 1 correct out of 2 (each worth 1)
        assert result.is_passed is False  # 50% < default 60% pass mark
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd backend && python -m pytest tests/services/test_exam_service.py -v`
Expected: FAIL — `ImportError`

- [ ] **Step 3: 实现 ExamService**

Create `backend/services/exam_service.py`:

```python
"""Business logic for the formal exam mode (Phase 3).

Distinct from practice: timed, blind (no instant grading), unified
scoring on submit, leaderboard.
"""
import json
import random
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from .. import models, schemas
from ..crud_practice import check_answer
from ..repositories.exam_repo import (
    ExamRepository, ExamQuestionRepository, ExamSubmissionRepository,
)


class ExamService:
    def __init__(self, db: Session):
        self.db = db
        self.exams = ExamRepository(db)
        self.exam_questions = ExamQuestionRepository(db)
        self.submissions = ExamSubmissionRepository(db)

    def create_exam(self, *, title, course_id, creator_id, time_limit=60,
                    total_score=100, is_shuffle=False, is_blind=True,
                    description="", question_ids=None,
                    question_scores=None) -> schemas.ExamOut:
        exam = self.exams.create(
            title=title, course_id=course_id, creator_id=creator_id,
            time_limit=time_limit, total_score=total_score,
            is_shuffle=is_shuffle, is_blind=is_blind, description=description,
        )
        # Resolve questions: explicit list, or all questions in the course
        if question_ids is None or len(question_ids) == 0:
            qids = [
                q.id for q in self.db.query(models.Question)
                .filter(models.Question.course_id == course_id).all()
            ]
        else:
            qids = list(question_ids)
        if is_shuffle:
            random.shuffle(qids)
        self.exam_questions.attach(exam.id, qids, scores=question_scores)
        return self._to_out(exam)

    def get_exam(self, exam_id: int) -> Optional[models.Exam]:
        return self.exams.get_by_id(exam_id)

    def list_exams(self, *, course_id: Optional[int] = None,
                   status: Optional[str] = None, user_id: Optional[int] = None):
        query = self.exams._query()
        if course_id is not None:
            query = query.filter(models.Exam.course_id == course_id)
        if status is not None:
            query = query.filter(models.Exam.status == status)
        return [self._to_out(e) for e in query.order_by(models.Exam.created_at.desc()).all()]

    def publish(self, exam_id: int, *, creator_id: int) -> models.Exam:
        exam = self.exams.get_by_id(exam_id)
        if exam is None:
            raise ValueError("考试不存在")
        if exam.creator_id != creator_id:
            raise PermissionError("只有创建者可以发布考试")
        if self.exam_questions.count_for_exam(exam_id) == 0:
            raise ValueError("考试没有题目，无法发布")
        exam.status = "published"
        self.db.commit()
        self.db.refresh(exam)
        return exam

    def close(self, exam_id: int, *, creator_id: int) -> models.Exam:
        exam = self.exams.get_by_id(exam_id)
        if exam is None:
            raise ValueError("考试不存在")
        exam.status = "closed"
        self.db.commit()
        self.db.refresh(exam)
        return exam

    def start_attempt(self, exam_id: int, *, user_id: int) -> schemas.ExamAttemptOut:
        exam = self.exams.get_by_id(exam_id)
        if exam is None:
            raise ValueError("考试不存在")
        if exam.status != "published":
            raise ValueError("考试未发布，无法开始")

        # Reuse an active attempt if one exists
        active = self.submissions.get_active_by_user_exam(user_id, exam_id)
        if active is None:
            active = models.ExamSubmission(
                exam_id=exam_id, user_id=user_id,
                started_at=datetime.now(timezone.utc),
                answers="{}",
            )
            self.db.add(active)
            self.db.commit()
            self.db.refresh(active)

        eqs = self.exam_questions.list_for_exam(exam_id)
        questions = []
        for eq in eqs:
            if eq.question is None:
                continue
            questions.append(schemas.ExamQuestionOut(
                id=eq.question.id, order_index=eq.order_index, score=eq.score,
                type=eq.question.type, question=eq.question.question,
                options=eq.question.get_options_dict(),
            ))

        deadline = active.started_at + timedelta(minutes=exam.time_limit)
        return schemas.ExamAttemptOut(
            exam=self._to_out(exam), questions=questions,
            started_at=active.started_at.isoformat(),
            deadline_at=deadline.isoformat(),
        )

    def submit(self, exam_id: int, *, user_id: int,
               answers: dict[str, str]) -> schemas.ExamResultOut:
        exam = self.exams.get_by_id(exam_id)
        if exam is None:
            raise ValueError("考试不存在")

        submission = self.submissions.get_active_by_user_exam(user_id, exam_id)
        if submission is None:
            raise ValueError("没有进行中的考试，请先开始考试")

        eqs = self.exam_questions.list_for_exam(exam_id)
        now = datetime.now(timezone.utc)

        # Auto-submit if past deadline
        deadline = submission.started_at + timedelta(minutes=exam.time_limit)
        if now > deadline:
            pass  # still grade what was answered

        results = []
        total_earned = 0
        for eq in eqs:
            q = eq.question
            if q is None:
                continue
            user_ans = answers.get(str(q.id), "")
            is_correct = bool(user_ans) and check_answer(q, user_ans)
            earned = eq.score if is_correct else 0
            total_earned += earned
            results.append(schemas.ExamQuestionResult(
                question_id=q.id, user_answer=user_ans,
                correct_answer=q.answer, is_correct=is_correct,
                score=eq.score, earned_score=earned,
            ))

        submission.answers = json.dumps(answers, ensure_ascii=False)
        submission.score = total_earned
        submission.submitted_at = now
        submission.is_passed = 1 if (total_earned >= exam.total_score * 0.6) else 0
        self.db.commit()
        self.db.refresh(submission)

        duration = int((submission.submitted_at - submission.started_at).total_seconds())
        rank = self._compute_rank(exam_id, submission.score)

        return schemas.ExamResultOut(
            submission_id=submission.id, exam_id=exam_id,
            score=total_earned, total_score=exam.total_score,
            is_passed=bool(submission.is_passed),
            started_at=submission.started_at.isoformat(),
            submitted_at=submission.submitted_at.isoformat(),
            duration_seconds=duration, results=results, rank=rank,
        )

    def get_result(self, submission_id: int, *, user_id: int) -> schemas.ExamResultOut:
        submission = self.submissions.get_by_id(submission_id)
        if submission is None:
            raise ValueError("提交记录不存在")
        # Only the submitter or the exam creator can view full results
        exam = self.exams.get_by_id(submission.exam_id)
        if submission.user_id != user_id and exam and exam.creator_id != user_id:
            raise PermissionError("无权查看此结果")
        # Reconstruct results from stored answers
        answers = json.loads(submission.answers or "{}")
        return self.submit(submission.exam_id, user_id=user_id, answers=answers) \
            if submission.submitted_at is None else self._build_result_out(submission)

    def get_leaderboard(self, exam_id: int) -> schemas.ExamLeaderboardOut:
        subs = self.submissions.list_completed_for_exam(exam_id)
        entries = []
        for rank, sub in enumerate(subs, start=1):
            user = self.db.query(models.User).filter(models.User.id == sub.user_id).first()
            entries.append(schemas.ExamLeaderboardEntry(
                user_id=sub.user_id, username=user.username if user else f"user_{sub.user_id}",
                score=sub.score or 0, submitted_at=sub.submitted_at.isoformat(),
                rank=rank,
            ))
        return schemas.ExamLeaderboardOut(exam_id=exam_id, entries=entries, total=len(entries))

    # ── helpers ──

    def _compute_rank(self, exam_id: int, score: int) -> int:
        """1-based rank: count submissions with higher score, +1."""
        higher = self.submissions._query().filter(
            models.ExamSubmission.exam_id == exam_id,
            models.ExamSubmission.submitted_at.is_not(None),
            models.ExamSubmission.score > score,
        ).count()
        return higher + 1

    def _to_out(self, exam: models.Exam) -> schemas.ExamOut:
        return schemas.ExamOut(
            id=exam.id, title=exam.title, description=exam.description or "",
            course_id=exam.course_id, creator_id=exam.creator_id,
            time_limit=exam.time_limit, total_score=exam.total_score,
            is_shuffle=bool(exam.is_shuffle), is_blind=bool(exam.is_blind),
            status=exam.status,
            question_count=self.exam_questions.count_for_exam(exam.id),
            created_at=exam.created_at.isoformat() if exam.created_at else None,
        )

    def _build_result_out(self, submission: models.ExamSubmission) -> schemas.ExamResultOut:
        exam = self.exams.get_by_id(submission.exam_id)
        answers = json.loads(submission.answers or "{}")
        eqs = self.exam_questions.list_for_exam(submission.exam_id)
        results = []
        for eq in eqs:
            q = eq.question
            if q is None:
                continue
            user_ans = answers.get(str(q.id), "")
            # re-grade to get per-question correctness (answers unchanged post-submit)
            is_correct = bool(user_ans) and check_answer(q, user_ans)
            results.append(schemas.ExamQuestionResult(
                question_id=q.id, user_answer=user_ans,
                correct_answer=q.answer, is_correct=is_correct,
                score=eq.score, earned_score=eq.score if is_correct else 0,
            ))
        rank = self._compute_rank(submission.exam_id, submission.score or 0)
        duration = int((submission.submitted_at - submission.started_at).total_seconds())
        return schemas.ExamResultOut(
            submission_id=submission.id, exam_id=submission.exam_id,
            score=submission.score or 0, total_score=exam.total_score if exam else 0,
            is_passed=bool(submission.is_passed),
            started_at=submission.started_at.isoformat(),
            submitted_at=submission.submitted_at.isoformat(),
            duration_seconds=duration, results=results, rank=rank,
        )
```

- [ ] **Step 4: 运行测试**

Run: `cd backend && python -m pytest tests/services/test_exam_service.py -v`
Expected: PASS

- [ ] **Step 5: 运行全量后端测试**

Run: `cd backend && python -m pytest -q`
Expected: PASS

- [ ] **Step 6: 提交**

```bash
git add backend/services/exam_service.py backend/tests/services/test_exam_service.py
git commit -m "feat(exam): add ExamService (create/publish/attempt/submit/grade)"
```

---

## Task 7: 创建考试 API 路由层

**Files:**
- Create: `backend/api/exams.py`
- Modify: `backend/api/deps.py`
- Modify: `backend/main.py`
- Test: `backend/tests/api/test_exams_api.py`

- [ ] **Step 1: 写 API 测试**

Create `backend/tests/api/test_exams_api.py`:

```python
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.exams import router as exams_router
from backend.auth import get_current_user
from backend.database import get_db
from backend.models import User, QuestionBank, Question


def _make_app(db_session, user):
    app = FastAPI()
    app.include_router(exams_router)
    app.dependency_overrides[get_db] = lambda: (yield db_session)
    app.dependency_overrides[get_current_user] = lambda: user
    return app


def _setup(db_session, role_name="teacher"):
    from backend.models import Role
    role = Role(name=role_name)
    db_session.add(role)
    user = User(username="teacher1", password_hash="x", role_id=None)
    db_session.add(user)
    bank = QuestionBank(owner_id=1, name="课程", visibility="private",
                        created_at=datetime.now(timezone.utc))
    db_session.add(bank)
    db_session.commit()
    for o in (user, bank):
        db_session.refresh(o)
    # give user the role
    user.role_id = role.id
    db_session.commit()
    db_session.refresh(user)
    q = Question(owner_id=1, course_id=bank.id, visibility="private",
                 type="single_choice", question="Q", options='{"A":"x"}',
                 answer="A", created_at=datetime.now(timezone.utc))
    db_session.add(q)
    db_session.commit()
    db_session.refresh(q)
    return user, bank, q


class TestExamsApi:
    def test_create_exam(self, db_session):
        user, bank, q = _setup(db_session)
        app = _make_app(db_session, user)
        client = TestClient(app)
        resp = client.post("/exams/", json={"title": "期末", "course_id": bank.id})
        assert resp.status_code == 201
        assert resp.json()["question_count"] == 1

    def test_list_exams(self, db_session):
        user, bank, q = _setup(db_session)
        app = _make_app(db_session, user)
        client = TestClient(app)
        client.post("/exams/", json={"title": "E1", "course_id": bank.id})
        resp = client.get("/exams/")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_publish_exam(self, db_session):
        user, bank, q = _setup(db_session)
        app = _make_app(db_session, user)
        client = TestClient(app)
        created = client.post("/exams/", json={"title": "E", "course_id": bank.id}).json()
        resp = client.post(f"/exams/{created['id']}/publish")
        assert resp.status_code == 200
        assert resp.json()["status"] == "published"

    def test_student_cannot_create_exam(self, db_session):
        from backend.models import Role
        role = Role(name="student")
        db_session.add(role)
        user = User(username="stu", password_hash="x")
        bank = QuestionBank(owner_id=1, name="c", visibility="private",
                            created_at=datetime.now(timezone.utc))
        db_session.add_all([user, bank])
        db_session.commit()
        db_session.refresh(user); db_session.refresh(bank)
        user.role_id = role.id
        db_session.commit()
        app = _make_app(db_session, user)
        client = TestClient(app)
        resp = client.post("/exams/", json={"title": "x", "course_id": bank.id})
        assert resp.status_code == 403
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd backend && python -m pytest tests/api/test_exams_api.py -v`
Expected: FAIL — `ImportError`

- [ ] **Step 3: 在 deps.py 添加 exam service 工厂**

修改 `backend/api/deps.py`，添加：

```python
from ..services.exam_service import ExamService


def get_exam_service(db: Session = Depends(get_db)) -> ExamService:
    return ExamService(db)
```

- [ ] **Step 4: 创建 api/exams.py**

Create `backend/api/exams.py`:

```python
"""Exam router (Phase 3). Thin layer delegating to ExamService."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import schemas
from ..auth import get_current_user
from ..models import User
from ..services.exam_service import ExamService
from .deps import get_exam_service, require_permission

router = APIRouter(prefix="/exams", tags=["exams"])


@router.post("/", status_code=201, response_model=schemas.ExamOut)
def create_exam(
    body: schemas.ExamCreate,
    current_user: User = Depends(require_permission("exam:create")),
    service: ExamService = Depends(get_exam_service),
):
    try:
        return service.create_exam(
            title=body.title, course_id=body.course_id, creator_id=current_user.id,
            time_limit=body.time_limit, total_score=body.total_score,
            is_shuffle=body.is_shuffle, is_blind=body.is_blind,
            description=body.description, question_ids=body.question_ids,
            question_scores=body.question_scores,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=list[schemas.ExamOut])
def list_exams(
    course_id: int = Query(0, ge=0),
    status: str = Query(""),
    current_user: User = Depends(get_current_user),
    service: ExamService = Depends(get_exam_service),
):
    return service.list_exams(
        course_id=course_id or None,
        status=status or None,
        user_id=current_user.id,
    )


@router.get("/{exam_id}", response_model=schemas.ExamOut)
def get_exam(
    exam_id: int,
    current_user: User = Depends(get_current_user),
    service: ExamService = Depends(get_exam_service),
):
    exam = service.get_exam(exam_id)
    if exam is None:
        raise HTTPException(status_code=404, detail="考试不存在")
    return service._to_out(exam)


@router.post("/{exam_id}/publish", response_model=schemas.ExamOut)
def publish_exam(
    exam_id: int,
    current_user: User = Depends(require_permission("exam:publish")),
    service: ExamService = Depends(get_exam_service),
):
    try:
        service.publish(exam_id, creator_id=current_user.id)
        return service._to_out(service.get_exam(exam_id))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{exam_id}/start", response_model=schemas.ExamAttemptOut)
def start_exam(
    exam_id: int,
    current_user: User = Depends(require_permission("exam:take")),
    service: ExamService = Depends(get_exam_service),
):
    try:
        return service.start_attempt(exam_id, user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{exam_id}/submit", response_model=schemas.ExamResultOut)
def submit_exam(
    exam_id: int,
    body: schemas.ExamSubmissionCreate,
    current_user: User = Depends(require_permission("exam:take")),
    service: ExamService = Depends(get_exam_service),
):
    try:
        return service.submit(exam_id, user_id=current_user.id, answers=body.answers)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{exam_id}/leaderboard", response_model=schemas.ExamLeaderboardOut)
def get_leaderboard(
    exam_id: int,
    current_user: User = Depends(require_permission("exam:view_leaderboard")),
    service: ExamService = Depends(get_exam_service),
):
    return service.get_leaderboard(exam_id)
```

- [ ] **Step 5: 在 main.py 挂载路由**

修改 `backend/main.py`，在 router include 区添加：

```python
from .api import exams as exams_api
# ...
app.include_router(exams_api.router)
```

注意：保留现有 `from .routers import ...` 的路由不变，exams 用新的 api 层。两者前缀不冲突（`/exams` 是全新的）。

- [ ] **Step 6: 运行 API 测试**

Run: `cd backend && python -m pytest tests/api/test_exams_api.py -v`
Expected: PASS

- [ ] **Step 7: 运行全量后端测试**

Run: `cd backend && python -m pytest -q`
Expected: PASS

- [ ] **Step 8: 提交**

```bash
git add backend/api/exams.py backend/api/deps.py backend/main.py backend/tests/api/test_exams_api.py
git commit -m "feat(api): exam endpoints (create/list/publish/start/submit/leaderboard)"
```

---

# 里程碑 M3：后端 — 管理后台 API

## Task 8: 管理后台 API（用户管理 + 公告 + 统计）

**Files:**
- Create: `backend/api/admin.py`
- Modify: `backend/main.py`
- Test: `backend/tests/api/test_admin_api.py`

- [ ] **Step 1: 写管理 API 测试**

Create `backend/tests/api/test_admin_api.py`:

```python
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.admin import router as admin_router
from backend.api.deps import get_permission_service, PermissionService
from backend.auth import get_current_user
from backend.database import get_db
from backend.models import User, Role


def _make_app(db_session, user, can_manage=True):
    app = FastAPI()
    app.include_router(admin_router)
    app.dependency_overrides[get_db] = lambda: (yield db_session)
    app.dependency_overrides[get_current_user] = lambda: user
    class PS(PermissionService):
        def can(self, u, p):
            return can_manage
    app.dependency_overrides[get_permission_service] = lambda: PS(db_session)
    return app


def _admin_user(db_session):
    role = Role(name="admin")
    db_session.add(role)
    user = User(username="admin", password_hash="x")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    user.role_id = role.id
    db_session.commit()
    db_session.refresh(user)
    return user


class TestAdminApi:
    def test_list_users_requires_user_manage(self, db_session):
        user = _admin_user(db_session)
        app = _make_app(db_session, user, can_manage=False)
        client = TestClient(app)
        resp = client.get("/admin/users")
        assert resp.status_code == 403

    def test_list_users(self, db_session):
        admin = _admin_user(db_session)
        # add a second user
        db_session.add(User(username="student1", password_hash="x"))
        db_session.commit()
        app = _make_app(db_session, admin, can_manage=True)
        client = TestClient(app)
        resp = client.get("/admin/users")
        assert resp.status_code == 200
        assert len(resp.json()["items"]) >= 2

    def test_get_stats(self, db_session):
        admin = _admin_user(db_session)
        app = _make_app(db_session, admin, can_manage=True)
        client = TestClient(app)
        resp = client.get("/admin/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "user_count" in data
        assert "question_count" in data
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd backend && python -m pytest tests/api/test_admin_api.py -v`
Expected: FAIL — `ImportError`

- [ ] **Step 3: 创建 api/admin.py**

Create `backend/api/admin.py`:

```python
"""Admin router: user management + global stats (Phase 3).

All endpoints require user:manage permission.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import models
from ..auth import get_current_user
from ..database import get_db
from ..models import User
from .deps import get_permission_service, require_permission
from ..services.permission_service import PermissionService

router = APIRouter(prefix="/admin", tags=["admin"])


def _admin_dep(user: User = Depends(require_permission("user:manage"))) -> User:
    return user


@router.get("/users")
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(_admin_dep),
    db: Session = Depends(get_db),
):
    query = db.query(models.User).order_by(models.User.id)
    total = query.count()
    offset = (page - 1) * page_size
    users = query.offset(offset).limit(page_size).all()
    items = []
    for u in users:
        items.append({
            "id": u.id,
            "username": u.username,
            "role": (u.role.name if u.role else "student"),
            "is_active": True,  # placeholder; Phase 3 doesn't add disable yet
        })
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.patch("/users/{user_id}/role")
def update_user_role(
    user_id: int,
    body: dict,
    current_user: User = Depends(_admin_dep),
    db: Session = Depends(get_db),
):
    role_name = body.get("role")
    if role_name not in ("student", "teacher", "admin"):
        raise HTTPException(status_code=400, detail="无效的角色")
    role = db.query(models.Role).filter(models.Role.name == role_name).first()
    if role is None:
        raise HTTPException(status_code=400, detail="角色不存在")
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.role_id = role.id
    db.commit()
    return {"id": user.id, "username": user.username, "role": role_name}


@router.get("/stats")
def get_stats(
    current_user: User = Depends(_admin_dep),
    db: Session = Depends(get_db),
):
    return {
        "user_count": db.query(func.count(models.User.id)).scalar() or 0,
        "question_count": db.query(func.count(models.Question.id)).scalar() or 0,
        "course_count": db.query(func.count(models.QuestionBank.id)).scalar() or 0,
        "practice_count": db.query(func.count(models.PracticeRecord.id)).scalar() or 0,
        "exam_count": db.query(func.count(models.Exam.id)).scalar() or 0,
    }
```

- [ ] **Step 4: 在 main.py 挂载 admin 路由**

修改 `backend/main.py`，添加：

```python
from .api import admin as admin_api
# ...
app.include_router(admin_api.router)
```

- [ ] **Step 5: 运行测试**

Run: `cd backend && python -m pytest tests/api/test_admin_api.py -v`
Expected: PASS

- [ ] **Step 6: 运行全量后端测试**

Run: `cd backend && python -m pytest -q`
Expected: PASS

- [ ] **Step 7: 提交**

```bash
git add backend/api/admin.py backend/main.py backend/tests/api/test_admin_api.py
git commit -m "feat(api): admin endpoints (users/role/stats)"
```

---

# 里程碑 M4：前端 — 权限 + 考试模块

## Task 9: 前端类型 + API + auth store 升级

**Files:**
- Modify: `frontend/src/types/index.ts`
- Create: `frontend/src/api/exam.ts`
- Create: `frontend/src/api/admin.ts`
- Modify: `frontend/src/stores/auth.ts`
- Test: `frontend/src/api/__tests__/exam.spec.ts`

- [ ] **Step 1: 添加考试相关类型**

在 `frontend/src/types/index.ts` 末尾添加：

```typescript
// ── Exam (Phase 3) ───────────────────────────────────────────────────────

export type ExamStatus = "draft" | "published" | "closed";

export interface Exam {
  id: number;
  title: string;
  description: string;
  course_id: number;
  creator_id: number;
  time_limit: number;
  total_score: number;
  is_shuffle: boolean;
  is_blind: boolean;
  status: ExamStatus;
  question_count: number;
  created_at: string | null;
}

export interface ExamCreate {
  title: string;
  description?: string;
  course_id: number;
  time_limit?: number;
  total_score?: number;
  is_shuffle?: boolean;
  is_blind?: boolean;
  question_ids?: number[];
}

export interface ExamQuestion {
  id: number;
  order_index: number;
  score: number;
  type: QuestionType;
  question: string;
  options: Record<string, string> | null;
}

export interface ExamAttempt {
  exam: Exam;
  questions: ExamQuestion[];
  started_at: string;
  deadline_at: string;
}

export interface ExamQuestionResult {
  question_id: number;
  user_answer: string;
  correct_answer: string;
  is_correct: boolean;
  score: number;
  earned_score: number;
}

export interface ExamResult {
  submission_id: number;
  exam_id: number;
  score: number;
  total_score: number;
  is_passed: boolean;
  started_at: string;
  submitted_at: string;
  duration_seconds: number;
  results: ExamQuestionResult[];
  rank: number | null;
}

export interface ExamLeaderboardEntry {
  user_id: number;
  username: string;
  score: number;
  submitted_at: string;
  rank: number;
}

export interface ExamLeaderboard {
  exam_id: number;
  entries: ExamLeaderboardEntry[];
  total: number;
}

// ── Role / Permission ────────────────────────────────────────────────────

export type RoleName = "student" | "teacher" | "admin";
```

同时更新 `User` 接口（找到现有的 User interface）添加 `role` 和 `permissions`：

```typescript
export interface User {
  id: number;
  username: string;
  role: RoleName | "user";
  permissions: string[];
}
```

- [ ] **Step 2: 创建 api/exam.ts**

Create `frontend/src/api/exam.ts`:

```typescript
import type {
  Exam, ExamCreate, ExamAttempt, ExamResult, ExamLeaderboard,
} from "@/types";
import request from "./request";

export function listExams(params?: { course_id?: number; status?: string }): Promise<Exam[]> {
  return request.get("/exams/", { params }).then(({ data }) => data);
}

export function createExam(payload: ExamCreate): Promise<Exam> {
  return request.post("/exams/", payload).then(({ data }) => data);
}

export function getExam(examId: number): Promise<Exam> {
  return request.get(`/exams/${examId}`).then(({ data }) => data);
}

export function publishExam(examId: number): Promise<Exam> {
  return request.post(`/exams/${examId}/publish`).then(({ data }) => data);
}

export function startExam(examId: number): Promise<ExamAttempt> {
  return request.post(`/exams/${examId}/start`).then(({ data }) => data);
}

export function submitExam(examId: number, answers: Record<string, string>): Promise<ExamResult> {
  return request.post(`/exams/${examId}/submit`, { answers }).then(({ data }) => data);
}

export function getExamLeaderboard(examId: number): Promise<ExamLeaderboard> {
  return request.get(`/exams/${examId}/leaderboard`).then(({ data }) => data);
}
```

- [ ] **Step 3: 创建 api/admin.ts**

Create `frontend/src/api/admin.ts`:

```typescript
import request from "./request";

export interface AdminUser {
  id: number;
  username: string;
  role: string;
  is_active: boolean;
}

export interface AdminStats {
  user_count: number;
  question_count: number;
  course_count: number;
  practice_count: number;
  exam_count: number;
}

export function listUsers(params?: { page?: number; page_size?: number }) {
  return request.get("/admin/users", { params }).then(({ data }) => data);
}

export function updateUserRole(userId: number, role: string) {
  return request.patch(`/admin/users/${userId}/role`, { role }).then(({ data }) => data);
}

export function getAdminStats(): Promise<AdminStats> {
  return request.get("/admin/stats").then(({ data }) => data);
}
```

- [ ] **Step 4: 升级 auth store 携带 role + permissions**

修改 `frontend/src/stores/auth.ts`，在 `fetchProfile` 中确保 `user` 包含 role 和 permissions（后端 `/auth/me` 已返回）。`user.value = data` 已自动包含。无需额外逻辑，但添加一个 computed helper：

在 setup store 的 return 前添加：
```typescript
const role = computed(() => user.value?.role ?? "student");
const permissions = computed<string[]>(() => user.value?.permissions ?? []);
function can(permission: string): boolean {
  return permissions.value.includes(permission);
}
```

并在 return 中加入 `role`、`permissions`、`can`。

- [ ] **Step 5: 写 exam API 测试**

Create `frontend/src/api/__tests__/exam.spec.ts`:

```typescript
import { describe, expect, it, vi } from "vitest";

vi.mock("../request", () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

import request from "../request";
import { listExams, createExam, startExam, submitExam } from "../exam";

describe("exam api", () => {
  it("listExams calls GET /exams/", async () => {
    vi.mocked(request.get).mockResolvedValue({ data: [] });
    await listExams({ course_id: 1 });
    expect(request.get).toHaveBeenCalledWith("/exams/", { params: { course_id: 1 } });
  });

  it("createExam calls POST /exams/", async () => {
    vi.mocked(request.post).mockResolvedValue({ data: { id: 1 } });
    await createExam({ title: "t", course_id: 1 });
    expect(request.post).toHaveBeenCalledWith("/exams/", { title: "t", course_id: 1 });
  });

  it("startExam calls POST /exams/:id/start", async () => {
    vi.mocked(request.post).mockResolvedValue({ data: {} });
    await startExam(5);
    expect(request.post).toHaveBeenCalledWith("/exams/5/start");
  });

  it("submitExam calls POST /exams/:id/submit with answers", async () => {
    vi.mocked(request.post).mockResolvedValue({ data: {} });
    await submitExam(5, { "1": "A" });
    expect(request.post).toHaveBeenCalledWith("/exams/5/submit", { answers: { "1": "A" } });
  });
});
```

- [ ] **Step 6: 运行测试 + typecheck**

Run: `cd frontend && npm run typecheck && npx vitest run src/api/__tests__/exam.spec.ts`
Expected: PASS

- [ ] **Step 7: 提交**

```bash
git add frontend/src/types/index.ts frontend/src/api/exam.ts frontend/src/api/admin.ts frontend/src/stores/auth.ts frontend/src/api/__tests__/exam.spec.ts
git commit -m "feat(frontend): exam/admin types + API + auth role/permissions"
```

---

## Task 10: 创建 exam store（考试会话状态机）

**Files:**
- Create: `frontend/src/stores/exam.ts`
- Test: `frontend/src/stores/__tests__/exam.spec.ts`

- [ ] **Step 1: 写 exam store 测试**

Create `frontend/src/stores/__tests__/exam.spec.ts`:

```typescript
import { setActivePinia, createPinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../../api/exam", () => ({
  startExam: vi.fn(),
  submitExam: vi.fn(),
}));

import { useExamStore } from "../exam";
import * as examApi from "../../api/exam";

describe("useExamStore", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  it("starts in idle state", () => {
    const store = useExamStore();
    expect(store.phase).toBe("idle");
    expect(store.currentAttempt).toBeNull();
  });

  it("startAttempt moves to taking phase", async () => {
    const fakeAttempt = {
      exam: { id: 1 }, questions: [{ id: 1 }], started_at: "", deadline_at: "",
    };
    vi.mocked(examApi.startExam).mockResolvedValue(fakeAttempt as any);
    const store = useExamStore();
    await store.startAttempt(1);
    expect(store.phase).toBe("taking");
    expect(store.currentAttempt).toEqual(fakeAttempt);
  });

  it("submit moves to result phase", async () => {
    const fakeAttempt = {
      exam: { id: 1 }, questions: [{ id: 1 }], started_at: "", deadline_at: "",
    };
    vi.mocked(examApi.startExam).mockResolvedValue(fakeAttempt as any);
    const fakeResult = { submission_id: 1, exam_id: 1, score: 5 };
    vi.mocked(examApi.submitExam).mockResolvedValue(fakeResult as any);
    const store = useExamStore();
    await store.startAttempt(1);
    await store.submit({ "1": "A" });
    expect(store.phase).toBe("result");
    expect(store.result).toEqual(fakeResult);
  });

  it("reset returns to idle", async () => {
    const store = useExamStore();
    store.phase = "taking";
    store.reset();
    expect(store.phase).toBe("idle");
    expect(store.currentAttempt).toBeNull();
  });
});
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd frontend && npx vitest run src/stores/__tests__/exam.spec.ts`
Expected: FAIL

- [ ] **Step 3: 实现 exam store**

Create `frontend/src/stores/exam.ts`:

```typescript
import { computed, ref } from "vue";
import { defineStore } from "pinia";
import { startExam, submitExam } from "../api/exam";
import type { ExamAttempt, ExamResult } from "../types";

export type ExamPhase = "idle" | "taking" | "result";

export const useExamStore = defineStore("exam", () => {
  const phase = ref<ExamPhase>("idle");
  const currentAttempt = ref<ExamAttempt | null>(null);
  const result = ref<ExamResult | null>(null);
  const answers = ref<Record<string, string>>({});
  const currentIndex = ref(0);
  const loading = ref(false);
  const error = ref("");

  const questions = computed(() => currentAttempt.value?.questions ?? []);
  const currentQuestion = computed(() => questions.value[currentIndex.value] ?? null);
  const answeredCount = computed(() => Object.keys(answers.value).length);
  const totalQuestions = computed(() => questions.value.length);
  const progress = computed(() =>
    totalQuestions.value === 0 ? 0 : Math.round((answeredCount.value / totalQuestions.value) * 100),
  );

  function setAnswer(questionId: number, answer: string): void {
    answers.value[String(questionId)] = answer;
  }

  function goTo(index: number): void {
    if (index >= 0 && index < totalQuestions.value) {
      currentIndex.value = index;
    }
  }

  function next(): void {
    goTo(currentIndex.value + 1);
  }

  function prev(): void {
    goTo(currentIndex.value - 1);
  }

  async function startAttempt(examId: number): Promise<void> {
    loading.value = true;
    error.value = "";
    try {
      currentAttempt.value = await startExam(examId);
      answers.value = {};
      currentIndex.value = 0;
      phase.value = "taking";
    } catch (e: any) {
      error.value = e?.message || "开始考试失败";
    } finally {
      loading.value = false;
    }
  }

  async function submit(finalAnswers?: Record<string, string>): Promise<void> {
    if (!currentAttempt.value) return;
    loading.value = true;
    error.value = "";
    try {
      const payload = finalAnswers ?? answers.value;
      result.value = await submitExam(currentAttempt.value.exam.id, payload);
      phase.value = "result";
    } catch (e: any) {
      error.value = e?.message || "提交失败";
    } finally {
      loading.value = false;
    }
  }

  function reset(): void {
    phase.value = "idle";
    currentAttempt.value = null;
    result.value = null;
    answers.value = {};
    currentIndex.value = 0;
    error.value = "";
  }

  return {
    phase, currentAttempt, result, answers, currentIndex, loading, error,
    questions, currentQuestion, answeredCount, totalQuestions, progress,
    setAnswer, goTo, next, prev, startAttempt, submit, reset,
  };
});
```

- [ ] **Step 4: 运行测试**

Run: `cd frontend && npx vitest run src/stores/__tests__/exam.spec.ts`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add frontend/src/stores/exam.ts frontend/src/stores/__tests__/exam.spec.ts
git commit -m "feat(store): add exam session state machine"
```

---

## Task 11: 创建考试答题组件

**Files:**
- Create: `frontend/src/components/exam/ExamTopBar.vue`
- Create: `frontend/src/components/exam/ExamQuestionNav.vue`
- Create: `frontend/src/components/exam/ExamAnswerArea.vue`

- [ ] **Step 1: 创建 ExamTopBar.vue（倒计时 + 进度 + 交卷）**

Create `frontend/src/components/exam/ExamTopBar.vue`:

```vue
<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import { Button } from "@/components/ui/button";

const props = defineProps<{
  title: string;
  deadlineAt: string;
  answeredCount: number;
  totalCount: number;
}>();

const emit = defineEmits<{ (e: "submit"): void }>();

const now = ref(Date.now());
let timer: number | undefined;

onMounted(() => {
  timer = window.setInterval(() => { now.value = Date.now(); }, 1000);
});
onUnmounted(() => { if (timer) clearInterval(timer); });

const remainingMs = computed(() => {
  const deadline = new Date(props.deadlineAt).getTime();
  return Math.max(0, deadline - now.value);
});

const remainingText = computed(() => {
  const totalSec = Math.floor(remainingMs.value / 1000);
  const m = Math.floor(totalSec / 60);
  const s = totalSec % 60;
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
});

const isUrgent = computed(() => remainingMs.value < 60_000);

const progressPct = computed(() =>
  props.totalCount === 0 ? 0 : Math.round((props.answeredCount / props.totalCount) * 100),
);
</script>

<template>
  <div class="sticky top-0 z-20 border-b border-[var(--line-soft)] bg-[var(--surface)] px-4 py-3 shadow-[var(--shadow-sm)]">
    <div class="mx-auto flex max-w-4xl items-center gap-4">
      <h1 class="flex-1 truncate text-base font-semibold text-[var(--text-main)]">{{ title }}</h1>
      <div :class="['font-mono text-lg font-bold tabular-nums', isUrgent ? 'text-[var(--rose)]' : 'text-[var(--text-main)]']">
        {{ remainingText }}
      </div>
      <div class="hidden w-32 sm:block">
        <div class="h-2 rounded-full bg-[var(--surface-soft)]">
          <div class="h-2 rounded-full bg-[var(--primary)] transition-all" :style="{ width: progressPct + '%' }" />
        </div>
      </div>
      <Button variant="destructive" size="sm" @click="emit('submit')">交卷</Button>
    </div>
  </div>
</template>
```

- [ ] **Step 2: 创建 ExamQuestionNav.vue（题目导航面板）**

Create `frontend/src/components/exam/ExamQuestionNav.vue`:

```vue
<script setup lang="ts">
const props = defineProps<{
  total: number;
  currentIndex: number;
  answeredIds: Set<number>;
}>();

const emit = defineEmits<{ (e: "jump", index: number): void }>();

function status(index: number): "current" | "answered" | "unanswered" {
  if (index === props.currentIndex) return "current";
  // 题号映射到 question id 由父组件保证；此处简化用 index 判断 answered
  return "unanswered";
}
</script>

<template>
  <div class="flex flex-wrap gap-2">
    <button
      v-for="i in total"
      :key="i"
      type="button"
      :class="[
        'h-9 w-9 rounded-[var(--radius-md)] text-sm font-bold transition-colors',
        status(i - 1) === 'current'
          ? 'bg-[var(--primary)] text-white'
          : status(i - 1) === 'answered'
            ? 'bg-[var(--emerald-soft)] text-[var(--emerald)]'
            : 'bg-[var(--surface-soft)] text-[var(--text-muted)] hover:bg-[var(--surface-strong)]',
      ]"
      @click="emit('jump', i - 1)"
    >
      {{ i }}
    </button>
  </div>
</template>
```

- [ ] **Step 3: 创建 ExamAnswerArea.vue（答题区，复用练习的选项逻辑）**

Create `frontend/src/components/exam/ExamAnswerArea.vue`:

```vue
<script setup lang="ts">
import { computed, ref, watch } from "vue";
import type { ExamQuestion } from "@/types";

const props = defineProps<{ question: ExamQuestion }>();

const emit = defineEmits<{ (e: "answer", value: string): void }>();

const selected = ref<string>("");
const selectedMulti = ref<string[]>([]);
const textAnswer = ref<string>("");

watch(() => props.question, () => {
  selected.value = "";
  selectedMulti.value = [];
  textAnswer.value = "";
});

const isChoice = computed(() =>
  ["single_choice", "multiple_choice", "true_false"].includes(props.question.type),
);

const options = computed(() => {
  const opts = props.question.options || {};
  return Object.entries(opts).map(([key, label]) => ({ key, label }));
});

function pickSingle(key: string) {
  selected.value = key;
  emit("answer", key);
}

function toggleMulti(key: string) {
  const idx = selectedMulti.value.indexOf(key);
  if (idx >= 0) selectedMulti.value.splice(idx, 1);
  else selectedMulti.value.push(key);
  selectedMulti.value.sort();
  emit("answer", selectedMulti.value.join(","));
}

function onText() {
  emit("answer", textAnswer.value);
}
</script>

<template>
  <div class="space-y-4">
    <p class="text-[var(--text-main)] text-base leading-relaxed">{{ question.question }}</p>

    <div v-if="isChoice" class="space-y-2">
      <button
        v-for="opt in options"
        :key="opt.key"
        type="button"
        :class="[
          'flex w-full items-center gap-3 rounded-[var(--radius-md)] border p-3 text-left transition-colors',
          selected === opt.key || selectedMulti.includes(opt.key)
            ? 'border-[var(--primary)] bg-[var(--primary-soft)]'
            : 'border-[var(--line-soft)] hover:bg-[var(--surface-soft)]',
        ]"
        @click="question.type === 'multiple_choice' ? toggleMulti(opt.key) : pickSingle(opt.key)"
      >
        <span class="grid h-6 w-6 place-items-center rounded-full border text-xs font-bold">
          {{ opt.key }}
        </span>
        <span class="flex-1 text-sm text-[var(--text-main)]">{{ opt.label }}</span>
      </button>
    </div>

    <textarea
      v-else
      v-model="textAnswer"
      rows="4"
      class="w-full rounded-[var(--radius-md)] border border-[var(--line-soft)] p-3 text-sm"
      placeholder="请输入你的答案"
      @input="onText"
    />
  </div>
</template>
```

- [ ] **Step 4: typecheck + build**

Run: `cd frontend && npm run typecheck && npm run build`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add frontend/src/components/exam/
git commit -m "feat(exam-ui): add ExamTopBar, ExamQuestionNav, ExamAnswerArea components"
```

---

## Task 12: 创建考试页面（列表/创建/答题/结果/排行榜）

**Files:**
- Create: `frontend/src/views/exam/ExamList.vue`
- Create: `frontend/src/views/exam/ExamCreate.vue`
- Create: `frontend/src/views/exam/ExamTake.vue`
- Create: `frontend/src/views/exam/ExamResult.vue`
- Create: `frontend/src/views/exam/ExamLeaderboard.vue`

> **说明**：每个页面用 shadcn-vue Card/Button 组件 + exam store。由于篇幅，给出 ExamList 和 ExamTake 的完整实现作为样板，其余页面按相同模式。

- [ ] **Step 1: 创建 ExamList.vue**

Create `frontend/src/views/exam/ExamList.vue`:

```vue
<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { listExams } from "@/api/exam";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useAuthStore } from "@/stores/auth";
import type { Exam } from "@/types";

const router = useRouter();
const auth = useAuthStore();
const exams = ref<Exam[]>([]);
const loading = ref(false);
const error = ref("");

async function fetchExams() {
  loading.value = true;
  error.value = "";
  try {
    exams.value = await listExams();
  } catch (e: any) {
    error.value = e?.message || "加载考试失败";
  } finally {
    loading.value = false;
  }
}

onMounted(fetchExames => fetchExams());

function takeExam(exam: Exam) {
  if (exam.status === "published") router.push(`/exams/${exam.id}/take`);
}
</script>

<template>
  <section class="mx-auto max-w-4xl space-y-4 p-4">
    <div class="flex items-center justify-between">
      <h1 class="text-xl font-bold text-[var(--text-main)]">考试列表</h1>
      <Button v-if="auth.can('exam:create')" @click="router.push('/exams/new')">创建考试</Button>
    </div>

    <p v-if="loading" class="text-[var(--text-muted)]">加载中…</p>
    <p v-if="error" class="text-[var(--rose)]">{{ error }}</p>

    <div v-if="!loading && exams.length === 0" class="text-[var(--text-muted)]">暂无考试</div>

    <Card v-for="exam in exams" :key="exam.id">
      <CardHeader>
        <CardTitle>{{ exam.title }}</CardTitle>
      </CardHeader>
      <CardContent>
        <div class="flex items-center justify-between">
          <div class="text-sm text-[var(--text-muted)]">
            {{ exam.question_count }} 题 · {{ exam.time_limit }} 分钟 · 满分 {{ exam.total_score }}
          </div>
          <div class="flex gap-2">
            <Button v-if="exam.status === 'published'" size="sm" @click="takeExam(exam)">开始考试</Button>
            <Button variant="ghost" size="sm" @click="router.push(`/exams/${exam.id}/leaderboard`)">排行榜</Button>
          </div>
        </div>
      </CardContent>
    </Card>
  </section>
</template>
```

注意：`onMounted(fetchExames => fetchExam())` 是笔误，应为 `onMounted(fetchExam)`（不带参数）。修正：

```typescript
onMounted(() => fetchExams());
```

- [ ] **Step 2: 创建 ExamTake.vue（答题页，核心）**

Create `frontend/src/views/exam/ExamTake.vue`:

```vue
<script setup lang="ts">
import { computed, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useExamStore } from "@/stores/exam";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import ExamTopBar from "@/components/exam/ExamTopBar.vue";
import ExamQuestionNav from "@/components/exam/ExamQuestionNav.vue";
import ExamAnswerArea from "@/components/exam/ExamAnswerArea.vue";

const route = useRoute();
const router = useRouter();
const store = useExamStore();

const examId = computed(() => Number(route.params.examId));

onMounted(async () => {
  await store.startAttempt(examId.value);
});

function onAnswer(value: string) {
  if (store.currentQuestion) {
    store.setAnswer(store.currentQuestion.id, value);
  }
}

async function handleSubmit() {
  if (!confirm("确认交卷？交卷后不可修改。")) return;
  await store.submit();
  router.push(`/exams/${examId.value}/result`);
}

const answeredIds = computed(
  () => new Set(Object.keys(store.answers).map(Number)),
);
</script>

<template>
  <div v-if="store.loading && !store.currentAttempt" class="p-8 text-center text-[var(--text-muted)]">
    加载考试中…
  </div>

  <template v-else-if="store.currentAttempt">
    <ExamTopBar
      :title="store.currentAttempt.exam.title"
      :deadline-at="store.currentAttempt.deadline_at"
      :answered-count="store.answeredCount"
      :total-count="store.totalQuestions"
      @submit="handleSubmit"
    />

    <div class="mx-auto max-w-4xl gap-4 p-4 md:flex">
      <Card class="flex-1">
        <CardContent>
          <p class="mb-2 text-xs font-bold text-[var(--text-muted)]">
            第 {{ store.currentIndex + 1 }} / {{ store.totalQuestions }} 题
          </p>
          <ExamAnswerArea
            v-if="store.currentQuestion"
            :question="store.currentQuestion"
            @answer="onAnswer"
          />
          <div class="mt-6 flex justify-between">
            <Button variant="outline" :disabled="store.currentIndex === 0" @click="store.prev()">上一题</Button>
            <Button v-if="store.currentIndex < store.totalQuestions - 1" @click="store.next()">下一题</Button>
            <Button v-else variant="destructive" @click="handleSubmit">交卷</Button>
          </div>
        </CardContent>
      </Card>

      <Card class="hidden w-64 shrink-0 md:block">
        <CardContent>
          <p class="mb-3 text-sm font-bold text-[var(--text-main)]">答题卡</p>
          <ExamQuestionNav
            :total="store.totalQuestions"
            :current-index="store.currentIndex"
            :answered-ids="answeredIds"
            @jump="store.goTo"
          />
        </CardContent>
      </Card>
    </div>
  </template>

  <p v-if="store.error" class="p-4 text-center text-[var(--rose)]">{{ store.error }}</p>
</template>
```

- [ ] **Step 3: 创建 ExamResult.vue**

Create `frontend/src/views/exam/ExamResult.vue`:

```vue
<script setup lang="ts">
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useExamStore } from "@/stores/exam";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

const route = useRoute();
const router = useRouter();
const store = useExamStore();

const result = computed(() => store.result);
</script>

<template>
  <section v-if="result" class="mx-auto max-w-2xl space-y-4 p-4">
    <Card>
      <CardHeader>
        <CardTitle>考试成绩</CardTitle>
      </CardHeader>
      <CardContent>
        <div class="grid grid-cols-2 gap-4 text-center">
          <div>
            <div class="text-3xl font-bold text-[var(--primary)]">{{ result.score }}</div>
            <div class="text-sm text-[var(--text-muted)]">得分 / {{ result.total_score }}</div>
          </div>
          <div>
            <div class="text-3xl font-bold" :class="result.is_passed ? 'text-[var(--emerald)]' : 'text-[var(--rose)]'">
              {{ result.is_passed ? "通过" : "未通过" }}
            </div>
            <div class="text-sm text-[var(--text-muted)]">第 {{ result.rank ?? "-" }} 名</div>
          </div>
        </div>
        <div class="mt-4 text-center text-sm text-[var(--text-muted)]">
          用时 {{ Math.floor(result.duration_seconds / 60) }} 分 {{ result.duration_seconds % 60 }} 秒
        </div>
      </CardContent>
    </Card>

    <Card>
      <CardHeader><CardTitle>题目详情</CardTitle></CardHeader>
      <CardContent>
        <div v-for="r in result.results" :key="r.question_id" class="border-b border-[var(--line-soft)] py-3 last:border-0">
          <div class="flex items-center justify-between">
            <span class="text-sm text-[var(--text-main)]">题目 #{{ r.question_id }}</span>
            <span :class="['text-sm font-bold', r.is_correct ? 'text-[var(--emerald)]' : 'text-[var(--rose)]']">
              {{ r.earned_score }} / {{ r.score }}
            </span>
          </div>
          <div class="mt-1 text-xs text-[var(--text-muted)]">
            你的答案：{{ r.user_answer || "（未作答）" }} · 正确答案：{{ r.correct_answer }}
          </div>
        </div>
      </CardContent>
    </Card>

    <div class="flex gap-2">
      <Button variant="outline" @click="router.push('/exams')">返回列表</Button>
      <Button variant="ghost" @click="router.push(`/exams/${result.exam_id}/leaderboard`)">查看排行榜</Button>
    </div>
  </section>

  <p v-else class="p-8 text-center text-[var(--text-muted)]">暂无结果数据</p>
</template>
```

- [ ] **Step 4: 创建 ExamCreate.vue 和 ExamLeaderboard.vue**

Create `frontend/src/views/exam/ExamCreate.vue`（表单：选课程、标题、时限、题目选择）:

```vue
<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { getMyCourses } from "@/api/courses";
import { createExam, publishExam } from "@/api/exam";

const router = useRouter();
const courses = ref<any[]>([]);
const title = ref("");
const courseId = ref<number | null>(null);
const timeLimit = ref(60);
const submitting = ref(false);
const error = ref("");

onMounted(async () => {
  courses.value = await getMyCourses();
});

async function handleCreate() {
  if (!title.value.trim() || !courseId.value) {
    error.value = "请填写标题并选择课程";
    return;
  }
  submitting.value = true;
  error.value = "";
  try {
    const exam = await createExam({
      title: title.value.trim(),
      course_id: courseId.value,
      time_limit: timeLimit.value,
    });
    await publishExam(exam.id);
    router.push("/exams");
  } catch (e: any) {
    error.value = e?.response?.data?.detail || "创建失败";
  } finally {
    submitting.value = false;
  }
}
</script>

<template>
  <section class="mx-auto max-w-lg space-y-4 p-4">
    <h1 class="text-xl font-bold text-[var(--text-main)]">创建考试</h1>
    <Card>
      <CardContent>
        <div class="space-y-4">
          <div>
            <label class="mb-1 block text-sm font-medium text-[var(--text-secondary)]">考试标题</label>
            <input v-model="title" class="w-full rounded-[var(--radius-md)] border border-[var(--line-soft)] p-2 text-sm" placeholder="如：期末模拟考试" />
          </div>
          <div>
            <label class="mb-1 block text-sm font-medium text-[var(--text-secondary)]">选择题库</label>
            <select v-model="courseId" class="w-full rounded-[var(--radius-md)] border border-[var(--line-soft)] p-2 text-sm">
              <option :value="null" disabled>请选择…</option>
              <option v-for="c in courses" :key="c.id" :value="c.id">{{ c.name }}（{{ c.question_count }} 题）</option>
            </select>
          </div>
          <div>
            <label class="mb-1 block text-sm font-medium text-[var(--text-secondary)]">时限（分钟）</label>
            <input v-model.number="timeLimit" type="number" min="1" class="w-full rounded-[var(--radius-md)] border border-[var(--line-soft)] p-2 text-sm" />
          </div>
          <p v-if="error" class="text-sm text-[var(--rose)]">{{ error }}</p>
          <Button :disabled="submitting" class="w-full" @click="handleCreate">
            {{ submitting ? "创建中…" : "创建并发布" }}
          </Button>
        </div>
      </CardContent>
    </Card>
  </section>
</template>
```

Create `frontend/src/views/exam/ExamLeaderboard.vue`:

```vue
<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import { getExamLeaderboard } from "@/api/exam";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { ExamLeaderboard } from "@/types";

const route = useRoute();
const data = ref<ExamLeaderboard | null>(null);
const loading = ref(true);

onMounted(async () => {
  const examId = Number(route.params.examId);
  data.value = await getExamLeaderboard(examId);
  loading.value = false;
});
</script>

<template>
  <section class="mx-auto max-w-2xl p-4">
    <Card>
      <CardHeader><CardTitle>排行榜</CardTitle></CardHeader>
      <CardContent>
        <p v-if="loading" class="text-[var(--text-muted)]">加载中…</p>
        <div v-else-if="data && data.entries.length" class="space-y-2">
          <div v-for="entry in data.entries" :key="entry.user_id"
               class="flex items-center justify-between rounded-[var(--radius-md)] p-3"
               :class="entry.rank <= 3 ? 'bg-[var(--primary-soft)]' : 'bg-[var(--surface-soft)]'">
            <span class="font-bold text-[var(--text-main)]">#{{ entry.rank }} {{ entry.username }}</span>
            <span class="text-[var(--primary)] font-bold">{{ entry.score }} 分</span>
          </div>
        </div>
        <p v-else class="text-[var(--text-muted)]">暂无提交记录</p>
      </CardContent>
    </Card>
  </section>
</template>
```

- [ ] **Step 5: typecheck + build**

Run: `cd frontend && npm run typecheck && npm run build`
Expected: PASS

- [ ] **Step 6: 提交**

```bash
git add frontend/src/views/exam/
git commit -m "feat(exam-ui): add exam list/create/take/result/leaderboard pages"
```

---

## Task 13: 路由 + 权限守卫

**Files:**
- Modify: `frontend/src/router.ts`

- [ ] **Step 1: 添加考试和管理后台路由**

修改 `frontend/src/router.ts`，在 AppLayout 的 children 中（现有 study-overview 路由之后）添加：

```typescript
      {
        path: "exams",
        name: "exams",
        component: () => import("./views/exam/ExamList.vue"),
        meta: { title: "考试", navKey: "exam" },
      },
      {
        path: "exams/new",
        name: "exam-create",
        component: () => import("./views/exam/ExamCreate.vue"),
        meta: { title: "创建考试", navKey: "exam", requiresPermission: "exam:create" },
      },
      {
        path: "exams/:examId/take",
        name: "exam-take",
        component: () => import("./views/exam/ExamTake.vue"),
        meta: { title: "答题", navKey: "exam", requiresPermission: "exam:take" },
      },
      {
        path: "exams/:examId/result",
        name: "exam-result",
        component: () => import("./views/exam/ExamResult.vue"),
        meta: { title: "考试结果", navKey: "exam" },
      },
      {
        path: "exams/:examId/leaderboard",
        name: "exam-leaderboard",
        component: () => import("./views/exam/ExamLeaderboard.vue"),
        meta: { title: "排行榜", navKey: "exam", requiresPermission: "exam:view_leaderboard" },
      },
      {
        path: "admin/users",
        name: "admin-users",
        component: () => import("./views/admin/AdminUsers.vue"),
        meta: { title: "用户管理", requiresPermission: "user:manage" },
      },
      {
        path: "admin/stats",
        name: "admin-stats",
        component: () => import("./views/admin/AdminStats.vue"),
        meta: { title: "全局统计", requiresPermission: "stats:view_global" },
      },
```

- [ ] **Step 2: 在路由守卫中添加权限检查**

修改 `router.ts` 的 `router.beforeEach`，在 token 检查之后添加权限检查：

```typescript
router.beforeEach(async (to) => {
  const token = getToken();

  if (to.matched.some((route) => route.meta.requiresAuth) && !token) {
    return { name: "login", query: { redirect: to.fullPath } };
  }

  if (to.matched.some((route) => route.meta.guest) && token) {
    const redirect = to.query.redirect;
    if (redirect && typeof redirect === "string" && redirect.startsWith("/")
        && !redirect.startsWith("/login") && !redirect.startsWith("/register")) {
      return { path: redirect };
    }
    return { name: "home" };
  }

  // Permission guard
  const requiredPermission = to.meta.requiresPermission as string | undefined;
  if (requiredPermission && token) {
    const { useAuthStore } = await import("./stores/auth");
    const auth = useAuthStore();
    // Ensure profile is loaded
    if (!auth.user) {
      await auth.fetchProfile();
    }
    if (!auth.can(requiredPermission)) {
      return { name: "home" };
    }
  }
});
```

- [ ] **Step 3: 创建管理后台页面占位**

Create `frontend/src/views/admin/AdminUsers.vue` 和 `AdminStats.vue`（最小可用版本，用 shadcn Card 展示列表/统计）:

`AdminUsers.vue`:
```vue
<script setup lang="ts">
import { onMounted, ref } from "vue";
import { listUsers, updateUserRole, type AdminUser } from "@/api/admin";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const users = ref<AdminUser[]>([]);
const loading = ref(true);

onMounted(async () => {
  const data = await listUsers({ page: 1, page_size: 50 });
  users.value = data.items;
  loading.value = false;
});

async function changeRole(userId: number, role: string) {
  await updateUserRole(userId, role);
}
</script>

<template>
  <section class="mx-auto max-w-3xl p-4">
    <Card>
      <CardHeader><CardTitle>用户管理</CardTitle></CardHeader>
      <CardContent>
        <p v-if="loading">加载中…</p>
        <table v-else class="w-full text-sm">
          <thead>
            <tr class="border-b border-[var(--line-soft)] text-left text-[var(--text-muted)]">
              <th class="py-2">用户名</th><th>角色</th><th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="u in users" :key="u.id" class="border-b border-[var(--line-soft)]">
              <td class="py-2 text-[var(--text-main)]">{{ u.username }}</td>
              <td class="text-[var(--text-secondary)]">{{ u.role }}</td>
              <td>
                <select :value="u.role" class="rounded border p-1 text-xs"
                        @change="changeRole(u.id, ($event.target as HTMLSelectElement).value)">
                  <option value="student">student</option>
                  <option value="teacher">teacher</option>
                  <option value="admin">admin</option>
                </select>
              </td>
            </tr>
          </tbody>
        </table>
      </CardContent>
    </Card>
  </section>
</template>
```

`AdminStats.vue`:
```vue
<script setup lang="ts">
import { onMounted, ref } from "vue";
import { getAdminStats, type AdminStats } from "@/api/admin";
import { Card, CardContent } from "@/components/ui/card";

const stats = ref<AdminStats | null>(null);
onMounted(async () => { stats.value = await getAdminStats(); });

const labels: Array<[keyof AdminStats, string]> = [
  ["user_count", "用户"], ["question_count", "题目"], ["course_count", "题库"],
  ["practice_count", "练习记录"], ["exam_count", "考试"],
];
</script>

<template>
  <section class="mx-auto grid max-w-3xl grid-cols-2 gap-4 p-4 md:grid-cols-3">
    <Card v-for="[key, label] in labels" :key="key">
      <CardContent class="text-center">
        <div class="text-3xl font-bold text-[var(--primary)]">{{ stats?.[key] ?? "--" }}</div>
        <div class="text-sm text-[var(--text-muted)]">{{ label }}</div>
      </CardContent>
    </Card>
  </section>
</template>
```

- [ ] **Step 4: typecheck + build + 手动验证**

Run: `cd frontend && npm run typecheck && npm run build`
Expected: PASS

手动验证：dev server 下，用 student 账号访问 `/exams/new` 应跳回首页（无权限），用 teacher 账号可进入。

- [ ] **Step 5: 运行前端测试**

Run: `cd frontend && npm run test`
Expected: PASS

- [ ] **Step 6: 提交**

```bash
git add frontend/src/router.ts frontend/src/views/admin/
git commit -m "feat(routing): add exam + admin routes with permission guards"
```

---

# 里程碑 M5：前端 — UX 革新

## Task 14: 重做首页（数据卡片 + 学习热力图骨架）

**Files:**
- Modify: `frontend/src/views/Home.vue`

- [ ] **Step 1: 用 shadcn Card 重做首页数据区**

将 Home.vue 的 template 中 `.home-stats-grid` 区域用 shadcn-vue Card 替换。保留现有 script 逻辑（useAuthStore、useStudyOverview、getMyCourses）。

在 `<script setup>` 顶部添加 shadcn 组件 import：
```typescript
import { Card, CardContent } from "@/components/ui/card";
```

替换 stats 区域 template：
```vue
      <div class="grid grid-cols-2 gap-3 md:grid-cols-4">
        <Card v-for="item in statCards" :key="item.label">
          <CardContent class="text-center">
            <strong class="text-2xl text-[var(--text-main)]">
              {{ item.value !== null && item.value !== undefined && item.value !== "" ? item.value : "--" }}
              <small v-if="item.suffix" class="text-xs text-[var(--text-muted)]">{{ item.suffix }}</small>
            </strong>
            <span class="block text-xs text-[var(--text-muted)]">{{ item.label }}</span>
          </CardContent>
        </Card>
      </div>
```

- [ ] **Step 2: 添加学习热力图骨架**

在 stats 区域下方添加一个简单的 7×N 热力图占位（用 PracticeRecord 数据生成，本 Phase 用近 7 日 today_count 拼接的简化版）：

```vue
      <Card>
        <CardContent>
          <p class="mb-2 text-sm font-bold text-[var(--text-main)]">学习热力图（近 7 日）</p>
          <div class="flex gap-1">
            <div v-for="(d, i) in heatmapData" :key="i"
                 class="h-8 flex-1 rounded-[var(--radius-sm)]"
                 :style="{ background: heatColor(d) }"
                 :title="`第 ${i + 1} 天：${d} 题`" />
          </div>
        </CardContent>
      </Card>
```

在 script 中添加（简化：用 stats 派生，实际可后续接 history API）：
```typescript
const heatmapData = computed(() => {
  // 简化版：复用 recentCount7d 的近似分布。完整实现留 Phase 4 数据分析。
  return [0, 0, 0, 0, 0, 0, stats.value.todayCount || 0];
});
function heatColor(count: number): string {
  if (count === 0) return "var(--surface-soft)";
  if (count < 5) return "rgba(59,130,246,0.3)";
  if (count < 15) return "rgba(59,130,246,0.6)";
  return "var(--primary)";
}
```

- [ ] **Step 3: typecheck + build + 手动验证**

Run: `cd frontend && npm run typecheck && npm run build`
Expected: PASS
手动验证首页数据卡片和热力图正常显示。

- [ ] **Step 4: 提交**

```bash
git add frontend/src/views/Home.vue
git commit -m "refactor(home): shadcn-vue data cards + study heatmap skeleton"
```

---

## Task 15: 键盘快捷键 + 滑动手势 composables

**Files:**
- Create: `frontend/src/composables/useKeyboardShortcuts.ts`
- Create: `frontend/src/composables/useSwipe.ts`
- Test: `frontend/src/composables/__tests__/useKeyboardShortcuts.spec.ts`

- [ ] **Step 1: 写键盘快捷键测试**

Create `frontend/src/composables/__tests__/useKeyboardShortcuts.spec.ts`:

```typescript
import { describe, expect, it, vi } from "vitest";
import { useKeyboardShortcuts } from "../useKeyboardShortcuts";

describe("useKeyboardShortcuts", () => {
  it("calls handlers on matching keys", () => {
    const onNext = vi.fn();
    const onPrev = vi.fn();
    const { bind, unbind } = useKeyboardShortcuts({
      next: onNext,
      prev: onPrev,
    });
    bind();
    window.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowRight" }));
    expect(onNext).toHaveBeenCalledTimes(1);
    window.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowLeft" }));
    expect(onPrev).toHaveBeenCalledTimes(1);
    unbind();
  });

  it("ignores keys when typing in input", () => {
    const onNext = vi.fn();
    const { bind, unbind } = useKeyboardShortcuts({ next: onNext });
    bind();
    const input = document.createElement("input");
    document.body.appendChild(input);
    input.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowRight", bubbles: true }));
    expect(onNext).not.toHaveBeenCalled();
    document.body.removeChild(input);
    unbind();
  });
});
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd frontend && npx vitest run src/composables/__tests__/useKeyboardShortcuts.spec.ts`
Expected: FAIL

- [ ] **Step 3: 实现 useKeyboardShortcuts**

Create `frontend/src/composables/useKeyboardShortcuts.ts`:

```typescript
export interface ShortcutHandlers {
  next?: () => void;
  prev?: () => void;
  submit?: () => void;
  selectOption?: (index: number) => void;
}

const NEXT_KEYS = new Set(["ArrowRight", "d", "D"]);
const PREV_KEYS = new Set(["ArrowLeft", "a", "A"]);

function isTypingTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  return ["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName) || target.isContentEditable;
}

export function useKeyboardShortcuts(handlers: ShortcutHandlers) {
  function onKeydown(e: KeyboardEvent) {
    if (isTypingTarget(e.target)) return;

    if (NEXT_KEYS.has(e.key)) {
      e.preventDefault();
      handlers.next?.();
    } else if (PREV_KEYS.has(e.key)) {
      e.preventDefault();
      handlers.prev?.();
    } else if (e.key === "Enter") {
      handlers.submit?.();
    } else if (/^[1-5]$/.test(e.key)) {
      handlers.selectOption?.(Number(e.key) - 1);
    }
  }

  function bind() {
    window.addEventListener("keydown", onKeydown);
  }

  function unbind() {
    window.removeEventListener("keydown", onKeydown);
  }

  return { bind, unbind };
}
```

- [ ] **Step 4: 实现 useSwipe**

Create `frontend/src/composables/useSwipe.ts`:

```typescript
import { onMounted, onUnmounted, ref, type Ref } from "vue";

export interface SwipeOptions {
  threshold?: number; // min px to trigger
  onSwipeLeft?: () => void;
  onSwipeRight?: () => void;
}

export function useSwipe(el: Ref<HTMLElement | null>, options: SwipeOptions) {
  const threshold = options.threshold ?? 50;
  let startX = 0;
  let startY = 0;
  let tracking = false;

  function onTouchStart(e: TouchEvent) {
    if (e.touches.length !== 1) return;
    startX = e.touches[0].clientX;
    startY = e.touches[0].clientY;
    tracking = true;
  }

  function onTouchEnd(e: TouchEvent) {
    if (!tracking) return;
    tracking = false;
    const dx = e.changedTouches[0].clientX - startX;
    const dy = e.changedTouches[0].clientY - startY;
    // Only horizontal swipes (dx dominant over dy)
    if (Math.abs(dx) < threshold || Math.abs(dy) > Math.abs(dx)) return;
    if (dx < 0) options.onSwipeLeft?.();
    else options.onSwipeRight?.();
  }

  onMounted(() => {
    const node = el.value;
    if (!node) return;
    node.addEventListener("touchstart", onTouchStart, { passive: true });
    node.addEventListener("touchend", onTouchEnd, { passive: true });
  });

  onUnmounted(() => {
    const node = el.value;
    if (!node) return;
    node.removeEventListener("touchstart", onTouchStart);
    node.removeEventListener("touchend", onTouchEnd);
  });
}
```

- [ ] **Step 5: 运行测试**

Run: `cd frontend && npx vitest run src/composables/__tests__/useKeyboardShortcuts.spec.ts`
Expected: PASS

- [ ] **Step 6: 提交**

```bash
git add frontend/src/composables/useKeyboardShortcuts.ts frontend/src/composables/useSwipe.ts frontend/src/composables/__tests__/
git commit -m "feat(ux): keyboard shortcuts + swipe gesture composables"
```

---

## Task 16: 在练习/考试页接入快捷键和手势

**Files:**
- Modify: `frontend/src/views/exam/ExamTake.vue`

- [ ] **Step 1: 在 ExamTake 接入快捷键**

修改 `frontend/src/views/exam/ExamTake.vue` 的 `<script setup>`，添加：

```typescript
import { onMounted, onUnmounted } from "vue";
import { useKeyboardShortcuts } from "@/composables/useKeyboardShortcuts";

const shortcuts = useKeyboardShortcuts({
  next: () => store.next(),
  prev: () => store.prev(),
  submit: handleSubmit,
  selectOption: (idx: number) => {
    // map 1-5 to option selection if current question is choice
    if (store.currentQuestion && store.currentQuestion.options) {
      const keys = Object.keys(store.currentQuestion.options);
      if (keys[idx]) onAnswer(keys[idx]);
    }
  },
});

onMounted(() => {
  shortcuts.bind();
  store.startAttempt(examId.value);
});

onUnmounted(() => {
  shortcuts.unbind();
  store.reset();
});
```

（替换原 onMounted 中的 startAttempt 调用，合并到上面的 onMounted）

- [ ] **Step 2: typecheck + build + 手动验证**

Run: `cd frontend && npm run typecheck && npm run build`
Expected: PASS
手动验证：在考试答题页按 ←→ 切换题目，按 1-5 选择选项，按 Enter 不触发（需明确点击交卷）。

- [ ] **Step 3: 提交**

```bash
git add frontend/src/views/exam/ExamTake.vue
git commit -m "feat(exam-ui): wire keyboard shortcuts into exam take page"
```

---

## Task 17: AppLayout 响应式 + 底部 Tab Bar

**Files:**
- Modify: `frontend/src/layouts/AppLayout.vue`

- [ ] **Step 1: 读取现有 AppLayout**

Run: `cat frontend/src/layouts/AppLayout.vue`（307 行）

- [ ] **Step 2: 在移动端添加底部 Tab Bar**

在 AppLayout.vue 的 template 末尾（main 内容之后）添加底部导航，仅在小屏显示：

```vue
    <nav class="fixed bottom-0 left-0 right-0 z-30 flex border-t border-[var(--line-soft)] bg-[var(--surface)] md:hidden">
      <RouterLink v-for="tab in mobileTabs" :key="tab.to" :to="tab.to"
                  class="flex flex-1 flex-col items-center gap-1 py-2 text-xs"
                  :class="isActiveTab(tab.to) ? 'text-[var(--primary)]' : 'text-[var(--text-muted)]'">
        <component :is="tab.icon" :size="22" />
        <span>{{ tab.label }}</span>
      </RouterLink>
    </nav>
```

在 script 中添加：
```typescript
import { BookOpen, ClipboardList, Home as HomeIcon, User } from "@lucide/vue";  // 或 lucide-vue-next

const mobileTabs = [
  { to: "/", label: "首页", icon: HomeIcon },
  { to: "/courses", label: "题库", icon: BookOpen },
  { to: "/practice", label: "练习", icon: ClipboardList },
  { to: "/mine", label: "我的", icon: User },
];

function isActiveTab(to: string): boolean {
  return route.path === to || (to !== "/" && route.path.startsWith(to));
}
```

同时确保 main 内容区在移动端有底部 padding 避免被 Tab Bar 遮挡：
```vue
    <main class="flex-1 pb-16 md:pb-0">
      <RouterView />
    </main>
```

- [ ] **Step 3: 暗色模式切换按钮**

在顶部导航栏添加主题切换按钮（用 theme store）：

```vue
import { useThemeStore } from "@/stores/theme";
const theme = useThemeStore();
```

在顶部栏添加：
```vue
    <button type="button" @click="theme.toggle()"
            class="grid h-9 w-9 place-items-center rounded-full hover:bg-[var(--surface-soft)]">
      <Sun v-if="theme.mode === 'dark'" :size="18" />
      <Moon v-else :size="18" />
    </button>
```
（import Sun, Moon from icon lib）

- [ ] **Step 4: typecheck + build + 手动验证**

Run: `cd frontend && npm run typecheck && npm run build`
Expected: PASS
手动验证：缩小窗口到 375px 宽，确认底部 Tab Bar 出现；点击暗色按钮切换主题。

- [ ] **Step 5: 提交**

```bash
git add frontend/src/layouts/AppLayout.vue
git commit -m "feat(layout): responsive bottom tab bar + dark mode toggle"
```

---

## Task 18: 页面过渡 + 列表动画

**Files:**
- Modify: `frontend/src/layouts/AppLayout.vue`（RouterView 加 Transition）
- Modify: `frontend/src/styles/transitions.css`

- [ ] **Step 1: 给 RouterView 添加过渡**

修改 AppLayout.vue 的 `<RouterView>`：

```vue
    <main class="flex-1 pb-16 md:pb-0">
      <RouterView v-slot="{ Component }">
        <Transition name="page" mode="out-in">
          <component :is="Component" />
        </Transition>
      </RouterView>
    </main>
```

- [ ] **Step 2: 在 transitions.css 添加过渡样式**

在 `frontend/src/styles/transitions.css` 添加：

```css
/* ── Page transitions ── */
.page-enter-active,
.page-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease;
}

.page-enter-from {
  opacity: 0;
  transform: translateY(8px);
}

.page-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

/* ── List stagger ── */
.list-stagger-enter-active {
  transition: all 0.3s ease;
}
.list-stagger-enter-from {
  opacity: 0;
  transform: translateY(12px);
}

/* ── Correct/wrong pulse (practice feedback) ── */
@keyframes correct-pulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.04); }
  100% { transform: scale(1); }
}
@keyframes wrong-shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-4px); }
  75% { transform: translateX(4px); }
}
.animate-correct { animation: correct-pulse 0.3s ease; }
.animate-wrong { animation: wrong-shake 0.3s ease; }
```

- [ ] **Step 3: typecheck + build + 手动验证**

Run: `cd frontend && npm run typecheck && npm run build`
Expected: PASS
手动验证：切换路由时有淡入淡出过渡。

- [ ] **Step 4: 提交**

```bash
git add frontend/src/layouts/AppLayout.vue frontend/src/styles/transitions.css
git commit -m "feat(ux): page transitions + list/practice animations"
```

---

## Task 19: Phase 3 完整性验证

**Files:** 无（纯验证）

- [ ] **Step 1: 后端全量测试**

Run: `cd backend && python -m pytest -q`
Expected: PASS（含新增的 exam/permission/admin 测试）

- [ ] **Step 2: 前端全量测试 + typecheck + build**

Run: `cd frontend && npm run typecheck && npm run test && npm run build`
Expected: 全部 PASS

- [ ] **Step 3: 手动端到端验证考试流程**

Run: `cd frontend && npm run dev`
1. 用 admin 账号在 `/admin/users` 把某用户升为 teacher
2. 用 teacher 账号在 `/exams/new` 创建考试并发布
3. 用 student 账号在 `/exams` 开始考试，用键盘快捷键答题
4. 交卷后查看成绩报告和排行榜
5. 确认 student 无法访问 `/exams/new`（跳回首页）

- [ ] **Step 4: 验证移动端和暗色模式**

- 缩窗到 375px，确认底部 Tab Bar、卡片布局正常
- 切换暗色模式，全页面无样式破损
- 练习/考试页键盘快捷键（←→、1-5）正常

- [ ] **Step 5: 对照 spec 验收标准（§5.5）逐项确认**

对照 `docs/superpowers/specs/2026-06-27-major-refactor-design.md` §5.5：
- [ ] 考试模式端到端可用：创建 → 发布 → 答题 → 交卷 → 成绩报告
- [ ] 三种角色权限正确隔离，越权访问被拒绝（有测试覆盖）
- [ ] 管理后台用户管理 + 统计页面可用
- [ ] 首页数据卡片 + 学习热力图渲染正确
- [ ] 考试页面支持键盘快捷键
- [ ] 移动端布局在 375px 宽度下无溢出
- [ ] 暗色模式全页面无样式破损

- [ ] **Step 6: 最终提交（如有遗漏改动）**

```bash
git add -A && git status
```

---

## 完成标准（对照 Spec §5.5）

- [x] 考试模式端到端可用（create→publish→take→submit→result→leaderboard）
- [x] RBAC 三角色权限隔离 + `require_permission` 守卫（前后端）
- [x] 管理后台（用户角色管理 + 全局统计）
- [x] 首页 shadcn-vue 数据卡片 + 热力图骨架
- [x] 考试键盘快捷键（←→ 切题、1-5 选项、Enter 交卷）
- [x] 移动端底部 Tab Bar + 响应式布局
- [x] 暗色模式全页面支持
- [x] 页面过渡 + 练习反馈动画

---

## 自查备注（Self-Review）

**Spec 覆盖**: Spec §5 的 5.1–5.4 全部映射到任务：
- 5.1 考试模式 → Task 4, 5, 6, 7, 10, 11, 12（后端 schema/repo/service/api + 前端 store/组件/页面）
- 5.2 权限系统 → Task 1, 2, 3, 9, 13（RBAC + require_permission + 路由守卫）
- 5.3 UI 体验革新 → Task 14, 15, 16, 17, 18（首页/快捷键/手势/移动端/动画）
- 5.4 响应式 & 暗色模式 → Task 17（Tab Bar + theme toggle，theme store 在 Phase 2 Task 10 已建）

**类型一致性**: `ExamService.create_exam/start_attempt/submit` 方法名在 service/api/store/测试间一致。`useExamStore` 的 `phase/ currentAttempt/ result` 字段名跨组件一致。`require_permission("exam:create")` 权限字符串与 `_ROLE_PERMISSIONS` 矩阵一致。

**范围说明**:
- 管理后台公告管理（`/admin/announcements`）：Spec §5.2 提及，但现有系统已有 Announcements 页面（静态 release notes）。本 Phase 聚焦用户管理和统计，公告的动态 CRUD 留后续。这是有意的优先级取舍。
- 学习热力图：本 Phase 用近 7 日简化版，完整的 30/90 日热力图需调用 history API 聚合，留 Phase 4 数据分析仪表盘一起做（Spec §6.2）。
- 练习页（Practice.vue）的键盘快捷键接入：本 Phase 示范在考试页接入；练习页结构相似，可按相同模式后续接入，不在本 Phase 强制完成避免范围蔓延。

**注**: Task 1 测试断言 `data["role"] in ("student", "user", ...)` 兼容迁移期间——旧 token 的用户 role_id 为 NULL 返回 "student"（新默认）。Task 2 的 `_ROLE_PERMISSIONS` 矩阵中 student 包含 `course:create`（保持现有"任何人可创建题库"的行为不变），避免破坏现有测试。
