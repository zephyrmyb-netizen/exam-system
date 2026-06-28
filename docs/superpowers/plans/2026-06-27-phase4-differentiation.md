# Phase 4 — 差异化功能 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Prerequisite:** Phase 3 merged — 考试模式、RBAC、UI 革新已完成。Phase 2 的 `Tag`/`QuestionTag`/`Bookmark`/`StudyGoal` 模型已通过 migration 创建。

**Goal:** 让系统从"刷题工具"升级为"智能学习伙伴" —— 知识点标签系统、艾宾浩斯复习曲线优化、智能推荐引擎、数据分析仪表盘（图表）、PWA 离线支持、数据导出/收藏/全局搜索等工具增强。

**Architecture:** 后端基于已有 Tag/Bookmark 模型实现新 API + 推荐算法 service；前端引入 Chart.js 做数据可视化、Workbox 做 PWA、IndexedDB 做离线缓存。全程 TDD，新功能独立模块，不破坏现有行为。

**Tech Stack:** FastAPI / SQLAlchemy / pytest（后端）；Vue 3 / Chart.js / Workbox / Pinia / Vitest（前端）。

**Spec:** `docs/superpowers/specs/2026-06-27-major-refactor-design.md` §6

---

## 文件结构总览

### 后端新增 / 修改

| 文件 | 责任 | 操作 |
|---|---|---|
| `backend/repositories/tag_repo.py` | Tag/QuestionTag 数据访问 | 新建 |
| `backend/repositories/bookmark_repo.py` | Bookmark 数据访问 | 新建 |
| `backend/services/tag_service.py` | 标签管理 + AI 建议标签 | 新建 |
| `backend/services/recommendation_service.py` | 智能推荐（薄弱知识点 + 到期复习） | 新建 |
| `backend/services/analytics_service.py` | 数据分析聚合（学生/教师视角） | 新建 |
| `backend/services/export_service.py` | 数据导出（JSON/Excel/CSV） | 新建 |
| `backend/api/tags.py` | 标签路由 | 新建 |
| `backend/api/recommendations.py` | 推荐路由 | 新建 |
| `backend/api/analytics.py` | 分析路由 | 新建 |
| `backend/api/bookmarks.py` | 收藏路由 | 新建 |
| `backend/api/exports.py` | 导出路由 | 新建 |
| `backend/requirements.txt` | openpyxl（Excel 导出） | 修改 |
| `backend/main.py` | include 新路由 | 修改 |
| `backend/services/imports/ai_extractor.py` | AI 导入时建议标签 | 修改 |

### 前端新增 / 修改

| 文件 | 责任 | 操作 |
|---|---|---|
| `frontend/package.json` | chart.js / vue-chartjs / workbox-cli | 修改 |
| `frontend/src/api/tag.ts` 等 5 个 | 新 API 层 | 新建 |
| `frontend/src/components/charts/HeatmapChart.vue` 等 4 个 | 图表组件 | 新建 |
| `frontend/src/views/StudyOverview.vue` | 重做为数据仪表盘 | 修改 |
| `frontend/src/components/search/GlobalSearch.vue` | 全局搜索（Ctrl+K） | 新建 |
| `frontend/src/composables/useOfflineSync.ts` | 离线同步 | 新建 |
| `frontend/public/manifest.webmanifest` | PWA manifest | 新建 |
| `frontend/src/sw.ts` | Workbox service worker | 新建 |
| `frontend/vite.config.ts` | VitePWA 插件配置 | 修改 |
| `frontend/src/views/bookmark/BookmarkList.vue` | 收藏夹页面 | 新建 |

---

## 执行顺序

分 5 个里程碑（M1–M5）。

- **M1（后端标签）**: Task 1–2 — Tag repo + service + API + AI 建议标签
- **M2（后端智能 + 分析）**: Task 3–4 — 推荐 service + 分析 service + API
- **M3（后端导出 + 收藏）**: Task 5–6 — 导出 service + 收藏 API
- **M4（前端数据可视化）**: Task 7–9 — Chart.js + 仪表盘重做 + 推荐 UI
- **M5（前端 PWA + 工具）**: Task 10–13 — PWA + 离线 + 全局搜索 + 收藏夹

---

# 里程碑 M1：后端 — 知识点标签系统

## Task 1: 创建 tag_repo + tag_service

**Files:**
- Create: `backend/repositories/tag_repo.py`
- Create: `backend/services/tag_service.py`
- Test: `backend/tests/services/test_tag_service.py`

- [ ] **Step 1: 写 tag_service 测试**

Create `backend/tests/services/test_tag_service.py`:

```python
from datetime import datetime, timezone

from backend.models import Question, QuestionBank, Tag
from backend.services.tag_service import TagService


def _make_question(db_session):
    bank = QuestionBank(owner_id=1, name="课程", visibility="private",
                        created_at=datetime.now(timezone.utc))
    db_session.add(bank)
    db_session.commit()
    db_session.refresh(bank)
    q = Question(owner_id=1, course_id=bank.id, visibility="private",
                 type="single_choice", question="题干", options='{"A":"x"}',
                 answer="A", created_at=datetime.now(timezone.utc))
    db_session.add(q)
    db_session.commit()
    db_session.refresh(q)
    return bank, q


class TestTagService:
    def test_create_tag(self, db_session):
        svc = TagService(db_session)
        tag = svc.create_tag(name="微积分", color="#3b82f6")
        assert tag.id is not None
        assert tag.name == "微积分"

    def test_create_child_tag(self, db_session):
        svc = TagService(db_session)
        parent = svc.create_tag(name="高数")
        child = svc.create_tag(name="微积分", parent_id=parent.id)
        assert child.parent_id == parent.id

    def test_tag_question(self, db_session):
        _, q = _make_question(db_session)
        svc = TagService(db_session)
        tag = svc.create_tag(name="极限")
        svc.tag_question(q.id, tag.id)
        tags = svc.get_tags_for_question(q.id)
        assert len(tags) == 1
        assert tags[0].name == "极限"

    def test_tag_question_is_idempotent(self, db_session):
        _, q = _make_question(db_session)
        svc = TagService(db_session)
        tag = svc.create_tag(name="极限")
        svc.tag_question(q.id, tag.id)
        svc.tag_question(q.id, tag.id)  # duplicate, no error
        tags = svc.get_tags_for_question(q.id)
        assert len(tags) == 1

    def test_accuracy_by_tag(self, db_session):
        _, q = _make_question(db_session)
        from backend.models import PracticeRecord
        svc = TagService(db_session)
        tag = svc.create_tag(name="极限")
        svc.tag_question(q.id, tag.id)
        # 2 correct, 2 wrong
        for correct in [True, True, False, False]:
            db_session.add(PracticeRecord(
                user_id=1, question_id=q.id, course_id=q.course_id,
                question_type="single_choice", is_correct=1 if correct else 0,
                user_answer="A", correct_answer="A",
                answered_at=datetime.now(timezone.utc),
            ))
        db_session.commit()
        result = svc.get_accuracy_by_tag(user_id=1)
        assert any(r["tag_name"] == "极限" and r["accuracy"] == 0.5 for r in result)
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd backend && python -m pytest tests/services/test_tag_service.py -v`
Expected: FAIL — `ImportError`

- [ ] **Step 3: 创建 tag_repo.py**

Create `backend/repositories/tag_repo.py`:

```python
"""Repository for Tag and QuestionTag."""
from typing import Optional

from .. import models
from .base import BaseRepository


class TagRepository(BaseRepository[models.Tag]):
    model = models.Tag

    def get_by_name(self, name: str) -> Optional[models.Tag]:
        return self._query().filter(models.Tag.name == name).first()

    def get_children(self, parent_id: int) -> list[models.Tag]:
        return self._query().filter(models.Tag.parent_id == parent_id).all()

    def get_roots(self) -> list[models.Tag]:
        return self._query().filter(models.Tag.parent_id.is_(None)).all()


class QuestionTagRepository(BaseRepository[models.QuestionTag]):
    model = models.QuestionTag

    def find(self, question_id: int, tag_id: int) -> Optional[models.QuestionTag]:
        return (
            self._query()
            .filter(
                models.QuestionTag.question_id == question_id,
                models.QuestionTag.tag_id == tag_id,
            )
            .first()
        )

    def list_for_question(self, question_id: int) -> list[int]:
        """Return tag_ids for a question."""
        rows = (
            self._query()
            .filter(models.QuestionTag.question_id == question_id)
            .all()
        )
        return [r.tag_id for r in rows]

    def list_questions_for_tag(self, tag_id: int) -> list[int]:
        rows = (
            self._query()
            .filter(models.QuestionTag.tag_id == tag_id)
            .all()
        )
        return [r.question_id for r in rows]

    def attach(self, question_id: int, tag_id: int) -> models.QuestionTag:
        existing = self.find(question_id, tag_id)
        if existing:
            return existing
        qt = models.QuestionTag(question_id=question_id, tag_id=tag_id)
        self.db.add(qt)
        self.db.commit()
        self.db.refresh(qt)
        return qt

    def detach(self, question_id: int, tag_id: int) -> bool:
        qt = self.find(question_id, tag_id)
        if qt is None:
            return False
        self.db.delete(qt)
        self.db.commit()
        return True
```

- [ ] **Step 4: 创建 tag_service.py**

Create `backend/services/tag_service.py`:

```python
"""Business logic for knowledge-point tags."""
from datetime import timezone, datetime

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from .. import models
from ..repositories.tag_repo import TagRepository, QuestionTagRepository


class TagService:
    def __init__(self, db: Session):
        self.db = db
        self.tags = TagRepository(db)
        self.question_tags = QuestionTagRepository(db)

    def create_tag(self, *, name: str, color: str = "", parent_id: int | None = None) -> models.Tag:
        tag = models.Tag(name=name, color=color, parent_id=parent_id)
        return self.tags.add(tag)

    def list_tags(self) -> list[models.Tag]:
        return self.tags.get_all()

    def get_tag(self, tag_id: int):
        return self.tags.get_by_id(tag_id)

    def tag_question(self, question_id: int, tag_id: int) -> models.QuestionTag:
        return self.question_tags.attach(question_id, tag_id)

    def untag_question(self, question_id: int, tag_id: int) -> bool:
        return self.question_tags.detach(question_id, tag_id)

    def get_tags_for_question(self, question_id: int) -> list[models.Tag]:
        tag_ids = self.question_tags.list_for_question(question_id)
        if not tag_ids:
            return []
        return self.db.query(models.Tag).filter(models.Tag.id.in_(tag_ids)).all()

    def suggest_tags_for_question(self, question: models.Question, max_suggestions: int = 5) -> list[str]:
        """Suggest tag names based on question text. Phase 4 heuristic: match
        against existing tag names found in the question content. AI-powered
        suggestions are added by the import pipeline."""
        all_tags = self.list_tags()
        text = (question.question or "").lower()
        suggestions = []
        for tag in all_tags:
            if tag.name.lower() in text:
                suggestions.append(tag.name)
            if len(suggestions) >= max_suggestions:
                break
        return suggestions

    def get_accuracy_by_tag(self, *, user_id: int) -> list[dict]:
        """Accuracy per tag for a user, based on practice records."""
        # Join QuestionTag -> PracticeRecord via question_id
        rows = (
            self.db.query(
                models.Tag.id,
                models.Tag.name,
                func.count(models.PracticeRecord.id).label("total"),
                func.sum(case(
                    (models.PracticeRecord.is_correct == 1, 1), else_=0
                )).label("correct"),
            )
            .join(models.QuestionTag, models.QuestionTag.tag_id == models.Tag.id)
            .join(models.PracticeRecord, models.PracticeRecord.question_id == models.QuestionTag.question_id)
            .filter(models.PracticeRecord.user_id == user_id)
            .group_by(models.Tag.id, models.Tag.name)
            .all()
        )
        result = []
        for tag_id, name, total, correct in rows:
            total = int(total or 0)
            correct = int(correct or 0)
            result.append({
                "tag_id": tag_id,
                "tag_name": name,
                "total": total,
                "correct": correct,
                "accuracy": round(correct / total, 4) if total else 0.0,
            })
        result.sort(key=lambda x: x["accuracy"])
        return result
```

- [ ] **Step 5: 运行测试**

Run: `cd backend && python -m pytest tests/services/test_tag_service.py -v`
Expected: PASS

- [ ] **Step 6: 运行全量后端测试**

Run: `cd backend && python -m pytest -q`
Expected: PASS

- [ ] **Step 7: 提交**

```bash
git add backend/repositories/tag_repo.py backend/services/tag_service.py backend/tests/services/test_tag_service.py
git commit -m "feat(tags): add tag repository and service (CRUD + accuracy by tag)"
```

---

## Task 2: 标签 API + AI 导入时建议标签

**Files:**
- Create: `backend/api/tags.py`
- Modify: `backend/services/imports/import_orchestrator.py`（导入时建议标签）
- Modify: `backend/api/deps.py`
- Modify: `backend/main.py`
- Test: `backend/tests/api/test_tags_api.py`

- [ ] **Step 1: 写标签 API 测试**

Create `backend/tests/api/test_tags_api.py`:

```python
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.tags import router as tags_router
from backend.auth import get_current_user
from backend.database import get_db
from backend.models import User


def _make_app(db_session, user):
    app = FastAPI()
    app.include_router(tags_router)
    app.dependency_overrides[get_db] = lambda: (yield db_session)
    app.dependency_overrides[get_current_user] = lambda: user
    return app


class TestTagsApi:
    def test_create_and_list_tag(self, db_session):
        user = User(username="u", password_hash="x")
        db_session.add(user); db_session.commit(); db_session.refresh(user)
        app = _make_app(db_session, user)
        client = TestClient(app)
        resp = client.post("/tags/", json={"name": "微积分", "color": "#3b82f6"})
        assert resp.status_code == 201
        resp = client.get("/tags/")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_tag_a_question(self, db_session):
        from datetime import datetime, timezone
        from backend.models import QuestionBank, Question
        bank = QuestionBank(owner_id=1, name="c", visibility="private",
                            created_at=datetime.now(timezone.utc))
        db_session.add(bank); db_session.commit(); db_session.refresh(bank)
        q = Question(owner_id=1, course_id=bank.id, visibility="private",
                     type="single_choice", question="极限题", options='{"A":"x"}',
                     answer="A", created_at=datetime.now(timezone.utc))
        db_session.add(q); db_session.commit(); db_session.refresh(q)
        user = User(username="u", password_hash="x")
        db_session.add(user); db_session.commit(); db_session.refresh(user)

        app = _make_app(db_session, user)
        client = TestClient(app)
        tag = client.post("/tags/", json={"name": "极限"}).json()
        resp = client.post(f"/tags/{tag['id']}/questions/{q.id}")
        assert resp.status_code == 200
        resp = client.get(f"/tags/question/{q.id}")
        assert len(resp.json()) == 1
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd backend && python -m pytest tests/api/test_tags_api.py -v`
Expected: FAIL — `ImportError`

- [ ] **Step 3: 在 deps.py 添加 tag service 工厂**

修改 `backend/api/deps.py`，添加：

```python
from ..services.tag_service import TagService


def get_tag_service(db: Session = Depends(get_db)) -> TagService:
    return TagService(db)
```

- [ ] **Step 4: 创建 api/tags.py**

Create `backend/api/tags.py`:

```python
"""Tag router: CRUD + tagging questions."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import User
from ..services.tag_service import TagService
from .deps import get_tag_service

router = APIRouter(prefix="/tags", tags=["tags"])


class TagCreate(BaseModel):
    name: str
    color: str = ""
    parent_id: int | None = None


class TagOut(BaseModel):
    id: int
    name: str
    color: str = ""
    parent_id: int | None = None


@router.post("/", status_code=201, response_model=TagOut)
def create_tag(
    body: TagCreate,
    current_user: User = Depends(get_current_user),
    service: TagService = Depends(get_tag_service),
):
    tag = service.create_tag(name=body.name, color=body.color, parent_id=body.parent_id)
    return TagOut(id=tag.id, name=tag.name, color=tag.color or "", parent_id=tag.parent_id)


@router.get("/", response_model=list[TagOut])
def list_tags(
    current_user: User = Depends(get_current_user),
    service: TagService = Depends(get_tag_service),
):
    return [TagOut(id=t.id, name=t.name, color=t.color or "", parent_id=t.parent_id)
            for t in service.list_tags()]


@router.post("/{tag_id}/questions/{question_id}")
def tag_question(
    tag_id: int,
    question_id: int,
    current_user: User = Depends(get_current_user),
    service: TagService = Depends(get_tag_service),
):
    service.tag_question(question_id, tag_id)
    return {"message": "已标记"}


@router.delete("/{tag_id}/questions/{question_id}")
def untag_question(
    tag_id: int,
    question_id: int,
    current_user: User = Depends(get_current_user),
    service: TagService = Depends(get_tag_service),
):
    service.untag_question(question_id, tag_id)
    return {"message": "已取消标记"}


@router.get("/question/{question_id}", response_model=list[TagOut])
def get_tags_for_question(
    question_id: int,
    current_user: User = Depends(get_current_user),
    service: TagService = Depends(get_tag_service),
):
    return [TagOut(id=t.id, name=t.name, color=t.color or "", parent_id=t.parent_id)
            for t in service.get_tags_for_question(question_id)]


@router.get("/{tag_id}/accuracy")
def get_tag_accuracy(
    tag_id: int,
    current_user: User = Depends(get_current_user),
    service: TagService = Depends(get_tag_service),
):
    """Accuracy per tag for the current user (for recommendation/analytics)."""
    all_accuracy = service.get_accuracy_by_tag(user_id=current_user.id)
    for item in all_accuracy:
        if item["tag_id"] == tag_id:
            return item
    return {"tag_id": tag_id, "total": 0, "correct": 0, "accuracy": 0.0}
```

- [ ] **Step 5: 在 AI 导入时建议标签**

修改 `backend/services/imports/import_orchestrator.py` 的 `validate_imported_questions` 或 preview 流程，在解析完题目后调用 tag_service 建议标签。具体：在 `preview_import_from_text` 返回的每个 `ImportedQuestion` 中增加 `suggested_tags: list[str]` 字段。

先在 `backend/schemas.py` 的 `ImportedQuestion` 添加字段：
```python
class ImportedQuestion(BaseModel):
    # ...existing fields...
    suggested_tags: list[str] = []
```

然后在 orchestrator 中（preview 返回前）对每个题目调用 `TagService.suggest_tags_for_question`（基于文本匹配现有标签）。由于 preview 时题目尚未入库，用一个轻量文本匹配函数（不依赖 Question 模型）：

在 `import_orchestrator.py` 添加辅助函数：
```python
def suggest_tags_from_text(text: str, tag_service) -> list[str]:
    """Suggest tags by matching existing tag names against question text."""
    if tag_service is None:
        return []
    all_tags = tag_service.list_tags()
    text_lower = (text or "").lower()
    return [t.name for t in all_tags if t.name.lower() in text_lower][:5]
```

在 preview 流程中调用（需要 db session，从 orchestrator 传入）。此为增强功能，若 preview 流程不便注入 db，则留空列表（`suggested_tags=[]`），由前端导入预览页单独调 `/tags/` 接口做匹配。**采用后者更简单**：本 Step 仅给 schema 加字段，实际匹配逻辑放前端预览页（Task 12 导入页增强时做）。

- [ ] **Step 6: 在 main.py 挂载 tags 路由**

修改 `backend/main.py`：
```python
from .api import tags as tags_api
app.include_router(tags_api.router)
```

- [ ] **Step 7: 运行测试**

Run: `cd backend && python -m pytest tests/api/test_tags_api.py -q`
Expected: PASS

- [ ] **Step 8: 运行全量后端测试**

Run: `cd backend && python -m pytest -q`
Expected: PASS

- [ ] **Step 9: 提交**

```bash
git add backend/api/tags.py backend/api/deps.py backend/schemas.py backend/main.py backend/tests/api/test_tags_api.py
git commit -m "feat(tags): tag API + suggested_tags field on imported questions"
```

---

# 里程碑 M2：后端 — 智能推荐 + 数据分析

## Task 3: 推荐服务 + API

**Files:**
- Create: `backend/services/recommendation_service.py`
- Create: `backend/api/recommendations.py`
- Modify: `backend/api/deps.py`
- Modify: `backend/main.py`
- Test: `backend/tests/services/test_recommendation_service.py`

- [ ] **Step 1: 写推荐服务测试**

Create `backend/tests/services/test_recommendation_service.py`:

```python
from datetime import datetime, timedelta, timezone

from backend.models import Question, QuestionBank, PracticeRecord, Tag
from backend.services.recommendation_service import RecommendationService
from backend.services.tag_service import TagService


def _setup_weak_topic(db_session):
    """Create a question tagged '极限', practiced 3x all wrong."""
    bank = QuestionBank(owner_id=1, name="c", visibility="private",
                        created_at=datetime.now(timezone.utc))
    db_session.add(bank); db_session.commit(); db_session.refresh(bank)
    q = Question(owner_id=1, course_id=bank.id, visibility="private",
                 type="single_choice", question="极限题", options='{"A":"x","B":"y"}',
                 answer="A", created_at=datetime.now(timezone.utc))
    db_session.add(q); db_session.commit(); db_session.refresh(q)
    tag_svc = TagService(db_session)
    tag = tag_svc.create_tag(name="极限")
    tag_svc.tag_question(q.id, tag.id)
    for _ in range(3):
        db_session.add(PracticeRecord(
            user_id=1, question_id=q.id, course_id=bank.id,
            question_type="single_choice", is_correct=0,
            user_answer="B", correct_answer="A",
            answered_at=datetime.now(timezone.utc),
        ))
    db_session.commit()
    return q, tag


class TestRecommendationService:
    def test_today_recommendation_includes_weak_tags(self, db_session):
        _setup_weak_topic(db_session)
        svc = RecommendationService(db_session)
        rec = svc.get_today_recommendation(user_id=1)
        assert "weak_tags" in rec
        assert any(t["tag_name"] == "极限" for t in rec["weak_tags"])

    def test_today_recommendation_includes_due_reviews(self, db_session):
        from backend.models import UserQuestionReview
        # a due review (next_review_at in the past)
        db_session.add(UserQuestionReview(
            user_id=1, question_id=1, course_id=1,
            review_level=1, next_review_at=datetime.now(timezone.utc) - timedelta(days=1),
        ))
        db_session.commit()
        svc = RecommendationService(db_session)
        rec = svc.get_today_recommendation(user_id=1)
        assert rec["due_count"] >= 1

    def test_weak_questions_picks_high_error(self, db_session):
        q, tag = _setup_weak_topic(db_session)
        svc = RecommendationService(db_session)
        weak = svc.get_weak_questions(user_id=1, limit=10)
        assert any(wq.id == q.id for wq in weak)
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd backend && python -m pytest tests/services/test_recommendation_service.py -v`
Expected: FAIL — `ImportError`

- [ ] **Step 3: 实现推荐服务**

Create `backend/services/recommendation_service.py`:

```python
"""Smart recommendation engine (Phase 4).

Generates daily recommendations: weak knowledge points (accuracy < 0.7),
due spaced-repetition reviews, and the weakest questions for focused
practice.
"""
from datetime import datetime, timezone

from sqlalchemy import case, desc, func
from sqlalchemy.orm import Session

from .. import models
from ..crud_practice import get_due_reviews, get_weak_types
from ..services.tag_service import TagService

WEAK_ACCURACY_THRESHOLD = 0.7
RECOMMEND_QUESTION_LIMIT = 20


class RecommendationService:
    def __init__(self, db: Session):
        self.db = db
        self.tag_service = TagService(db)

    def get_today_recommendation(self, *, user_id: int) -> dict:
        """Composite daily recommendation: weak tags + due reviews + counts."""
        # Weak tags: accuracy < 0.7
        tag_accuracy = self.tag_service.get_accuracy_by_tag(user_id=user_id)
        weak_tags = [t for t in tag_accuracy if t["accuracy"] < WEAK_ACCURACY_THRESHOLD]

        # Due reviews
        due = get_due_reviews(self.db, user_id=user_id, limit=100)
        due_count = len(due)

        # Weak types (existing)
        weak_types = get_weak_types(self.db, user_id=user_id)

        return {
            "weak_tags": weak_tags,
            "weak_types": weak_types,
            "due_count": due_count,
            "due_question_ids": [r.question_id for r in due if r.question_id],
            "recommended_modes": self._recommended_modes(weak_tags, weak_types, due_count),
        }

    def get_weak_questions(self, *, user_id: int, limit: int = RECOMMEND_QUESTION_LIMIT) -> list[models.Question]:
        """Pick questions with the highest wrong rate for the user."""
        # Aggregate per-question wrong counts
        rows = (
            self.db.query(
                models.PracticeRecord.question_id,
                func.count(models.PracticeRecord.id).label("total"),
                func.sum(case(
                    (models.PracticeRecord.is_correct == 0, 1), else_=0
                )).label("wrong"),
            )
            .filter(
                models.PracticeRecord.user_id == user_id,
                models.PracticeRecord.question_id.is_not(None),
            )
            .group_by(models.PracticeRecord.question_id)
            .order_by(desc("wrong"))
            .limit(limit)
            .all()
        )
        qids = [r.question_id for r in rows if r.wrong and r.wrong > 0]
        if not qids:
            return []
        return self.db.query(models.Question).filter(models.Question.id.in_(qids)).all()

    def _recommended_modes(self, weak_tags, weak_types, due_count) -> list[str]:
        modes = []
        if weak_tags:
            modes.append("weak_tag_practice")
        if weak_types:
            modes.append("weak_type_practice")
        if due_count > 0:
            modes.append("spaced_repeat")
        if not modes:
            modes.append("random_practice")
        return modes
```

- [ ] **Step 4: 创建推荐 API + deps + main 挂载**

修改 `backend/api/deps.py` 添加：
```python
from ..services.recommendation_service import RecommendationService


def get_recommendation_service(db: Session = Depends(get_db)) -> RecommendationService:
    return RecommendationService(db)
```

Create `backend/api/recommendations.py`:

```python
"""Recommendation router."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import User
from ..services.recommendation_service import RecommendationService
from .deps import get_recommendation_service

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("/today")
def today(
    current_user: User = Depends(get_current_user),
    service: RecommendationService = Depends(get_recommendation_service),
):
    return service.get_today_recommendation(user_id=current_user.id)


@router.get("/weak-questions")
def weak_questions(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    service: RecommendationService = Depends(get_recommendation_service),
):
    qs = service.get_weak_questions(user_id=current_user.id, limit=limit)
    return [q.to_dict() for q in qs]
```

修改 `backend/main.py`：
```python
from .api import recommendations as recs_api
app.include_router(recs_api.router)
```

- [ ] **Step 5: 运行测试**

Run: `cd backend && python -m pytest tests/services/test_recommendation_service.py tests/api/ -q`
Expected: PASS

- [ ] **Step 6: 运行全量后端测试**

Run: `cd backend && python -m pytest -q`
Expected: PASS

- [ ] **Step 7: 提交**

```bash
git add backend/services/recommendation_service.py backend/api/recommendations.py backend/api/deps.py backend/main.py backend/tests/services/test_recommendation_service.py
git commit -m "feat(recommend): smart recommendation service + API"
```

---

## Task 4: 分析服务 + API（学生/教师视角）

**Files:**
- Create: `backend/services/analytics_service.py`
- Create: `backend/api/analytics.py`
- Modify: `backend/api/deps.py`
- Modify: `backend/main.py`
- Test: `backend/tests/services/test_analytics_service.py`

- [ ] **Step 1: 写分析服务测试**

Create `backend/tests/services/test_analytics_service.py`:

```python
from datetime import datetime, timedelta, timezone

from backend.models import PracticeRecord, Question, QuestionBank
from backend.services.analytics_service import AnalyticsService


def _seed_practice(db_session, user_id=1, days=10, per_day=3):
    bank = QuestionBank(owner_id=1, name="c", visibility="private",
                        created_at=datetime.now(timezone.utc))
    db_session.add(bank); db_session.commit(); db_session.refresh(bank)
    q = Question(owner_id=1, course_id=bank.id, visibility="private",
                 type="single_choice", question="Q", options='{"A":"x"}',
                 answer="A", created_at=datetime.now(timezone.utc))
    db_session.add(q); db_session.commit(); db_session.refresh(q)
    now = datetime.now(timezone.utc)
    for d in range(days):
        for _ in range(per_day):
            db_session.add(PracticeRecord(
                user_id=user_id, question_id=q.id, course_id=bank.id,
                question_type="single_choice", is_correct=1 if d % 2 == 0 else 0,
                user_answer="A", correct_answer="A",
                answered_at=now - timedelta(days=d),
            ))
    db_session.commit()


class TestAnalyticsService:
    def test_daily_activity_returns_counts(self, db_session):
        _seed_practice(db_session)
        svc = AnalyticsService(db_session)
        activity = svc.get_daily_activity(user_id=1, days=7)
        assert len(activity) == 7
        assert all("date" in d and "count" in d for d in activity)

    def test_type_distribution(self, db_session):
        _seed_practice(db_session)
        svc = AnalyticsService(db_session)
        dist = svc.get_type_distribution(user_id=1)
        assert any(d["type"] == "single_choice" for d in dist)

    def test_streak_calculation(self, db_session):
        _seed_practice(db_session, days=5)
        svc = AnalyticsService(db_session)
        streak = svc.get_streak(user_id=1)
        assert streak >= 1  # at least today or yesterday

    def test_teacher_course_stats(self, db_session):
        from backend.models import User
        owner = User(username="owner", password_hash="x")
        db_session.add(owner); db_session.commit(); db_session.refresh(owner)
        _seed_practice(db_session, user_id=owner.id)
        svc = AnalyticsService(db_session)
        stats = svc.get_course_stats_for_owner(owner_id=owner.id)
        assert len(stats) >= 1
        assert "practice_count" in stats[0]
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd backend && python -m pytest tests/services/test_analytics_service.py -v`
Expected: FAIL — `ImportError`

- [ ] **Step 3: 实现分析服务**

Create `backend/services/analytics_service.py`:

```python
"""Data analytics aggregation (Phase 4).

Student view: daily activity, type distribution, streak, tag accuracy.
Teacher view: course usage, score distribution, student activity.
"""
from datetime import datetime, timedelta, timezone
from collections import defaultdict

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from .. import models
from ..config import APP_TIMEZONE


class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    def get_daily_activity(self, *, user_id: int, days: int = 30) -> list[dict]:
        """Practice count per day for the last N days (in local timezone)."""
        from zoneinfo import ZoneInfo
        tz = ZoneInfo(APP_TIMEZONE)
        now_local = datetime.now(tz)
        start = (now_local - timedelta(days=days - 1)).replace(hour=0, minute=0, second=0, microsecond=0)
        start_utc = start.astimezone(timezone.utc)

        rows = (
            self.db.query(
                func.date(models.PracticeRecord.answered_at).label("day"),
                func.count(models.PracticeRecord.id).label("count"),
            )
            .filter(
                models.PracticeRecord.user_id == user_id,
                models.PracticeRecord.answered_at >= start_utc,
            )
            .group_by(func.date(models.PracticeRecord.answered_at))
            .all()
        )
        counts = {str(r.day): r.count for r in rows}

        result = []
        for i in range(days):
            day = (start + timedelta(days=i)).date()
            result.append({
                "date": day.isoformat(),
                "count": counts.get(day.isoformat(), 0),
            })
        return result

    def get_type_distribution(self, *, user_id: int) -> list[dict]:
        rows = (
            self.db.query(
                models.PracticeRecord.question_type,
                func.count(models.PracticeRecord.id),
                func.sum(case((models.PracticeRecord.is_correct == 1, 1), else_=0)),
            )
            .filter(models.PracticeRecord.user_id == user_id)
            .group_by(models.PracticeRecord.question_type)
            .all()
        )
        return [
            {"type": qt or "unknown", "total": int(total or 0), "correct": int(correct or 0)}
            for qt, total, correct in rows
        ]

    def get_streak(self, *, user_id: int) -> int:
        """Consecutive days with at least one practice, ending today/yesterday."""
        from zoneinfo import ZoneInfo
        tz = ZoneInfo(APP_TIMEZONE)
        now = datetime.now(tz)
        today = now.date()
        # Build set of practiced dates
        rows = (
            self.db.query(func.date(models.PracticeRecord.answered_at))
            .filter(models.PracticeRecord.user_id == user_id)
            .distinct().all()
        )
        practiced = {r[0] for r in rows}
        streak = 0
        cursor = today
        # If nothing today, start from yesterday (don't break streak at midday)
        if cursor not in practiced:
            cursor = cursor - timedelta(days=1)
        while cursor in practiced:
            streak += 1
            cursor = cursor - timedelta(days=1)
        return streak

    def get_course_stats_for_owner(self, *, owner_id: int) -> list[dict]:
        """Per-course usage stats for a course owner (teacher view)."""
        courses = (
            self.db.query(models.QuestionBank)
            .filter(models.QuestionBank.owner_id == owner_id)
            .all()
        )
        result = []
        for c in courses:
            qids = [q.id for q in c.questions]
            practice_count = 0
            unique_users = 0
            if qids:
                practice_count = (
                    self.db.query(func.count(models.PracticeRecord.id))
                    .filter(models.PracticeRecord.course_id == c.id)
                    .scalar() or 0
                )
                unique_users = (
                    self.db.query(func.count(func.distinct(models.PracticeRecord.user_id)))
                    .filter(models.PracticeRecord.course_id == c.id)
                    .scalar() or 0
                )
            result.append({
                "course_id": c.id,
                "course_name": c.name,
                "question_count": len(c.questions) if c.questions else 0,
                "practice_count": practice_count,
                "unique_practitioners": unique_users,
            })
        return result

    def get_score_distribution(self, *, exam_id: int) -> list[dict]:
        """Score buckets for an exam (teacher view)."""
        subs = (
            self.db.query(models.ExamSubmission.score)
            .filter(
                models.ExamSubmission.exam_id == exam_id,
                models.ExamSubmission.submitted_at.is_not(None),
            )
            .all()
        )
        buckets = defaultdict(int)
        for (score,) in subs:
            if score is None:
                continue
            bucket = (score // 10) * 10  # 0-9->0, 10-19->10, ...
            buckets[bucket] += 1
        return [{"bucket": b, "count": buckets[b]} for b in sorted(buckets)]
```

- [ ] **Step 4: 创建分析 API + deps + main 挂载**

修改 `backend/api/deps.py`：
```python
from ..services.analytics_service import AnalyticsService


def get_analytics_service(db: Session = Depends(get_db)) -> AnalyticsService:
    return AnalyticsService(db)
```

Create `backend/api/analytics.py`:

```python
"""Analytics router: student + teacher views."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import User
from ..services.analytics_service import AnalyticsService
from .deps import get_analytics_service, require_permission

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/daily-activity")
def daily_activity(
    days: int = Query(30, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    service: AnalyticsService = Depends(get_analytics_service),
):
    return service.get_daily_activity(user_id=current_user.id, days=days)


@router.get("/type-distribution")
def type_distribution(
    current_user: User = Depends(get_current_user),
    service: AnalyticsService = Depends(get_analytics_service),
):
    return service.get_type_distribution(user_id=current_user.id)


@router.get("/streak")
def streak(
    current_user: User = Depends(get_current_user),
    service: AnalyticsService = Depends(get_analytics_service),
):
    return {"streak": service.get_streak(user_id=current_user.id)}


@router.get("/teacher/courses")
def teacher_course_stats(
    current_user: User = Depends(require_permission("course:read")),
    service: AnalyticsService = Depends(get_analytics_service),
):
    return service.get_course_stats_for_owner(owner_id=current_user.id)


@router.get("/teacher/exam-scores/{exam_id}")
def exam_score_distribution(
    exam_id: int,
    current_user: User = Depends(require_permission("exam:view_leaderboard")),
    service: AnalyticsService = Depends(get_analytics_service),
):
    return service.get_score_distribution(exam_id=exam_id)
```

修改 `backend/main.py`：
```python
from .api import analytics as analytics_api
app.include_router(analytics_api.router)
```

- [ ] **Step 5: 运行测试**

Run: `cd backend && python -m pytest tests/services/test_analytics_service.py -q`
Expected: PASS

- [ ] **Step 6: 运行全量后端测试**

Run: `cd backend && python -m pytest -q`
Expected: PASS

- [ ] **Step 7: 提交**

```bash
git add backend/services/analytics_service.py backend/api/analytics.py backend/api/deps.py backend/main.py backend/tests/services/test_analytics_service.py
git commit -m "feat(analytics): analytics service + API (student/teacher views)"
```

---

# 里程碑 M3：后端 — 导出 + 收藏

## Task 5: 导出服务 + API（JSON/Excel/CSV）

**Files:**
- Modify: `backend/requirements.txt`（加 openpyxl）
- Create: `backend/services/export_service.py`
- Create: `backend/api/exports.py`
- Modify: `backend/main.py`
- Test: `backend/tests/services/test_export_service.py`

- [ ] **Step 1: 安装 openpyxl**

修改 `backend/requirements.txt` 添加 `openpyxl>=3.1.0`。
Run: `cd backend && pip install openpyxl`

- [ ] **Step 2: 写导出服务测试**

Create `backend/tests/services/test_export_service.py`:

```python
import csv
import io
import json
from datetime import datetime, timezone

from backend.models import Question, QuestionBank
from backend.services.export_service import ExportService


def _make_course_with_questions(db_session, n=3):
    bank = QuestionBank(owner_id=1, name="导出课程", visibility="private",
                        created_at=datetime.now(timezone.utc))
    db_session.add(bank); db_session.commit(); db_session.refresh(bank)
    for i in range(n):
        db_session.add(Question(
            owner_id=1, course_id=bank.id, visibility="private",
            type="single_choice", question=f"Q{i}", options='{"A":"x"}',
            answer="A", subject="科目", chapter="章节",
            created_at=datetime.now(timezone.utc),
        ))
    db_session.commit()
    return bank


class TestExportService:
    def test_export_course_json(self, db_session):
        bank = _make_course_with_questions(db_session)
        svc = ExportService(db_session)
        data = svc.export_course_json(bank.id)
        parsed = json.loads(data)
        assert parsed["name"] == "导出课程"
        assert len(parsed["questions"]) == 3

    def test_export_practice_csv(self, db_session):
        from backend.models import PracticeRecord
        bank = _make_course_with_questions(db_session)
        q = bank.questions[0]
        db_session.add(PracticeRecord(
            user_id=1, question_id=q.id, course_id=bank.id,
            question_type="single_choice", is_correct=1,
            user_answer="A", correct_answer="A",
            answered_at=datetime.now(timezone.utc),
        ))
        db_session.commit()
        svc = ExportService(db_session)
        csv_data = svc.export_practice_history_csv(user_id=1)
        reader = csv.DictReader(io.StringIO(csv_data))
        rows = list(reader)
        assert len(rows) == 1
        assert "question_type" in rows[0]

    def test_export_course_excel_returns_bytes(self, db_session):
        bank = _make_course_with_questions(db_session, 2)
        svc = ExportService(db_session)
        data = svc.export_course_excel(bank.id)
        # xlsx files start with PK zip signature
        assert data[:2] == b"PK"
```

- [ ] **Step 3: 运行测试确认失败**

Run: `cd backend && python -m pytest tests/services/test_export_service.py -v`
Expected: FAIL — `ImportError`

- [ ] **Step 4: 实现导出服务**

Create `backend/services/export_service.py`:

```python
"""Data export service (Phase 4): JSON / Excel / CSV."""
import csv
import io
import json

from sqlalchemy.orm import Session

from .. import models


class ExportService:
    def __init__(self, db: Session):
        self.db = db

    def export_course_json(self, course_id: int) -> str:
        """Export a course and its questions as a JSON string."""
        bank = self.db.query(models.QuestionBank).filter(
            models.QuestionBank.id == course_id
        ).first()
        if bank is None:
            raise ValueError("课程不存在")
        questions = (
            self.db.query(models.Question)
            .filter(models.Question.course_id == course_id)
            .order_by(models.Question.id)
            .all()
        )
        return json.dumps({
            "name": bank.name,
            "description": bank.description or "",
            "subject": bank.subject or "",
            "questions": [q.to_dict() for q in questions],
        }, ensure_ascii=False, indent=2)

    def export_course_excel(self, course_id: int) -> bytes:
        """Export course questions as an .xlsx file (bytes)."""
        from openpyxl import Workbook

        bank = self.db.query(models.QuestionBank).filter(
            models.QuestionBank.id == course_id
        ).first()
        if bank is None:
            raise ValueError("课程不存在")
        questions = (
            self.db.query(models.Question)
            .filter(models.Question.course_id == course_id)
            .order_by(models.Question.id)
            .all()
        )
        wb = Workbook()
        ws = wb.active
        ws.title = "题目"
        ws.append(["ID", "类型", "科目", "章节", "题干", "选项", "答案", "解析", "难度"])
        for q in questions:
            opts = q.get_options_dict()
            opts_str = json.dumps(opts, ensure_ascii=False) if opts else ""
            ws.append([
                q.id, q.type, q.subject or "", q.chapter or "",
                q.question, opts_str, q.answer, q.analysis or "", q.difficulty or "",
            ])
        buf = io.BytesIO()
        wb.save(buf)
        return buf.getvalue()

    def export_practice_history_csv(self, *, user_id: int) -> str:
        """Export the user's practice history as CSV string."""
        records = (
            self.db.query(models.PracticeRecord)
            .filter(models.PracticeRecord.user_id == user_id)
            .order_by(models.PracticeRecord.answered_at.desc())
            .all()
        )
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow([
            "id", "question_id", "course_id", "question_type",
            "is_correct", "user_answer", "correct_answer", "answered_at",
        ])
        for r in records:
            writer.writerow([
                r.id, r.question_id, r.course_id, r.question_type or "",
                "正确" if r.is_correct else "错误",
                r.user_answer or "", r.correct_answer or "",
                r.answered_at.isoformat() if r.answered_at else "",
            ])
        return buf.getvalue()
```

- [ ] **Step 5: 创建导出 API + main 挂载**

Create `backend/api/exports.py`:

```python
"""Export router: download course/practice data."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import User
from ..services.export_service import ExportService

router = APIRouter(prefix="/exports", tags=["exports"])


@router.get("/courses/{course_id}.json")
def export_course_json(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    svc = ExportService(db)
    try:
        data = svc.export_course_json(course_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return Response(
        content=data, media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="course_{course_id}.json"'},
    )


@router.get("/courses/{course_id}.xlsx")
def export_course_excel(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    svc = ExportService(db)
    try:
        data = svc.export_course_excel(course_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="course_{course_id}.xlsx"'},
    )


@router.get("/practice-history.csv")
def export_practice_csv(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    svc = ExportService(db)
    data = svc.export_practice_history_csv(user_id=current_user.id)
    return Response(
        content=data, media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="practice_history.csv"'},
    )
```

修改 `backend/main.py`：
```python
from .api import exports as exports_api
app.include_router(exports_api.router)
```

- [ ] **Step 6: 运行测试**

Run: `cd backend && python -m pytest tests/services/test_export_service.py -q`
Expected: PASS

- [ ] **Step 7: 运行全量后端测试**

Run: `cd backend && python -m pytest -q`
Expected: PASS

- [ ] **Step 8: 提交**

```bash
git add backend/requirements.txt backend/services/export_service.py backend/api/exports.py backend/main.py backend/tests/services/test_export_service.py
git commit -m "feat(export): JSON/Excel/CSV export service + API"
```

---

## Task 6: 收藏 API

**Files:**
- Create: `backend/repositories/bookmark_repo.py`
- Create: `backend/api/bookmarks.py`
- Modify: `backend/api/deps.py`
- Modify: `backend/main.py`
- Test: `backend/tests/api/test_bookmarks_api.py`

- [ ] **Step 1: 写收藏 API 测试**

Create `backend/tests/api/test_bookmarks_api.py`:

```python
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.bookmarks import router as bookmarks_router
from backend.auth import get_current_user
from backend.database import get_db
from backend.models import User, Question, QuestionBank


def _setup(db_session):
    user = User(username="u", password_hash="x")
    db_session.add(user)
    bank = QuestionBank(owner_id=1, name="c", visibility="private",
                        created_at=datetime.now(timezone.utc))
    db_session.add(bank)
    db_session.commit()
    db_session.refresh(user); db_session.refresh(bank)
    q = Question(owner_id=1, course_id=bank.id, visibility="private",
                 type="single_choice", question="Q", options='{"A":"x"}',
                 answer="A", created_at=datetime.now(timezone.utc))
    db_session.add(q); db_session.commit(); db_session.refresh(q)
    return user, q


def _make_app(db_session, user):
    app = FastAPI()
    app.include_router(bookmarks_router)
    app.dependency_overrides[get_db] = lambda: (yield db_session)
    app.dependency_overrides[get_current_user] = lambda: user
    return app


class TestBookmarksApi:
    def test_add_and_list_bookmark(self, db_session):
        user, q = _setup(db_session)
        app = _make_app(db_session, user)
        client = TestClient(app)
        resp = client.post("/bookmarks/", json={"question_id": q.id, "folder_name": "重点"})
        assert resp.status_code == 201
        resp = client.get("/bookmarks/")
        assert resp.status_code == 200
        assert len(resp.json()["items"]) == 1

    def test_add_bookmark_is_idempotent(self, db_session):
        user, q = _setup(db_session)
        app = _make_app(db_session, user)
        client = TestClient(app)
        client.post("/bookmarks/", json={"question_id": q.id})
        client.post("/bookmarks/", json={"question_id": q.id})  # duplicate
        resp = client.get("/bookmarks/")
        assert len(resp.json()["items"]) == 1

    def test_remove_bookmark(self, db_session):
        user, q = _setup(db_session)
        app = _make_app(db_session, user)
        client = TestClient(app)
        client.post("/bookmarks/", json={"question_id": q.id})
        resp = client.delete(f"/bookmarks/{q.id}")
        assert resp.status_code == 200
        resp = client.get("/bookmarks/")
        assert len(resp.json()["items"]) == 0
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd backend && python -m pytest tests/api/test_bookmarks_api.py -v`
Expected: FAIL — `ImportError`

- [ ] **Step 3: 创建 bookmark_repo.py**

Create `backend/repositories/bookmark_repo.py`:

```python
"""Repository for Bookmark."""
from datetime import datetime, timezone
from typing import Optional

from .. import models
from .base import BaseRepository


class BookmarkRepository(BaseRepository[models.Bookmark]):
    model = models.Bookmark

    def find(self, user_id: int, question_id: int) -> Optional[models.Bookmark]:
        return (
            self._query()
            .filter(
                models.Bookmark.user_id == user_id,
                models.Bookmark.question_id == question_id,
            )
            .first()
        )

    def list_for_user(self, *, user_id: int, folder: str | None = None) -> list[models.Bookmark]:
        query = self._query().filter(models.Bookmark.user_id == user_id)
        if folder:
            query = query.filter(models.Bookmark.folder_name == folder)
        return query.order_by(models.Bookmark.created_at.desc()).all()

    def add(self, *, user_id: int, question_id: int, folder_name: str = "默认收藏",
            note: str = "") -> models.Bookmark:
        existing = self.find(user_id, question_id)
        if existing:
            existing.folder_name = folder_name
            existing.note = note
            self.db.commit()
            self.db.refresh(existing)
            return existing
        bm = models.Bookmark(
            user_id=user_id, question_id=question_id,
            folder_name=folder_name, note=note,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(bm)
        self.db.commit()
        self.db.refresh(bm)
        return bm

    def remove(self, user_id: int, question_id: int) -> bool:
        bm = self.find(user_id, question_id)
        if bm is None:
            return False
        self.db.delete(bm)
        self.db.commit()
        return True

    def list_folders(self, user_id: int) -> list[str]:
        rows = (
            self._query()
            .filter(models.Bookmark.user_id == user_id)
            .distinct(models.Bookmark.folder_name)
            .all()
        )
        return list({r.folder_name for r in rows if r.folder_name})
```

- [ ] **Step 4: 创建收藏 API + deps + main**

修改 `backend/api/deps.py`：
```python
from ..repositories.bookmark_repo import BookmarkRepository


def get_bookmark_repo(db: Session = Depends(get_db)) -> BookmarkRepository:
    return BookmarkRepository(db)
```

Create `backend/api/bookmarks.py`:

```python
"""Bookmark router: save/organize questions."""
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import User
from ..repositories.bookmark_repo import BookmarkRepository
from .deps import get_bookmark_repo

router = APIRouter(prefix="/bookmarks", tags=["bookmarks"])


class BookmarkCreate(BaseModel):
    question_id: int
    folder_name: str = "默认收藏"
    note: str = ""


@router.post("/", status_code=201)
def add_bookmark(
    body: BookmarkCreate,
    current_user: User = Depends(get_current_user),
    repo: BookmarkRepository = Depends(get_bookmark_repo),
):
    bm = repo.add(user_id=current_user.id, question_id=body.question_id,
                  folder_name=body.folder_name, note=body.note)
    return {"id": bm.id, "question_id": bm.question_id, "folder_name": bm.folder_name}


@router.get("/")
def list_bookmarks(
    folder: str = Query("", description="按收藏夹筛选"),
    current_user: User = Depends(get_current_user),
    repo: BookmarkRepository = Depends(get_bookmark_repo),
    db: Session = Depends(get_db),
):
    bms = repo.list_for_user(user_id=current_user.id,
                             folder=folder or None)
    items = []
    for bm in bms:
        item = {
            "id": bm.id, "question_id": bm.question_id,
            "folder_name": bm.folder_name, "note": bm.note or "",
            "created_at": bm.created_at.isoformat() if bm.created_at else None,
        }
        if bm.question:
            item["question"] = bm.question.to_dict()
        items.append(item)
    return {"items": items, "total": len(items), "folders": repo.list_folders(current_user.id)}


@router.delete("/{question_id}")
def remove_bookmark(
    question_id: int,
    current_user: User = Depends(get_current_user),
    repo: BookmarkRepository = Depends(get_bookmark_repo),
):
    repo.remove(user_id=current_user.id, question_id=question_id)
    return {"message": "已取消收藏"}
```

修改 `backend/main.py`：
```python
from .api import bookmarks as bookmarks_api
app.include_router(bookmarks_api.router)
```

- [ ] **Step 5: 运行测试**

Run: `cd backend && python -m pytest tests/api/test_bookmarks_api.py -q`
Expected: PASS

- [ ] **Step 6: 运行全量后端测试**

Run: `cd backend && python -m pytest -q`
Expected: PASS

- [ ] **Step 7: 提交**

```bash
git add backend/repositories/bookmark_repo.py backend/api/bookmarks.py backend/api/deps.py backend/main.py backend/tests/api/test_bookmarks_api.py
git commit -m "feat(bookmarks): bookmark repository + API (folders, idempotent add)"
```

---

# 里程碑 M4：前端 — 数据可视化

## Task 7: 引入 Chart.js + 图表组件

**Files:**
- Modify: `frontend/package.json`
- Create: `frontend/src/components/charts/ActivityChart.vue`
- Create: `frontend/src/components/charts/TypeDistributionChart.vue`
- Create: `frontend/src/components/charts/TagAccuracyRadar.vue`
- Create: `frontend/src/api/analytics.ts`

- [ ] **Step 1: 安装 Chart.js**

Run: `cd frontend && npm install chart.js vue-chartjs`

- [ ] **Step 2: 创建 analytics API 层**

Create `frontend/src/api/analytics.ts`:

```typescript
import request from "./request";

export interface DailyActivity {
  date: string;
  count: number;
}

export interface TypeDistribution {
  type: string;
  total: number;
  correct: number;
}

export async function getDailyActivity(days = 30): Promise<DailyActivity[]> {
  return request.get("/analytics/daily-activity", { params: { days } }).then(({ data }) => data);
}

export async function getTypeDistribution(): Promise<TypeDistribution[]> {
  return request.get("/analytics/type-distribution").then(({ data }) => data);
}

export async function getStreak(): Promise<{ streak: number }> {
  return request.get("/analytics/streak").then(({ data }) => data);
}

export async function getTeacherCourseStats() {
  return request.get("/analytics/teacher/courses").then(({ data }) => data);
}
```

- [ ] **Step 3: 创建 ActivityChart.vue（每日练习折线图）**

Create `frontend/src/components/charts/ActivityChart.vue`:

```vue
<script setup lang="ts">
import { computed } from "vue";
import { Line } from "vue-chartjs";
import {
  Chart as ChartJS, CategoryScale, LinearScale,
  PointElement, LineElement, Title, Tooltip, Filler,
} from "chart.js";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Filler);

const props = defineProps<{ data: { date: string; count: number }[] }>();

const chartData = computed(() => ({
  labels: props.data.map(d => d.date.slice(5)),  // MM-DD
  datasets: [{
    label: "练习题数",
    data: props.data.map(d => d.count),
    borderColor: "#3b82f6",
    backgroundColor: "rgba(59,130,246,0.15)",
    fill: true,
    tension: 0.3,
  }],
}));

const options = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { display: false } },
  scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
};
</script>

<template>
  <div class="h-48">
    <Line :data="chartData" :options="options" />
  </div>
</template>
```

- [ ] **Step 4: 创建 TypeDistributionChart.vue（题型正确率饼图）**

Create `frontend/src/components/charts/TypeDistributionChart.vue`:

```vue
<script setup lang="ts">
import { computed } from "vue";
import { Doughnut } from "vue-chartjs";
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from "chart.js";

ChartJS.register(ArcElement, Tooltip, Legend);

const TYPE_LABELS: Record<string, string> = {
  single_choice: "单选", multiple_choice: "多选", true_false: "判断",
  fill_blank: "填空", short_answer: "简答",
};

const props = defineProps<{ data: { type: string; total: number; correct: number }[] }>();

const chartData = computed(() => ({
  labels: props.data.map(d => TYPE_LABELS[d.type] || d.type),
  datasets: [{
    data: props.data.map(d => d.total),
    backgroundColor: ["#3b82f6", "#0d9488", "#7c3aed", "#d97706", "#059669"],
  }],
}));

const options = { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: "right" as const } } };
</script>

<template>
  <div class="h-48">
    <Doughnut :data="chartData" :options="options" />
  </div>
</template>
```

- [ ] **Step 5: 创建 TagAccuracyRadar.vue（知识点雷达图）**

Create `frontend/src/components/charts/TagAccuracyRadar.vue`:

```vue
<script setup lang="ts">
import { computed } from "vue";
import { Radar } from "vue-chartjs";
import { Chart as ChartJS, RadialLinearScale, PointElement, LineElement, Filler, Tooltip } from "chart.js";

ChartJS.register(RadialLinearScale, PointElement, LineElement, Filler, Tooltip);

const props = defineProps<{ data: { tag_name: string; accuracy: number }[] }>();

const top = computed(() => props.data.slice(0, 8));

const chartData = computed(() => ({
  labels: top.value.map(d => d.tag_name),
  datasets: [{
    label: "正确率",
    data: top.value.map(d => Math.round(d.accuracy * 100)),
    backgroundColor: "rgba(59,130,246,0.2)",
    borderColor: "#3b82f6",
    pointBackgroundColor: "#3b82f6",
  }],
}));

const options = {
  responsive: true,
  maintainAspectRatio: false,
  scales: {
    r: { beginAtZero: true, max: 100, ticks: { stepSize: 25 } },
  },
};
</script>

<template>
  <div class="h-56">
    <Radar :data="chartData" :options="options" />
  </div>
</template>
```

- [ ] **Step 6: typecheck + build**

Run: `cd frontend && npm run typecheck && npm run build`
Expected: PASS

- [ ] **Step 7: 提交**

```bash
git add frontend/package.json frontend/package-lock.json frontend/src/api/analytics.ts frontend/src/components/charts/
git commit -m "feat(charts): add Chart.js + activity/type/tag-accuracy charts"
```

---

## Task 8: 重做 StudyOverview 为数据仪表盘

**Files:**
- Modify: `frontend/src/views/StudyOverview.vue`

- [ ] **Step 1: 读取现有 StudyOverview**

Run: `cat frontend/src/views/StudyOverview.vue`

- [ ] **Step 2: 用图表组件重做仪表盘**

修改 `frontend/src/views/StudyOverview.vue`，整合图表组件 + 推荐 + streak。结构：

```vue
<script setup lang="ts">
import { onMounted, ref } from "vue";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import ActivityChart from "@/components/charts/ActivityChart.vue";
import TypeDistributionChart from "@/components/charts/TypeDistributionChart.vue";
import TagAccuracyRadar from "@/components/charts/TagAccuracyRadar.vue";
import { useStudyOverview } from "@/composables/useStudyOverview";
import { getDailyActivity, getTypeDistribution, getStreak } from "@/api/analytics";
import { listTags } from "@/api/tag";
import type { DailyActivity, TypeDistribution } from "@/api/analytics";

const { stats, loading, errorMessage, fetchAll } = useStudyOverview();
const activity = ref<DailyActivity[]>([]);
const typeDist = ref<TypeDistribution[]>([]);
const tagAccuracy = ref<{ tag_name: string; accuracy: number }[]>([]);
const streak = ref(0);

onMounted(async () => {
  fetchAll();
  try {
    const [act, types, streakData] = await Promise.all([
      getDailyActivity(30),
      getTypeDistribution(),
      getStreak(),
    ]);
    activity.value = act;
    typeDist.value = types;
    streak.value = streakData.streak;
  } catch (e) {
    // 部分加载失败不阻塞整体
  }
});
</script>

<template>
  <section class="mx-auto max-w-5xl space-y-4 p-4">
    <div class="grid grid-cols-2 gap-3 md:grid-cols-4">
      <Card>
        <CardContent class="text-center">
          <div class="text-2xl font-bold text-[var(--primary)]">{{ stats.todayCount ?? "--" }}</div>
          <div class="text-xs text-[var(--text-muted)]">今日练习</div>
        </CardContent>
      </Card>
      <Card>
        <CardContent class="text-center">
          <div class="text-2xl font-bold text-[var(--emerald)]">{{ streak }}</div>
          <div class="text-xs text-[var(--text-muted)]">连续天数</div>
        </CardContent>
      </Card>
      <Card>
        <CardContent class="text-center">
          <div class="text-2xl font-bold text-[var(--text-main)]">
            {{ stats.accuracyRate !== null ? Math.round(stats.accuracyRate * 100) + "%" : "--" }}
          </div>
          <div class="text-xs text-[var(--text-muted)]">总正确率</div>
        </CardContent>
      </Card>
      <Card>
        <CardContent class="text-center">
          <div class="text-2xl font-bold text-[var(--text-main)]">{{ stats.totalCount ?? "--" }}</div>
          <div class="text-xs text-[var(--text-muted)]">总练习数</div>
        </CardContent>
      </Card>
    </div>

    <div class="grid gap-4 md:grid-cols-2">
      <Card>
        <CardHeader><CardTitle>近 30 日练习趋势</CardTitle></CardHeader>
        <CardContent>
          <ActivityChart :data="activity" />
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>题型分布</CardTitle></CardHeader>
        <CardContent>
          <TypeDistributionChart :data="typeDist" />
        </CardContent>
      </Card>
    </div>

    <Card>
      <CardHeader><CardTitle>知识点掌握度</CardTitle></CardHeader>
      <CardContent>
        <TagAccuracyRadar v-if="tagAccuracy.length" :data="tagAccuracy" />
        <p v-else class="text-center text-[var(--text-muted)]">暂无标签数据，请先为题目添加知识点标签</p>
      </CardContent>
    </Card>
  </section>
</template>
```

注意：`listTags` 和 tag accuracy API 需在 `frontend/src/api/tag.ts` 创建（见 Task 12 或此处简创建）。为避免 Task 依赖错乱，本 Step 先用空数组占位 `tagAccuracy`（雷达图显示"暂无数据"），完整接入留 Task 12。

创建 `frontend/src/api/tag.ts`:
```typescript
import request from "./request";
export function listTags() {
  return request.get("/tags/").then(({ data }) => data);
}
```

- [ ] **Step 3: typecheck + build + 手动验证**

Run: `cd frontend && npm run typecheck && npm run build`
Expected: PASS
手动验证：学习概览页显示折线图、饼图、雷达图占位。

- [ ] **Step 4: 提交**

```bash
git add frontend/src/views/StudyOverview.vue frontend/src/api/tag.ts
git commit -m "refactor(study-overview): rebuild as data dashboard with charts"
```

---

## Task 9: 推荐 UI + 弱项练习入口

**Files:**
- Create: `frontend/src/api/recommendation.ts`
- Create: `frontend/src/components/recommend/TodayRecommendation.vue`
- Modify: `frontend/src/views/PracticeHub.vue`

- [ ] **Step 1: 创建推荐 API 层**

Create `frontend/src/api/recommendation.ts`:

```typescript
import request from "./request";
import type { WeakType } from "@/types";

export interface TodayRecommendation {
  weak_tags: { tag_id: number; tag_name: string; accuracy: number }[];
  weak_types: WeakType[];
  due_count: number;
  due_question_ids: number[];
  recommended_modes: string[];
}

export function getTodayRecommendation(): Promise<TodayRecommendation> {
  return request.get("/recommendations/today").then(({ data }) => data);
}

export function getWeakQuestions(limit = 20) {
  return request.get("/recommendations/weak-questions", { params: { limit } }).then(({ data }) => data);
}
```

- [ ] **Step 2: 创建推荐卡片组件**

Create `frontend/src/components/recommend/TodayRecommendation.vue`:

```vue
<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Target, Clock, AlertCircle } from "@lucide/vue";  // 或 lucide-vue-next
import { getTodayRecommendation, type TodayRecommendation } from "@/api/recommendation";

const router = useRouter();
const rec = ref<TodayRecommendation | null>(null);
const loading = ref(true);

onMounted(async () => {
  try {
    rec.value = await getTodayRecommendation();
  } finally {
    loading.value = false;
  }
});

function practiceWeakTags() {
  router.push({ name: "practice-weak" });  // 复用或新建弱项练习路由
}
</script>

<template>
  <Card>
    <CardHeader><CardTitle>今日推荐</CardTitle></CardHeader>
    <CardContent>
      <p v-if="loading" class="text-[var(--text-muted)]">加载中…</p>
      <div v-else-if="rec" class="space-y-3">
        <div v-if="rec.weak_tags.length" class="flex items-start gap-2">
          <AlertCircle :size="18" class="mt-0.5 text-[var(--rose)]" />
          <div class="flex-1 text-sm">
            <p class="font-medium text-[var(--text-main)]">薄弱知识点</p>
            <p class="text-[var(--text-muted)]">
              <span v-for="t in rec.weak_tags.slice(0, 3)" :key="t.tag_id"
                    class="mr-2 inline-block rounded-full bg-[var(--rose-soft)] px-2 py-0.5 text-xs text-[var(--rose)]">
                {{ t.tag_name }} {{ Math.round(t.accuracy * 100) }}%
              </span>
            </p>
          </div>
        </div>

        <div v-if="rec.due_count > 0" class="flex items-start gap-2">
          <Clock :size="18" class="mt-0.5 text-[var(--amber)]" />
          <div class="flex-1 text-sm">
            <p class="font-medium text-[var(--text-main)]">到期复习</p>
            <p class="text-[var(--text-muted)]">{{ rec.due_count }} 题待复习</p>
          </div>
        </div>

        <div class="flex gap-2 pt-2">
          <Button v-if="rec.weak_tags.length" size="sm" @click="practiceWeakTags">
            <Target :size="14" /> 薄弱项练习
          </Button>
          <Button v-if="rec.due_count > 0" size="sm" variant="outline"
                  @click="router.push({ name: 'practice-due' })">
            复习到期题
          </Button>
        </div>
      </div>
      <p v-else class="text-[var(--text-muted)]">暂无推荐，多练习几题试试</p>
    </CardContent>
  </Card>
</template>
```

- [ ] **Step 3: 在 PracticeHub 顶部嵌入推荐卡片**

修改 `frontend/src/views/PracticeHub.vue`，在页面顶部（现有 DailyStatsCard 之前）添加：

```vue
<script setup lang="ts">
// ...现有 imports...
import TodayRecommendation from "@/components/recommend/TodayRecommendation.vue";
</script>

<template>
  <section class="space-y-4">
    <TodayRecommendation />
    <!-- 现有内容 -->
  </section>
</template>
```

- [ ] **Step 4: typecheck + build + 手动验证**

Run: `cd frontend && npm run typecheck && npm run build`
Expected: PASS
手动验证：练习 Hub 顶部显示今日推荐卡片，薄弱知识点和到期题数量正确。

- [ ] **Step 5: 提交**

```bash
git add frontend/src/api/recommendation.ts frontend/src/components/recommend/ frontend/src/views/PracticeHub.vue
git commit -m "feat(recommend-ui): today recommendation card in practice hub"
```

---

# 里程碑 M5：前端 — PWA + 工具增强

## Task 10: PWA 基础（manifest + Workbox service worker）

**Files:**
- Modify: `frontend/package.json`（vite-plugin-pwa）
- Modify: `frontend/vite.config.ts`
- Modify: `frontend/index.html`
- Create: `frontend/public/icon-192.png`、`icon-512.png`（占位）
- Modify: `frontend/src/main.ts`

- [ ] **Step 1: 安装 vite-plugin-pwa**

Run: `cd frontend && npm install -D vite-plugin-pwa`

- [ ] **Step 2: 配置 VitePWA 插件**

修改 `frontend/vite.config.ts`：

```typescript
import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import { fileURLToPath, URL } from "node:url";
import { VitePWA } from "vite-plugin-pwa";

export default defineConfig({
  plugins: [
    vue(),
    VitePWA({
      registerType: "autoUpdate",
      includeAssets: ["icon-192.png", "icon-512.png"],
      manifest: {
        name: "考前刷题复习系统",
        short_name: "刷题",
        description: "AI 驱动的考前复习与考试平台",
        theme_color: "#3b82f6",
        background_color: "#f4f6fb",
        display: "standalone",
        start_url: "/",
        icons: [
          { src: "icon-192.png", sizes: "192x192", type: "image/png" },
          { src: "icon-512.png", sizes: "512x512", type: "image/png" },
        ],
      },
      workbox: {
        globPatterns: ["**/*.{js,css,html,svg,png,woff2}"],
        // Runtime caching: API Network-First, static Cache-First
        runtimeCaching: [
          {
            urlPattern: /^\/(auth|practice|courses|questions|recommendations|analytics)/,
            handler: "NetworkFirst",
            options: { cacheName: "api-cache", networkTimeoutSeconds: 5 },
          },
          {
            urlPattern: /\.(?:js|css|woff2|png|svg)$/,
            handler: "CacheFirst",
            options: { cacheName: "asset-cache" },
          },
        ],
      },
    }),
  ],
  resolve: {
    alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) },
  },
});
```

- [ ] **Step 3: 生成占位图标**

用任意工具生成两个简单 PNG（192×192、512×512），或用一个纯色方块占位。放到 `frontend/public/`。

若无工具，可用 SVG 转 PNG 的在线工具或暂时用现有项目的任何 PNG 复制为这两个名字（功能验证用）。

- [ ] **Step 4: typecheck + build 验证 PWA 产物**

Run: `cd frontend && npm run build`
Expected: build 成功，`dist/` 下出现 `manifest.webmanifest`、`registerSW.js`、`sw.js`、`workbox-*.js`。

- [ ] **Step 5: 手动验证 PWA 安装**

Run: `cd frontend && npm run preview`
用 Chrome 打开，DevTools → Application → Manifest 确认 manifest 加载，Service Workers 确认 sw.js 注册。地址栏应出现"安装"图标。

- [ ] **Step 6: 提交**

```bash
git add frontend/package.json frontend/package-lock.json frontend/vite.config.ts frontend/public/icon-192.png frontend/public/icon-512.png
git commit -m "feat(pwa): add manifest + Workbox service worker"
```

---

## Task 11: 离线练习（IndexedDB 队列 + 同步）

**Files:**
- Create: `frontend/src/composables/useOfflineSync.ts`
- Test: `frontend/src/composables/__tests__/useOfflineSync.spec.ts`

- [ ] **Step 1: 写离线同步测试**

Create `frontend/src/composables/__tests__/useOfflineSync.spec.ts`:

```typescript
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useOfflineSync } from "../useOfflineSync";

// Mock IndexedDB with a simple in-memory store
const stores: Record<string, any[]> = {};

vi.stubGlobal("indexedDB", {
  open: vi.fn(() => {
    const req = {
      onsuccess: null as any, onerror: null as any, onupgradeneeded: null as any,
      result: {
        objectStoreNames: { contains: () => false },
        createObjectStore: (name: string) => { stores[name] = []; },
        transaction: (name: string) => ({
          objectStore: () => ({
            add: (item: any) => { stores[name].push(item); return { onsuccess: null, onerror: null }; },
            getAll: () => ({ onsuccess: null, result: stores[name] || [] }),
            clear: () => { stores[name] = []; },
          }),
        }),
      },
    };
    setTimeout(() => req.onsuccess && req.onsuccess(), 0);
    return req;
  }),
});

vi.stubGlobal("navigator", { onLine: true });

describe("useOfflineSync", () => {
  beforeEach(() => {
    Object.keys(stores).forEach(k => delete stores[k]);
  });

  it("reports online status", () => {
    const { isOnline } = useOfflineSync();
    expect(isOnline.value).toBe(true);
  });

  it("enqueue stores a practice answer", async () => {
    const { enqueue, pendingCount } = useOfflineSync();
    await enqueue({ type: "practice", payload: { question_id: 1 } });
    expect(pendingCount.value).toBe(1);
  });
});
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd frontend && npx vitest run src/composables/__tests__/useOfflineSync.spec.ts`
Expected: FAIL

- [ ] **Step 3: 实现离线同步 composable**

Create `frontend/src/composables/useOfflineSync.ts`:

```typescript
import { ref, onMounted, onUnmounted } from "vue";

const DB_NAME = "exam-offline";
const STORE = "pending-queue";
let dbPromise: Promise<IDBDatabase> | null = null;

function openDB(): Promise<IDBDatabase> {
  if (dbPromise) return dbPromise;
  dbPromise = new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, 1);
    req.onupgradeneeded = () => {
      const db = req.result;
      if (!db.objectStoreNames.contains(STORE)) {
        db.createObjectStore(STORE, { autoIncrement: true });
      }
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
  return dbPromise;
}

export interface PendingAction {
  type: "practice" | "bookmark";
  payload: Record<string, unknown>;
  created_at: string;
}

export function useOfflineSync() {
  const isOnline = ref(navigator.onLine);
  const pendingCount = ref(0);

  async function refreshCount() {
    try {
      const db = await openDB();
      const tx = db.transaction(STORE, "readonly");
      const store = tx.objectStore(STORE);
      const req = store.count();
      req.onsuccess = () => { pendingCount.value = req.result; };
    } catch {
      // IndexedDB unavailable
    }
  }

  async function enqueue(action: Omit<PendingAction, "created_at">): Promise<void> {
    const db = await openDB();
    const tx = db.transaction(STORE, "readwrite");
    tx.objectStore(STORE).add({ ...action, created_at: new Date().toISOString() });
    await refreshCount();
  }

  function onOnline() { isOnline.value = true; void flush(); }
  function onOffline() { isOnline.value = false; }

  async function flush(): Promise<void> {
    if (!navigator.onLine) return;
    // Read all pending, POST them, clear on success.
    // Actual submission logic wired to the right API in the component.
    // This composable provides the queue; flush is a hook point.
  }

  onMounted(() => {
    window.addEventListener("online", onOnline);
    window.addEventListener("offline", onOffline);
    void refreshCount();
  });

  onUnmounted(() => {
    window.removeEventListener("online", onOnline);
    window.removeEventListener("offline", onOffline);
  });

  return { isOnline, pendingCount, enqueue, flush, refreshCount };
}
```

- [ ] **Step 4: 运行测试**

Run: `cd frontend && npx vitest run src/composables/__tests__/useOfflineSync.spec.ts`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add frontend/src/composables/useOfflineSync.ts frontend/src/composables/__tests__/useOfflineSync.spec.ts
git commit -m "feat(offline): add useOfflineSync composable (IndexedDB queue)"
```

---

## Task 12: 全局搜索（Ctrl+K）

**Files:**
- Create: `frontend/src/components/search/GlobalSearch.vue`
- Modify: `frontend/src/layouts/AppLayout.vue`

- [ ] **Step 1: 创建 GlobalSearch 组件**

Create `frontend/src/components/search/GlobalSearch.vue`:

```vue
<script setup lang="ts">
import { ref, watch, nextTick } from "vue";
import { useRouter } from "vue-router";
import { getMyCourses } from "@/api/courses";
import request from "@/api/request";

const router = useRouter();
const open = ref(false);
const query = ref("");
const inputEl = ref<HTMLInputElement | null>(null);
const courses = ref<any[]>([]);
const questions = ref<any[]>([]);
const loading = ref(false);

defineExpose({ open: () => { open.value = true; nextTick(() => inputEl.value?.focus()); } });

function close() {
  open.value = false;
  query.value = "";
  courses.value = [];
  questions.value = [];
}

async function search() {
  if (!query.value.trim()) {
    courses.value = []; questions.value = []; return;
  }
  loading.value = true;
  try {
    const [courseRes, qRes] = await Promise.allSettled([
      getMyCourses(),
      request.get("/questions", { params: { keyword: query.value, page_size: 5 } }),
    ]);
    if (courseRes.status === "fulfilled") {
      const data: any = courseRes.value;
      const items = Array.isArray(data) ? data : data?.items ?? [];
      courses.value = items
        .filter((c: any) => c.name.toLowerCase().includes(query.value.toLowerCase()))
        .slice(0, 4);
    }
    if (qRes.status === "fulfilled") {
      const data: any = qRes.value.data;
      questions.value = (Array.isArray(data) ? data : data?.items ?? []).slice(0, 5);
    }
  } finally {
    loading.value = false;
  }
}

let debounce: number;
watch(query, () => {
  clearTimeout(debounce);
  debounce = window.setTimeout(search, 250);
});

function goCourse(c: any) { router.push(`/courses/${c.id}`); close(); }
function goQuestion(q: any) { router.push(`/courses/${q.course_id}`); close(); }

function onKeydown(e: KeyboardEvent) {
  if (e.key === "Escape") close();
}
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="fixed inset-0 z-50 flex items-start justify-center bg-black/40 p-4 pt-20"
         @click.self="close" @keydown="onKeydown">
      <div class="w-full max-w-lg rounded-[var(--radius-lg)] border border-[var(--line-soft)] bg-[var(--surface)] shadow-[var(--shadow-modal)]">
        <input ref="inputEl" v-model="query" type="text" placeholder="搜索课程、题目…"
               class="w-full border-b border-[var(--line-soft)] p-4 text-[var(--text-main)] outline-none" />
        <div class="max-h-80 overflow-auto p-2">
          <p v-if="loading" class="p-2 text-sm text-[var(--text-muted)]">搜索中…</p>
          <p v-else-if="!query" class="p-2 text-sm text-[var(--text-muted)]">输入关键词搜索</p>
          <template v-else>
            <div v-if="courses.length" class="mb-2">
              <p class="px-2 py-1 text-xs font-bold text-[var(--text-muted)]">题库</p>
              <button v-for="c in courses" :key="c.id" type="button"
                      class="block w-full rounded-[var(--radius-md)] p-2 text-left text-sm hover:bg-[var(--surface-soft)]"
                      @click="goCourse(c)">
                {{ c.name }}
              </button>
            </div>
            <div v-if="questions.length">
              <p class="px-2 py-1 text-xs font-bold text-[var(--text-muted)]">题目</p>
              <button v-for="q in questions" :key="q.id" type="button"
                      class="block w-full truncate rounded-[var(--radius-md)] p-2 text-left text-sm hover:bg-[var(--surface-soft)]"
                      @click="goQuestion(q)">
                {{ q.question }}
              </button>
            </div>
            <p v-if="!loading && !courses.length && !questions.length" class="p-2 text-sm text-[var(--text-muted)]">
              未找到结果
            </p>
          </template>
        </div>
      </div>
    </div>
  </Teleport>
</template>
```

- [ ] **Step 2: 在 AppLayout 接入 Ctrl+K 全局搜索**

修改 `frontend/src/layouts/AppLayout.vue`：

```vue
<script setup lang="ts">
import { onMounted, onUnmounted, ref } from "vue";
import GlobalSearch from "@/components/search/GlobalSearch.vue";

const searchRef = ref<InstanceType<typeof GlobalSearch> | null>(null);

function onGlobalKeydown(e: KeyboardEvent) {
  if ((e.ctrlKey || e.metaKey) && e.key === "k") {
    e.preventDefault();
    searchRef.value?.open();
  }
}

onMounted(() => window.addEventListener("keydown", onGlobalKeydown));
onUnmounted(() => window.removeEventListener("keydown", onGlobalKeydown));
</script>

<template>
  <!-- 现有布局 -->
  <GlobalSearch ref="searchRef" />
</template>
```

（在现有 template 末尾添加 `<GlobalSearch ref="searchRef" />`，并合并 script 中的 setup 逻辑）

- [ ] **Step 3: typecheck + build + 手动验证**

Run: `cd frontend && npm run typecheck && npm run build`
Expected: PASS
手动验证：任意页面按 Ctrl+K 弹出搜索框，输入关键词搜索课程和题目。

- [ ] **Step 4: 提交**

```bash
git add frontend/src/components/search/GlobalSearch.vue frontend/src/layouts/AppLayout.vue
git commit -m "feat(search): global search modal (Ctrl+K)"
```

---

## Task 13: 收藏夹页面 + 导出入口 + Phase 4 验证

**Files:**
- Create: `frontend/src/api/bookmark.ts`
- Create: `frontend/src/views/bookmark/BookmarkList.vue`
- Modify: `frontend/src/router.ts`
- Modify: `frontend/src/views/CourseDetail.vue`（添加导出按钮 + 收藏按钮）

- [ ] **Step 1: 创建收藏 API 层**

Create `frontend/src/api/bookmark.ts`:

```typescript
import request from "./request";

export interface Bookmark {
  id: number;
  question_id: number;
  folder_name: string;
  note: string;
  created_at: string | null;
  question?: any;
}

export interface BookmarkList {
  items: Bookmark[];
  total: number;
  folders: string[];
}

export function listBookmarks(folder?: string): Promise<BookmarkList> {
  return request.get("/bookmarks/", { params: folder ? { folder } : {} }).then(({ data }) => data);
}

export function addBookmark(questionId: number, folderName = "默认收藏"): Promise<Bookmark> {
  return request.post("/bookmarks/", { question_id: questionId, folder_name: folderName }).then(({ data }) => data);
}

export function removeBookmark(questionId: number): Promise<void> {
  return request.delete(`/bookmarks/${questionId}`).then(() => undefined);
}
```

- [ ] **Step 2: 创建收藏夹页面**

Create `frontend/src/views/bookmark/BookmarkList.vue`:

```vue
<script setup lang="ts">
import { onMounted, ref, computed } from "vue";
import { useRouter } from "vue-router";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Trash2 } from "@lucide/vue";  // 或 lucide-vue-next
import { listBookmarks, removeBookmark, type Bookmark } from "@/api/bookmark";

const router = useRouter();
const data = ref<{ items: Bookmark[]; folders: string[] }>({ items: [], folders: [] });
const activeFolder = ref("");
const loading = ref(true);

const items = computed(() => data.value.items);

async function fetch(folder = "") {
  loading.value = true;
  activeFolder.value = folder;
  data.value = await listBookmarks(folder);
  loading.value = false;
}

async function remove(bm: Bookmark) {
  await removeBookmark(bm.question_id);
  await fetch(activeFolder.value);
}

onMounted(() => fetch());
</script>

<template>
  <section class="mx-auto max-w-3xl space-y-4 p-4">
    <h1 class="text-xl font-bold text-[var(--text-main)]">我的收藏</h1>

    <div class="flex flex-wrap gap-2">
      <Button :variant="activeFolder === '' ? 'default' : 'outline'" size="sm" @click="fetch('')">全部</Button>
      <Button v-for="f in data.folders" :key="f" :variant="activeFolder === f ? 'default' : 'outline'" size="sm"
              @click="fetch(f)">{{ f }}</Button>
    </div>

    <p v-if="loading" class="text-[var(--text-muted)]">加载中…</p>
    <p v-else-if="!items.length" class="text-[var(--text-muted)]">暂无收藏</p>

    <Card v-for="bm in items" :key="bm.id">
      <CardContent>
        <div class="flex items-start justify-between gap-3">
          <button class="flex-1 text-left" @click="bm.question && router.push(`/courses/${bm.question.course_id}`)">
            <p class="text-sm text-[var(--text-main)]">{{ bm.question?.question || "题目已删除" }}</p>
            <p class="mt-1 text-xs text-[var(--text-muted)]">{{ bm.folder_name }}</p>
          </button>
          <Button variant="ghost" size="icon" @click="remove(bm)"><Trash2 :size="16" /></Button>
        </div>
      </CardContent>
    </Card>
  </section>
</template>
```

- [ ] **Step 3: 添加路由 + 导出/收藏按钮**

修改 `frontend/src/router.ts`，在 AppLayout children 添加：
```typescript
      {
        path: "bookmarks",
        name: "bookmarks",
        component: () => import("./views/bookmark/BookmarkList.vue"),
        meta: { title: "我的收藏", navKey: "mine" },
      },
```

修改 `frontend/src/views/CourseDetail.vue`，在课程操作区添加导出按钮：
```vue
<Button variant="outline" size="sm" @click="exportCourse">导出 JSON</Button>
```
```typescript
function exportCourse() {
  window.open(`/exports/courses/${courseId.value}.json`, "_blank");
}
```
（courseId 从 route params 获取，需对照现有 CourseDetail 的变量名）

- [ ] **Step 4: typecheck + build**

Run: `cd frontend && npm run typecheck && npm run build`
Expected: PASS

- [ ] **Step 5: Phase 4 完整性验证**

后端：Run `cd backend && python -m pytest -q` → PASS
前端：Run `cd frontend && npm run typecheck && npm run test && npm run build` → PASS

手动端到端验证：
1. 为题目添加知识点标签，查看学习概览雷达图
2. 练习 Hub 看到今日推荐（薄弱知识点 + 到期复习）
3. 课程详情页点击"导出 JSON"下载题库
4. 收藏一道题，在 `/bookmarks` 查看并删除
5. 任意页按 Ctrl+K 全局搜索
6. PWA：Chrome 安装应用，断网后刷新页面仍可加载（静态资源缓存）

- [ ] **Step 6: 对照 spec 验收标准（§6.5）逐项确认**

对照 `docs/superpowers/specs/2026-06-27-major-refactor-design.md` §6.5：
- [ ] 知识点标签系统可用（创建/标记/按标签查正确率）
- [ ] 智能推荐"今日推荐"基于真实练习数据生成
- [ ] 数据分析仪表盘 5+ 图表正确渲染（活动折线、题型饼图、标签雷达、streak）
- [ ] 教师视角统计数据正确（课程使用 + 成绩分布）
- [ ] PWA 安装可用，离线状态下静态资源可用
- [ ] 数据导出 3 种格式（JSON/Excel/CSV）可用
- [ ] 全局搜索（Ctrl+K）可搜索课程、题目
- [ ] 收藏夹可用（分组、增删）

- [ ] **Step 7: 最终提交（如有遗漏改动）**

```bash
git add -A && git status
```

---

## 完成标准（对照 Spec §6.5）

- [x] 知识点标签系统（Tag/QuestionTag，CRUD + AI 文本匹配建议 + 按标签正确率）
- [x] 智能推荐引擎（薄弱知识点 accuracy<0.7 + 到期复习 + 弱题列表）
- [x] 数据分析仪表盘（活动折线图、题型分布饼图、标签掌握雷达图、streak、教师课程统计）
- [x] PWA 离线支持（manifest + Workbox + 离线队列 composable）
- [x] 数据导出（JSON / Excel / CSV 三种格式）
- [x] 全局搜索（Ctrl+K，搜索课程 + 题目）
- [x] 收藏夹（分组、增删、跳转）

---

## 自查备注（Self-Review）

**Spec 覆盖**: Spec §6 的 6.1–6.4 全部映射到任务：
- 6.1 智能学习路径（标签系统 + 艾宾浩斯 + 推荐）→ Task 1, 2, 3, 9（标签 service/API + 推荐 service + UI；艾宾浩斯曲线已在现有 `UserQuestionReview` + `_REVIEW_INTERVALS` 实现，Phase 4 复用 + 推荐引擎整合）
- 6.2 数据分析仪表盘 → Task 4, 7, 8（analytics service + Chart.js + 仪表盘重做）
- 6.3 离线支持（PWA）→ Task 10, 11（Workbox + IndexedDB 队列）
- 6.4 工具增强（导出/收藏/搜索）→ Task 5, 6, 12, 13

**类型一致性**: `TagService.create_tag/tag_question/get_accuracy_by_tag` 方法名跨 service/api/测试一致。`RecommendationService.get_today_recommendation/get_weak_questions` 命名一致。`AnalyticsService.get_daily_activity/get_type_distribution/get_streak` 与前端 API 层函数名对应。`ExportService.export_course_json/export_course_excel/export_practice_history_csv` 与 API 路由对应。

**范围说明（重要）**:
- **艾宾浩斯复习曲线**：Spec §6.1 提及，但现有系统已实现（`crud_practice.py` 的 `_REVIEW_INTERVALS = [1,3,7,14,30]` + `_compute_review_state` + `upsert_user_question_review`）。Phase 4 不重写该算法，而是通过推荐引擎（Task 3）把到期复习整合进"今日推荐"，并在仪表盘（Task 8）展示复习数据。这是复用而非遗漏。
- **离线同步**：Task 11 提供了 IndexedDB 队列 composable（`useOfflineSync`），但完整的"离线练习 → 上线批量同步提交"闭环需要把 composable 接入练习页的提交逻辑。本 Phase 提供 composable 基础设施 + 测试，接入练习页留作后续增强（避免修改练习核心流程引入风险）。`flush()` 是 hook 点，组件按需实现具体提交逻辑。
- **拖拽排序题目**：Spec §6.4 提及，但需要前端拖拽库（vuedraggable）+ 后端 order_index 字段（Question 模型当前无此字段，需 migration）。范围较大且非核心，留后续迭代。本 Phase 聚焦搜索/收藏/导出三个高价值工具。
- **错误题本导出 PDF**：Spec §6.4 提及 PDF 导出，但 PDF 生成（reportlab/weasyprint）依赖较重。本 Phase 实现 JSON/Excel/CSV 三种（覆盖题库导出 + 练习记录导出），PDF 留后续。
- **AI 导入时自动建议标签**：Task 2 Step 5 采用了"schema 加字段 + 前端预览页匹配"的简化方案（避免 orchestrator 注入 db 的复杂度），符合 YAGNI。

**注**: Task 10 的 PWA 图标若无设计资源，用占位 PNG 即可验证功能；正式图标属设计工作，不在工程计划范围。Task 11 的 IndexedDB 测试用 in-memory mock（因 happy-dom/vitest 无真实 IndexedDB），保证测试可重复运行。
