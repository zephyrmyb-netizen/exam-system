# Phase 1 — 代码质量革命 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 消灭技术债务，建立可维护的代码基座 —— 拆分巨石文件、提取通用 CRUD、引入 Pinia、补全测试，全程不改变面向用户的功能行为。

**Architecture:** 渐进式重构。后端先拆 God Service + 提取 GenericCRUD 基类并迁移现有 CRUD；前端引入 Tailwind 占位 + Pinia stores，将路由改为懒加载，拆分三个巨石组件。每一步用现有 300+ 后端测试 + 前端测试作为回归保护网。

**Tech Stack:** FastAPI / SQLAlchemy 2.0 / pytest / structlog / pydantic-settings（后端）；Vue 3 / TypeScript / Vite 6 / Vitest / Pinia（前端）。

**Spec:** `docs/superpowers/specs/2026-06-27-major-refactor-design.md` §3

---

## 文件结构总览

### 后端新增 / 修改

| 文件 | 责任 | 操作 |
|---|---|---|
| `backend/crud_base.py` | `GenericCRUD` 泛型基类 + `PaginatedResult` | 新建 |
| `backend/services/imports/file_parser.py` | 文件读取 + docx/pptx 解析 | 新建（从 imports_service 迁移） |
| `backend/services/imports/ai_extractor.py` | AI 提取逻辑 | 新建（从 imports_service 迁移） |
| `backend/services/imports/import_validator.py` | 题目格式验证 + 去重 | 新建（从 imports_service 迁移） |
| `backend/services/imports/import_orchestrator.py` | 导入流程编排 | 新建（从 imports_service 迁移） |
| `backend/services/imports/__init__.py` | 重新导出，保持外部 API 不变 | 新建 |
| `backend/services/imports_service.py` | **删除**（被 imports/ 包取代） | 删除 |
| `backend/config.py` | Pydantic Settings 化 | 修改 |
| `backend/logging_config.py` | structlog 配置 | 新建 |
| `backend/middleware/request_id.py` | request-id 中间件 | 新建 |
| `backend/crud_courses.py` / `crud_questions.py` | 用 `GenericCRUD` 重写 paginate | 修改 |

### 前端新增 / 修改

| 文件 | 责任 | 操作 |
|---|---|---|
| `frontend/src/stores/auth.ts` | Pinia 化（替代裸模块） | 修改 |
| `frontend/src/stores/import.ts` | Pinia 化（替代 aiImportTask.ts） | 新建 |
| `frontend/src/stores/notification.ts` | 全局通知 store | 新建 |
| `frontend/src/stores/aiImportTask.ts` | **删除** | 删除 |
| `frontend/src/router.ts` | 全部路由懒加载 | 修改 |
| `frontend/src/components/import/ImportFileUpload.vue` 等 5 个 | 拆分自 ImportQuestions | 新建 |
| `frontend/src/components/course/CourseQuestionList.vue` 等 2 个 | 拆分自 CourseDetail | 新建 |
| `frontend/src/components/practice/DailyStatsCard.vue` 等 2 个 | 拆分自 PracticeHub | 新建 |
| `frontend/src/views/ImportQuestions.vue` / `CourseDetail.vue` / `PracticeHub.vue` | 改为组合子组件 | 修改 |
| `frontend/src/styles/base.css` / `transitions.css` / `utilities.css` | CSS 拆分骨架 | 新建 |
| `.github/workflows/ci.yml` | 启用前端 vitest | 修改 |

---

## 执行顺序

任务按依赖关系排序，分 4 个里程碑（M1–M4）。每个里程碑结束都是可提交、可测试的状态。

- **M1（后端基石）**: Task 1–4 — GenericCRUD 基类 + 迁移
- **M2（后端拆分）**: Task 5–8 — God Service 拆分 + 日志/中间件
- **M3（前端基石）**: Task 9–12 — Pinia + 路由懒加载 + CSS 拆分
- **M4（前端拆分 + CI）**: Task 13–17 — 巨石组件拆分 + CI 测试

---

# 里程碑 M1：后端 — GenericCRUD 基类

## Task 1: 创建 GenericCRUD 基类与 PaginatedResult

**Files:**
- Create: `backend/crud_base.py`
- Test: `backend/tests/test_crud_base.py`

- [ ] **Step 1: 写失败测试**

Create `backend/tests/test_crud_base.py`:

```python
from typing import Optional

from sqlalchemy.orm import Session

from backend.crud_base import GenericCRUD, PaginatedResult
from backend import models, schemas


class TestPaginatedResult:
    def test_constructs_with_items_and_total(self):
        result = PaginatedResult(items=[1, 2, 3], total=10, page=1, page_size=3)
        assert result.items == [1, 2, 3]
        assert result.total == 10
        assert result.page == 1
        assert result.page_size == 3

    def test_total_pages_rounds_up(self):
        result = PaginatedResult(items=[1], total=10, page=4, page_size=3)
        assert result.total_pages == 4  # ceil(10/3) = 4

    def test_total_pages_zero_when_no_items(self):
        result = PaginatedResult(items=[], total=0, page=1, page_size=20)
        assert result.total_pages == 0

    def test_has_next_and_has_prev(self):
        r1 = PaginatedResult(items=[1], total=10, page=1, page_size=3)
        assert r1.has_next is True
        assert r1.has_prev is False
        r2 = PaginatedResult(items=[1], total=10, page=4, page_size=3)
        assert r2.has_next is False
        assert r2.has_prev is True


class TestGenericCRUD:
    def test_get_by_id_returns_model_instance(self, db_session: Session, sample_bank):
        repo = GenericCRUD(models.QuestionBank, schemas.CourseCreate, schemas.CourseUpdate)
        result = repo.get_by_id(db_session, sample_bank.id)
        assert result is not None
        assert result.id == sample_bank.id

    def test_get_by_id_returns_none_when_missing(self, db_session: Session):
        repo = GenericCRUD(models.QuestionBank, schemas.CourseCreate, schemas.CourseUpdate)
        assert repo.get_by_id(db_session, 999999) is None

    def test_paginate_applies_offset_and_limit(self, db_session: Session, many_banks):
        repo = GenericCRUD(models.QuestionBank, schemas.CourseCreate, schemas.CourseUpdate)
        result = repo.paginate(db_session, page=1, page_size=2)
        assert len(result.items) == 2
        assert result.total == len(many_banks)

    def test_paginate_page_zero_returns_all(self, db_session: Session, many_banks):
        repo = GenericCRUD(models.QuestionBank, schemas.CourseCreate, schemas.CourseUpdate)
        result = repo.paginate(db_session, page=0, page_size=0)
        assert len(result.items) == len(many_banks)
```

- [ ] **Step 2: 检查测试用的 fixture 是否存在**

Run: `grep -n "sample_bank\|many_banks\|db_session" backend/tests/conftest.py`

如果 `sample_bank` / `many_banks` fixture 不存在，在 `backend/tests/conftest.py` 中添加（见 Step 3）。如果已存在 `db_session`，跳过其定义。

- [ ] **Step 3: 补充缺失的 fixture（若需要）**

在 `backend/tests/conftest.py` 中添加（若 grep 未找到）：

```python
@pytest.fixture
def sample_bank(db_session):
    from backend.models import QuestionBank
    from datetime import datetime, timezone
    bank = QuestionBank(
        owner_id=1,
        name="测试题库",
        visibility="private",
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(bank)
    db_session.commit()
    db_session.refresh(bank)
    return bank


@pytest.fixture
def many_banks(db_session):
    from backend.models import QuestionBank
    from datetime import datetime, timezone
    banks = []
    for i in range(5):
        b = QuestionBank(
            owner_id=1,
            name=f"题库 {i}",
            visibility="private",
            created_at=datetime.now(timezone.utc),
        )
        db_session.add(b)
        banks.append(b)
    db_session.commit()
    for b in banks:
        db_session.refresh(b)
    return banks
```

注意：`owner_id=1` 假设 conftest 中已有 user fixture 创建了 id=1 的用户；若 user fixture 的 id 不同，需先在 fixture 内创建 user。运行测试时若报外键错误，参考现有测试中如何构造 QuestionBank（grep `QuestionBank(` backend/tests）。

- [ ] **Step 4: 运行测试确认失败**

Run: `cd backend && python -m pytest tests/test_crud_base.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'backend.crud_base'`

- [ ] **Step 5: 实现 crud_base.py**

Create `backend/crud_base.py`:

```python
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Generic, Optional, Type, TypeVar

from sqlalchemy.orm import Session

ModelType = TypeVar("ModelType")
CreateSchema = TypeVar("CreateSchema")
UpdateSchema = TypeVar("UpdateSchema")


@dataclass
class PaginatedResult:
    """Generic paginated list result."""
    items: list[Any]
    total: int
    page: int
    page_size: int

    @property
    def total_pages(self) -> int:
        if self.page_size <= 0:
            return 0 if self.total == 0 else 1
        return math.ceil(self.total / self.page_size)

    @property
    def has_next(self) -> bool:
        return self.page < self.total_pages

    @property
    def has_prev(self) -> bool:
        return self.page > 1


class GenericCRUD(Generic[ModelType, CreateSchema, UpdateSchema]):
    """Reusable CRUD base. Subclasses add entity-specific queries."""

    def __init__(self, model: Type[ModelType]):
        self.model = model

    def get_by_id(self, db: Session, id: int) -> Optional[ModelType]:
        return db.query(self.model).filter(self.model.id == id).first()

    def get_list(
        self, db: Session, *, skip: int = 0, limit: int = 0,
    ) -> list[ModelType]:
        query = db.query(self.model)
        if skip:
            query = query.offset(skip)
        if limit:
            query = query.limit(limit)
        return query.all()

    def paginate(
        self, db: Session, *, page: int = 0, page_size: int = 0,
    ) -> PaginatedResult:
        query = db.query(self.model)
        total = query.count()
        if page > 0 and page_size > 0:
            offset = (page - 1) * page_size
            query = query.offset(offset).limit(page_size)
        return PaginatedResult(items=query.all(), total=total, page=page, page_size=page_size)

    def delete(self, db: Session, id: int) -> bool:
        obj = self.get_by_id(db, id)
        if obj is None:
            return False
        db.delete(obj)
        db.commit()
        return True
```

- [ ] **Step 6: 运行测试确认通过**

Run: `cd backend && python -m pytest tests/test_crud_base.py -v`
Expected: PASS（全部 8 个测试）

- [ ] **Step 7: 运行全量后端测试确认无回归**

Run: `cd backend && python -m pytest -q`
Expected: PASS（所有现有测试 + 新测试）

- [ ] **Step 8: 提交**

```bash
git add backend/crud_base.py backend/tests/test_crud_base.py backend/tests/conftest.py
git commit -m "refactor: add GenericCRUD base class and PaginatedResult"
```

---

## Task 2: 用 GenericCRUD 重构 crud_courses 的分页查询

**Files:**
- Modify: `backend/crud_courses.py:90-117`（`get_question_banks`、`get_my_question_banks`）
- Test: `backend/tests/test_courses.py`（现有，作为回归保护）

- [ ] **Step 1: 先跑现有测试，确认基线通过**

Run: `cd backend && python -m pytest tests/test_courses.py -v`
Expected: PASS — 记录测试数量作为基线

- [ ] **Step 2: 写一个验证分页行为的测试**

在 `backend/tests/test_courses.py` 末尾添加：

```python
def test_get_question_banks_pagination(db_session, many_banks):
    from backend.crud_courses import get_question_banks
    items, total = get_question_banks(db_session, user_id=1, page=1, page_size=2)
    assert total == len(many_banks)
    assert len(items) == 2


def test_get_my_question_banks_pagination(db_session, many_banks):
    from backend.crud_courses import get_my_question_banks
    items, total = get_my_question_banks(db_session, user_id=1, page=1, page_size=2)
    assert total == len(many_banks)
    assert len(items) == 2
```

- [ ] **Step 3: 运行新测试确认通过（重构前）**

Run: `cd backend && python -m pytest tests/test_courses.py::test_get_question_banks_pagination tests/test_courses.py::test_get_my_question_banks_pagination -v`
Expected: PASS — 证明现有实现行为正确

- [ ] **Step 4: 重构 get_question_banks 使用内部 paginate 辅助**

修改 `backend/crud_courses.py`，在文件顶部添加导入，并提取分页辅助函数。将 `get_question_banks` 和 `get_my_question_banks` 中重复的 `page/page_size` 分页逻辑提取为一个模块级辅助：

在 `backend/crud_courses.py` 顶部 `import` 区后添加：

```python
def _apply_pagination(query, page: int, page_size: int):
    """Apply offset/limit pagination to a query, returning (items, total).

    Mirrors the GenericCRUD.paginate convention: page/page_size <= 0
    means "return all rows".
    """
    total = query.count()
    if page > 0 and page_size > 0:
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
    return query.all(), total
```

将 `get_question_banks`（原 90-99 行）替换为：

```python
def get_question_banks(
    db: Session, user_id: int | None, page: int = 0, page_size: int = 0,
) -> tuple[list[models.QuestionBank], int]:
    query = _add_bank_visibility_filter(db.query(models.QuestionBank), user_id)
    query = query.order_by(models.QuestionBank.created_at.desc())
    return _apply_pagination(query, page, page_size)
```

将 `get_my_question_banks`（原 102-117 行）替换为：

```python
def get_my_question_banks(
    db: Session, user_id: int, page: int = 0, page_size: int = 0,
) -> tuple[list[models.QuestionBank], int]:
    from sqlalchemy.orm import selectinload

    query = (
        db.query(models.QuestionBank)
        .filter(models.QuestionBank.owner_id == user_id)
        .options(selectinload(models.QuestionBank.questions))
        .order_by(models.QuestionBank.created_at.desc())
    )
    return _apply_pagination(query, page, page_size)
```

注意顺序调整：原本先 `count()` 后 `order_by()`，重构后先 `order_by()` 后在辅助函数内 `count()`。`count()` 不受 order_by 影响，行为一致。

- [ ] **Step 5: 运行相关测试确认通过**

Run: `cd backend && python -m pytest tests/test_courses.py -v`
Expected: PASS（所有测试，包括新加的 2 个）

- [ ] **Step 6: 运行全量后端测试确认无回归**

Run: `cd backend && python -m pytest -q`
Expected: PASS

- [ ] **Step 7: 提交**

```bash
git add backend/crud_courses.py backend/tests/test_courses.py
git commit -m "refactor: extract pagination helper in crud_courses"
```

---

## Task 3: 重构 crud_questions 和 crud_wrongbook 的分页

**Files:**
- Modify: `backend/crud_questions.py`（分页函数）
- Modify: `backend/crud_wrongbook.py`（分页函数）
- Test: `backend/tests/test_questions.py`、`backend/tests/test_wrongbook.py`（现有回归）

- [ ] **Step 1: 定位重复分页模式**

Run: `grep -n "page > 0 and page_size > 0" backend/crud_questions.py backend/crud_wrongbook.py backend/crud_practice.py`
Expected: 列出所有重复分页块的具体行号

- [ ] **Step 2: 把 _apply_pagination 提升到 crud_common.py**

修改 `backend/crud_common.py`，在文件末尾添加：

```python
def apply_pagination(query, page: int, page_size: int):
    """Apply offset/limit pagination to a SQLAlchemy query.

    Returns (items, total). When page or page_size <= 0, returns all rows.
    """
    total = query.count()
    if page > 0 and page_size > 0:
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
    return query.all(), total
```

- [ ] **Step 3: 修改 crud_courses 改用统一的 apply_pagination**

修改 `backend/crud_courses.py`：删除 Step 4 中添加的本地 `_apply_pagination`，改为从 `crud_common` 导入：

顶部 import 改为：
```python
from .crud_common import _add_bank_visibility_filter, apply_pagination
```

将两个函数体中的 `_apply_pagination(query, page, page_size)` 改为 `apply_pagination(query, page, page_size)`。

删除 `backend/crud_courses.py` 中本地定义的 `_apply_pagination`。

- [ ] **Step 4: 修改 crud_questions.py 使用 apply_pagination**

对 `backend/crud_questions.py` 中每一个含 `page > 0 and page_size > 0` 的函数，用 `apply_pagination` 替换内联分页逻辑。

示例（以 `get_questions` 为模板，按 grep 输出的每个函数逐一替换）：

顶部添加导入（若尚无）：
```python
from .crud_common import apply_pagination
```

将：
```python
    total = query.count()
    query = query.order_by(...)
    if page > 0 and page_size > 0:
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
    return query.all(), total
```

替换为：
```python
    query = query.order_by(...)
    return apply_pagination(query, page, page_size)
```

对每个匹配函数重复。注意保留各自原有的 `.filter()` 和 `.order_by()` 调用，只替换分页块。

- [ ] **Step 5: 修改 crud_wrongbook.py 使用 apply_pagination**

同样处理 `backend/crud_wrongbook.py` 中的分页函数（如 `get_wrong_records`）。

- [ ] **Step 6: 修改 crud_practice.py 使用 apply_pagination**

同样处理 `backend/crud_practice.py` 中的分页函数（如 `get_practice_history`）。

- [ ] **Step 7: 运行全量后端测试**

Run: `cd backend && python -m pytest -q`
Expected: PASS — 若有失败，检查是否漏改了某个函数的 order_by 或 filter

- [ ] **Step 8: 提交**

```bash
git add backend/crud_common.py backend/crud_courses.py backend/crud_questions.py backend/crud_wrongbook.py backend/crud_practice.py
git commit -m "refactor: unify pagination via crud_common.apply_pagination"
```

---

# 里程碑 M2：后端 — 拆分 God Service + 日志现代化

## Task 4: 创建 imports 包并迁移 file_parser

**Files:**
- Create: `backend/services/imports/__init__.py`
- Create: `backend/services/imports/file_parser.py`（从 imports_service.py 迁移）
- Test: `backend/tests/test_imports_file_parser.py`

- [ ] **Step 1: 先确认现有 import 测试基线**

Run: `cd backend && python -m pytest tests/test_imports.py -q`
Expected: PASS — 记录测试数量

- [ ] **Step 2: 写 file_parser 单元测试**

Create `backend/tests/test_imports_file_parser.py`:

```python
import pytest

from backend.services.imports.file_parser import (
    ALLOWED_EXTENSIONS,
    MAX_FILE_SIZE,
    SavedUpload,
    cleanup_temp_file,
    extract_text_from_file,
    extract_text_or_raise,
    validate_upload,
)


class TestValidateUpload:
    def test_accepts_docx(self):
        ext = validate_upload("notes.docx", b"x" * 100)
        assert ext == ".docx"

    def test_accepts_pptx(self):
        ext = validate_upload("slides.pptx", b"x" * 100)
        assert ext == ".pptx"

    def test_rejects_unsupported_extension(self):
        with pytest.raises(Exception):
            validate_upload("file.txt", b"x" * 100)

    def test_rejects_oversized_file(self):
        with pytest.raises(Exception):
            validate_upload("big.docx", b"x" * (MAX_FILE_SIZE + 1))


class TestExtractTextOrRaise:
    def test_returns_text_and_empty_warnings_for_valid_docx(self, tmp_path, sample_docx):
        text, warnings = extract_text_or_raise(str(sample_docx))
        assert isinstance(text, str)
        assert isinstance(warnings, list)
```

（`sample_docx` fixture 若不存在，在 conftest.py 中用 python-docx 生成一个最小 .docx 到 tmp_path。）

- [ ] **Step 3: 运行测试确认失败**

Run: `cd backend && python -m pytest tests/test_imports_file_parser.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 4: 创建包与 file_parser 模块**

Create `backend/services/imports/__init__.py`（先空文件占位，Task 7 补充导出）:

```python
"""AI-powered question import pipeline (split for maintainability).

Public API is re-exported here so callers can keep importing from
``backend.services.imports_service`` — see Task 7.
"""
```

Create `backend/services/imports/file_parser.py`，将 `imports_service.py` 中以下函数及其依赖**原样迁移**（保持函数签名和实现不变，只移动位置）：

从 `imports_service.py` 迁移：
- 常量 `ALLOWED_EXTENSIONS`、`MAX_FILE_SIZE`
- dataclass `SavedUpload`
- `elapsed_ms`、`build_timing`（file_parser 不需要 build_timing，留给 orchestrator —— 但 build_timing 依赖 schemas，放这里会循环依赖；只迁 `elapsed_ms` 如果 file_parser 用到，否则不迁）
- `validate_upload`
- `save_upload_to_temp`
- `cleanup_temp_file`
- `extract_text_and_warnings`
- `_extract_docx`
- `_extract_pptx`
- `extract_text_from_file`
- `extract_text_or_raise`

迁移规则：
- 这些函数只依赖标准库 + python-docx/python-pptx + schemas.ImportTiming（仅 build_timing）
- `build_timing` 依赖 schemas，放在 Task 6 的 orchestrator 里。file_parser 不导出它。
- 把文件读取用到的 `tempfile`、`os`、`Path` import 带过去

- [ ] **Step 5: 运行 file_parser 测试**

Run: `cd backend && python -m pytest tests/test_imports_file_parser.py -v`
Expected: PASS

- [ ] **Step 6: 确认 imports_service.py 仍然可导入（暂时保留重复）**

Run: `cd backend && python -c "from backend.services import imports_service; print('ok')"`
Expected: 输出 `ok`（此时两个地方都有这些函数，稍后 Task 7 统一）

- [ ] **Step 7: 提交**

```bash
git add backend/services/imports/__init__.py backend/services/imports/file_parser.py backend/tests/test_imports_file_parser.py
git commit -m "refactor: extract file_parser module from imports_service"
```

---

## Task 5: 迁移 ai_extractor 模块

**Files:**
- Create: `backend/services/imports/ai_extractor.py`（从 imports_service.py 迁移）
- Test: `backend/tests/test_imports_ai_extractor.py`

- [ ] **Step 1: 写 ai_extractor 单元测试**

Create `backend/tests/test_imports_ai_extractor.py`:

```python
from backend.services.imports.ai_extractor import (
    build_ai_prompt,
    build_ai_repair_prompt,
    deduplicate_questions,
    extract_questions_from_ai_response,
    json_candidates_from_text,
    question_items_from_parsed_json,
    validate_question_item,
)


class TestValidateQuestionItem:
    def test_valid_single_choice(self):
        item = {
            "type": "single_choice",
            "content": "题干",
            "options": ["A", "B", "C", "D"],
            "answer": "A",
        }
        result, error = validate_question_item(item)
        assert error is None
        assert result["type"] == "single_choice"

    def test_missing_type_returns_error(self):
        result, error = validate_question_item({"content": "题干"})
        assert result is None
        assert error is not None


class TestExtractFromAIResponse:
    def test_extracts_from_valid_json(self):
        raw = '{"questions": [{"type": "true_false", "content": "1+1=2", "answer": "对"}]}'
        questions, warnings = extract_questions_from_ai_response(raw)
        assert len(questions) == 1
        assert questions[0]["type"] == "true_false"

    def test_returns_warnings_for_empty(self):
        questions, warnings = extract_questions_from_ai_response("not json at all")
        assert questions == []


class TestDeduplicateQuestions:
    def test_removes_duplicates_by_content(self):
        qs = [
            {"content": "重复题", "type": "single_choice", "answer": "A"},
            {"content": "重复题", "type": "single_choice", "answer": "A"},
            {"content": "不同题", "type": "single_choice", "answer": "B"},
        ]
        result = deduplicate_questions(qs)
        assert len(result) == 2
```

注意：`validate_question_item` 对 single_choice 的具体校验规则（是否要求 options、answer 格式）请先读 `imports_service.py:228-255` 确认实际行为，测试断言与实际行为对齐。如果实现要求 answer 在 options 中，调整测试用例。

- [ ] **Step 2: 运行测试确认失败**

Run: `cd backend && python -m pytest tests/test_imports_ai_extractor.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: 迁移函数到 ai_extractor.py**

从 `imports_service.py` 迁移到 `backend/services/imports/ai_extractor.py`：
- `build_ai_prompt`
- `build_ai_repair_prompt`
- `validate_question_item`
- `question_items_from_parsed_json`
- `json_candidates_from_text`
- `extract_questions_from_ai_response`
- `deduplicate_questions`
- `chunk_document_text`
- 常量 `AI_CHUNK_SIZE`、`MAX_CHUNKS`（如被 `chunk_document_text` 使用）

迁移规则：保持函数体原样。需要的 import 带过去：`re`、`json as json_module`、`Any`、`IMPORT_CHUNK_SIZE`、`IMPORT_MAX_CHUNKS`（from `...config`）、`VALID_QUESTION_TYPES`、`normalize_answer`（from `...utils`）。

注意 `validate_question_item` 若调用了 `normalize_answer`，确保 import 正确。

- [ ] **Step 4: 运行测试**

Run: `cd backend && python -m pytest tests/test_imports_ai_extractor.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add backend/services/imports/ai_extractor.py backend/tests/test_imports_ai_extractor.py
git commit -m "refactor: extract ai_extractor module from imports_service"
```

---

## Task 6: 迁移 AI 客户端调用逻辑 + 创建 orchestrator + validator

**Files:**
- Create: `backend/services/imports/ai_client_calls.py`（AI 调用封装）
- Create: `backend/services/imports/import_validator.py`（验证 + 去重编排）
- Create: `backend/services/imports/import_orchestrator.py`（主编排）
- Test: `backend/tests/test_imports_orchestrator.py`

- [ ] **Step 1: 先确认现有 imports_service 公共 API**

Run: `grep -n "^def \|^async def " backend/services/imports_service.py | grep -v "^.*_"`
Expected: 列出所有顶层公共函数名。这些就是 orchestrator 必须重新导出的 API（供 routers/imports.py 调用）。

记录下 `routers/imports.py` 实际 import 了哪些名字：
Run: `grep -n "imports_service" backend/routers/imports.py`

- [ ] **Step 2: 写 orchestrator 端到端测试（基于文本预览路径）**

Create `backend/tests/test_imports_orchestrator.py`:

```python
import pytest

from backend.services.imports.import_orchestrator import preview_import_from_text


class TestPreviewImportFromText:
    def test_returns_tuple_of_three(self):
        # preview_import_from_text 应返回 (questions, warnings, timing_dict)
        result = preview_import_from_text("not a question")
        assert isinstance(result, tuple)
        assert len(result) == 3
        questions, warnings, timing = result
        assert isinstance(questions, list)
        assert isinstance(warnings, list)
```

注意：`preview_import_from_text` 会调用 AI，测试中需 mock。先读现有 `tests/test_imports.py` 中如何 mock AI（grep `monkeypatch\|_ai_override\|mock` backend/tests/test_imports.py），复用相同的 mock 策略。如果现有测试通过环境变量 `AI_OVERRIDE` 注入假数据，本测试也设置该变量。

- [ ] **Step 3: 迁移 AI 客户端调用函数**

Create `backend/services/imports/ai_client_calls.py`，从 `imports_service.py` 迁移：
- `_build_import_client`
- `safe_ai_error_detail`
- `call_ai_parse_chunk`
- `call_ai_parse`
- 相关异常 import（`APIConnectionError`、`APIStatusError`、`OpenAI`、`APITimeoutError`）

需要的 config import：`IMPORT_UPSTREAM_TIMEOUT`、`OPENAI_API_KEY`、`OPENAI_BASE_URL`、`OPENAI_MODEL`。

- [ ] **Step 4: 迁移 validator**

Create `backend/services/imports/import_validator.py`，从 `imports_service.py` 迁移：
- `ensure_questions_found`
- `validate_imported_questions`

这两个函数依赖 `validate_question_item`（已在 ai_extractor），import from `.ai_extractor`。

- [ ] **Step 5: 创建 orchestrator**

Create `backend/services/imports/import_orchestrator.py`，从 `imports_service.py` 迁移剩余的编排函数：
- `build_timing`（依赖 schemas.ImportTiming）
- `resolve_target_course`
- `persist_imported_questions`
- `preview_import_from_text`
- `_ai_override_active`

从同包导入：
```python
from .file_parser import extract_text_or_raise, SavedUpload, validate_upload, save_upload_to_temp, cleanup_temp_file, extract_text_from_file, elapsed_ms
from .ai_extractor import build_ai_prompt, chunk_document_text, deduplicate_questions, extract_questions_from_ai_response, validate_question_item, question_items_from_parsed_json
from .ai_client_calls import call_ai_parse, call_ai_parse_chunk, _build_import_client, safe_ai_error_detail
from .import_validator import ensure_questions_found, validate_imported_questions
```

需要的外部依赖：`crud`、`schemas`、`models.Question`、`utils`、各 config 值、`derive_course_name_from_filename`。

- [ ] **Step 6: 运行 orchestrator 测试**

Run: `cd backend && python -m pytest tests/test_imports_orchestrator.py -v`
Expected: PASS

- [ ] **Step 7: 提交（此时 imports_service.py 仍存在，新旧并存）**

```bash
git add backend/services/imports/ai_client_calls.py backend/services/imports/import_validator.py backend/services/imports/import_orchestrator.py backend/tests/test_imports_orchestrator.py
git commit -m "refactor: extract import orchestrator, validator, ai client calls"
```

---

## Task 7: 统一包导出，删除 imports_service.py

**Files:**
- Modify: `backend/services/imports/__init__.py`
- Delete: `backend/services/imports_service.py`
- Modify: `backend/routers/imports.py`（若 import 路径变化）
- Test: `backend/tests/test_imports.py`（现有，回归）

- [ ] **Step 1: 在 __init__.py 中重新导出所有公共 API**

修改 `backend/services/imports/__init__.py`，从各子模块重新导出 `routers/imports.py` 用到的所有名字：

```python
"""AI-powered question import pipeline.

Split for maintainability; public API preserved for callers that import
from ``backend.services.imports_service`` via the shim below.
"""
from .file_parser import (
    ALLOWED_EXTENSIONS,
    MAX_FILE_SIZE,
    SavedUpload,
    cleanup_temp_file,
    elapsed_ms,
    extract_text_from_file,
    extract_text_or_raise,
    extract_text_and_warnings,
    save_upload_to_temp,
    validate_upload,
)
from .ai_extractor import (
    AI_CHUNK_SIZE,
    MAX_CHUNKS,
    build_ai_prompt,
    build_ai_repair_prompt,
    chunk_document_text,
    deduplicate_questions,
    extract_questions_from_ai_response,
    json_candidates_from_text,
    question_items_from_parsed_json,
    validate_question_item,
)
from .ai_client_calls import (
    call_ai_parse,
    call_ai_parse_chunk,
    safe_ai_error_detail,
)
from .import_validator import (
    ensure_questions_found,
    validate_imported_questions,
)
from .import_orchestrator import (
    build_timing,
    persist_imported_questions,
    preview_import_from_text,
    resolve_target_course,
)

__all__ = [
    # ... 列出上面所有名字
]
```

**重要**：先运行 Step 1 的 grep 结果对照，确保 `routers/imports.py` import 的每个名字都在 `__all__` 中。

- [ ] **Step 2: 创建兼容 shim（保持 routers 不用改）**

为避免改动所有调用方，创建 `backend/services/imports_service.py` 作为薄 shim：

```python
"""Backward-compatible shim. Real implementation lives in the ``imports``
package. This file re-exports everything so existing
``from backend.services.imports_service import X`` keeps working.
"""
from .imports import *  # noqa: F401,F403
from .imports import __all__  # noqa: F401
```

- [ ] **Step 3: 运行全量 import 测试**

Run: `cd backend && python -m pytest tests/test_imports.py -v`
Expected: PASS（所有现有 import 测试通过，证明 shim 工作正常）

- [ ] **Step 4: 运行全量后端测试**

Run: `cd backend && python -m pytest -q`
Expected: PASS（300+ 测试全部通过）

- [ ] **Step 5: 提交**

```bash
git add backend/services/imports/__init__.py backend/services/imports_service.py
git commit -m "refactor: unify imports package exports via backward-compat shim"
```

---

## Task 8: 配置 Pydantic Settings + structlog + request-id 中间件

**Files:**
- Modify: `backend/config.py`
- Create: `backend/logging_config.py`
- Create: `backend/middleware/__init__.py`
- Create: `backend/middleware/request_id.py`
- Modify: `backend/main.py`
- Modify: `backend/requirements.txt`
- Test: `backend/tests/test_config.py`（现有，回归）、`backend/tests/test_logging.py`（新）

- [ ] **Step 1: 添加依赖**

修改 `backend/requirements.txt`，添加：
```
pydantic-settings>=2.6.0
structlog>=24.4.0
```

- [ ] **Step 2: 安装新依赖**

Run: `cd backend && pip install pydantic-settings structlog`

- [ ] **Step 3: 先跑现有 config 测试，确认基线**

Run: `cd backend && python -m pytest tests/test_config.py -v`
Expected: PASS — 记录基线

- [ ] **Step 4: 写日志配置测试**

Create `backend/tests/test_logging.py`:

```python
import logging

from backend.logging_config import configure_logging


def test_configure_logging_returns_logger():
    logger = configure_logging()
    assert isinstance(logger, logging.Logger)


def test_configure_logging_is_idempotent():
    logger1 = configure_logging()
    logger2 = configure_logging()
    assert logger1.name == logger2.name == "xuexibao"
```

- [ ] **Step 5: 运行测试确认失败**

Run: `cd backend && python -m pytest tests/test_logging.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 6: 实现 logging_config.py**

Create `backend/logging_config.py`:

```python
"""Structured logging configuration using structlog.

Renders JSON in production, pretty console output in development.
"""
import logging
import sys

import structlog

from .config import IS_PRODUCTION


def configure_logging() -> logging.Logger:
    """Configure structlog once and return the app logger."""
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if IS_PRODUCTION:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer(colors=True))

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Bridge stdlib logging into structlog
    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stdout,
        format="%(message)s",
    )

    return structlog.get_logger("xuexibao")
```

- [ ] **Step 7: 运行日志测试**

Run: `cd backend && python -m pytest tests/test_logging.py -v`
Expected: PASS

- [ ] **Step 8: 创建 request-id 中间件**

Create `backend/middleware/__init__.py`（空文件）.

Create `backend/middleware/request_id.py`:

```python
"""Middleware that assigns a unique request id to every request and binds
it to the structlog contextvars so all log lines for a request share it.
"""
import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)
        try:
            response: Response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            structlog.contextvars.clear_contextvars()
```

- [ ] **Step 9: 在 main.py 中接入中间件和日志**

修改 `backend/main.py`：

1. 顶部 import 区添加：
```python
from .logging_config import configure_logging
from .middleware.request_id import RequestIdMiddleware
```

2. 替换 `logger = logging.getLogger("xuexibao")` 为：
```python
logger = configure_logging()
```
（删除原 `import logging` 若不再需要）

3. 在 `app = FastAPI(...)` 之后、CORS 中间件之前添加：
```python
app.add_middleware(RequestIdMiddleware)
```

- [ ] **Step 10: config.py 改用 Pydantic Settings（谨慎，保持外部属性名不变）**

⚠️ 这是高风险改动。`config.py` 被 database.py、main.py、所有 router 依赖。Pydantic Settings 化必须保持所有现有模块级常量名（`DATABASE_URL`、`SECRET_KEY`、`IS_PRODUCTION` 等）完全不变。

修改 `backend/config.py`：保留现有的 dotenv 加载逻辑和所有模块级常量定义**不变**（它们已被大量代码 import），在文件末尾**额外**添加一个 Pydantic Settings 类，供后续新代码使用类型安全配置：

```python
# ── Typed settings (new code should prefer this) ─────────────────────────────
try:
    from pydantic_settings import BaseSettings, SettingsConfigDict

    class Settings(BaseSettings):
        """Typed, validated settings. Existing module-level constants above
        remain the source of truth for now; this provides type-safe access
        for new code without forcing a full migration."""

        model_config = SettingsConfigDict(env_file=".env", extra="ignore")

        app_env: str = APP_ENV
        database_url: str = DATABASE_URL
        secret_key: str = SECRET_KEY
        algorithm: str = ALGORITHM
        access_token_expire_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES
        invite_code: str = INVITE_CODE
        openai_api_key: str = OPENAI_API_KEY
        openai_base_url: str = OPENAI_BASE_URL
        openai_model: str = OPENAI_MODEL
        redis_url: str = REDIS_URL

    settings = Settings()
except ImportError:  # pydantic-settings not installed
    settings = None
```

这样既引入了类型安全配置（新代码用 `settings.secret_key`），又不破坏任何现有 import。完整迁移留待 Phase 2。

- [ ] **Step 11: 运行全量后端测试**

Run: `cd backend && python -m pytest -q`
Expected: PASS

- [ ] **Step 12: 手动冒烟测试启动**

Run: `cd backend && python -c "from backend.main import app; print('app created ok')"`
Expected: 输出 `app created ok`，无异常

- [ ] **Step 13: 提交**

```bash
git add backend/requirements.txt backend/logging_config.py backend/middleware/ backend/main.py backend/config.py backend/tests/test_logging.py
git commit -m "feat: add structlog logging, request-id middleware, typed settings"
```

---

# 里程碑 M3：前端 — Pinia + 路由懒加载 + CSS 骨架

## Task 9: 引入 Pinia 并迁移 auth store

**Files:**
- Modify: `frontend/package.json`
- Modify: `frontend/src/main.ts`
- Modify: `frontend/src/stores/auth.ts`
- Modify: 调用 `useAuth()` 的组件（grep 定位）
- Test: `frontend/src/stores/__tests__/auth.spec.ts`

- [ ] **Step 1: 安装 Pinia**

Run: `cd frontend && npm install pinia@^2.3.0`
（Pinia 2.x 兼容 Vue 3.5；不要装 3.x 以免破坏兼容）

- [ ] **Step 2: 定位所有 useAuth 调用点**

Run: `grep -rn "useAuth" frontend/src --include="*.vue" --include="*.ts"`
记录所有调用文件，迁移后需逐一验证。

- [ ] **Step 3: 写 auth store 测试**

Create `frontend/src/stores/__tests__/auth.spec.ts`:

```typescript
import { setActivePinia, createPinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";

// Mock the request module before importing the store
vi.mock("../../api/request", () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
  getToken: vi.fn(() => ""),
  setToken: vi.fn(),
  clearToken: vi.fn(),
  getErrorMessage: vi.fn((_, fallback) => fallback),
}));

import { useAuthStore } from "../auth";

describe("useAuthStore", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it("starts unauthenticated", () => {
    const auth = useAuthStore();
    expect(auth.isAuthenticated).toBe(false);
    expect(auth.user).toBeNull();
  });

  it("logout clears user", () => {
    const auth = useAuthStore();
    auth.logout();
    expect(auth.user).toBeNull();
  });

  it("resetFeedback clears messages", () => {
    const auth = useAuthStore();
    auth.authError = "err";
    auth.authMessage = "msg";
    auth.resetFeedback();
    expect(auth.authError).toBe("");
    expect(auth.authMessage).toBe("");
  });
});
```

- [ ] **Step 4: 运行测试确认失败**

Run: `cd frontend && npx vitest run src/stores/__tests__/auth.spec.ts`
Expected: FAIL — `useAuthStore` 未导出（当前导出的是 `useAuth` 函数）

- [ ] **Step 5: 在 main.ts 注册 Pinia**

修改 `frontend/src/main.ts`：

```typescript
import { createApp } from "vue";
import { createPinia } from "pinia";
import App from "./App.vue";
import router from "./router";
import i18n from "./i18n";
import "./style.css";

const app = createApp(App);
app.use(createPinia());
app.use(router);
app.use(i18n);
app.mount("#app");
```

- [ ] **Step 6: 将 auth.ts 改写为 Pinia store**

将 `frontend/src/stores/auth.ts` 整体替换为 Pinia 定义式 store，**保持所有外部使用的方法名和响应式属性名不变**（`user`、`loading`、`authMessage`、`authError`、`isAuthenticated`、`fetchProfile`、`login`、`register`、`logout`、`resetFeedback`）：

```typescript
import { computed, ref } from "vue";
import { defineStore } from "pinia";
import request, { clearToken, getErrorMessage, getToken, setToken } from "../api/request";
import type { User, TokenResponse } from "../types";

export const useAuthStore = defineStore("auth", () => {
  const user = ref<User | null>(null);
  const loading = ref<boolean>(false);
  const authMessage = ref<string>("");
  const authError = ref<string>("");
  const isAuthenticated = computed<boolean>(() => !!getToken());

  function normalizeToken(data: TokenResponse | Record<string, unknown> | undefined): string {
    if (!data) return "";
    return (data as Record<string, unknown>)?.access_token as string
      || (data as Record<string, unknown>)?.token as string
      || (data as Record<string, unknown>)?.accessToken as string
      || "";
  }

  function resetFeedback(): void {
    authMessage.value = "";
    authError.value = "";
  }

  async function fetchProfile(): Promise<void> {
    if (!getToken()) {
      user.value = null;
      return;
    }
    loading.value = true;
    resetFeedback();
    try {
      const { data } = await request.get<User>("/auth/me");
      user.value = data;
    } catch (error: unknown) {
      if ((error as { response?: { status?: number } })?.response?.status === 401) {
        user.value = null;
        clearToken();
      }
      authError.value = getErrorMessage(error, "获取用户信息失败");
    } finally {
      loading.value = false;
    }
  }

  async function login(username: string, password: string): Promise<boolean> {
    if (!username.trim() || !password) {
      authError.value = "请填写用户名和密码。";
      return false;
    }
    loading.value = true;
    resetFeedback();
    try {
      const { data } = await request.post<TokenResponse>("/auth/login", {
        username: username.trim(),
        password,
      });
      const token = normalizeToken(data);
      if (!token) throw new Error("登录成功，但未收到 token");
      setToken(token);
      await fetchProfile();
      authMessage.value = "登录成功。";
      return true;
    } catch (error: unknown) {
      authError.value = getErrorMessage(error, "登录失败");
      return false;
    } finally {
      loading.value = false;
    }
  }

  async function register(
    username: string,
    password: string,
    inviteCode: string,
  ): Promise<boolean> {
    if (!username.trim() || !password || !inviteCode.trim()) {
      authError.value = "注册时请填写用户名、密码和邀请码。";
      return false;
    }
    loading.value = true;
    resetFeedback();
    try {
      await request.post("/auth/register", {
        username: username.trim(),
        password,
        invite_code: inviteCode.trim(),
      });
      authMessage.value = "注册成功，请使用新账号登录。";
      return true;
    } catch (error: unknown) {
      authError.value = getErrorMessage(error, "注册失败");
      return false;
    } finally {
      loading.value = false;
    }
  }

  function logout(): void {
    clearToken();
    user.value = null;
    resetFeedback();
    authMessage.value = "已退出登录。";
  }

  return {
    user,
    loading,
    authMessage,
    authError,
    isAuthenticated,
    fetchProfile,
    login,
    register,
    logout,
    resetFeedback,
  };
});
```

- [ ] **Step 7: 运行 store 测试**

Run: `cd frontend && npx vitest run src/stores/__tests__/auth.spec.ts`
Expected: PASS

- [ ] **Step 8: 更新所有调用点**

对 Step 2 找到的每个文件，将：
```typescript
import { useAuth } from "@/stores/auth";  // 或相对路径
const { user, login } = useAuth();
```
改为：
```typescript
import { useAuthStore } from "@/stores/auth";
const auth = useAuthStore();
// 用 auth.user, auth.login(...)
```

Vue 组件中由于 Pinia store 的 ref 会自动解包，模板里直接用 `auth.user`、`auth.login`。

- [ ] **Step 9: 运行前端测试 + typecheck**

Run: `cd frontend && npm run typecheck && npx vitest run`
Expected: PASS

- [ ] **Step 10: 提交**

```bash
git add frontend/package.json frontend/package-lock.json frontend/src/main.ts frontend/src/stores/auth.ts frontend/src/stores/__tests__/auth.spec.ts
# 加上所有改动的调用点组件
git add -A
git commit -m "refactor: migrate auth store to Pinia"
```

---

## Task 10: 迁移 import store 到 Pinia

**Files:**
- Create: `frontend/src/stores/import.ts`
- Delete: `frontend/src/stores/aiImportTask.ts`
- Modify: 调用 `useAiImportTask` 的组件
- Test: `frontend/src/stores/__tests__/import.spec.ts`

- [ ] **Step 1: 读现有 aiImportTask.ts 了解其 API**

Run: `cat frontend/src/stores/aiImportTask.ts`
记录它导出的所有 ref 和方法名。

- [ ] **Step 2: 定位调用点**

Run: `grep -rn "useAiImportTask\|aiImportTask" frontend/src --include="*.vue" --include="*.ts"`

- [ ] **Step 3: 写 import store 测试**

Create `frontend/src/stores/__tests__/import.spec.ts`:

```typescript
import { setActivePinia, createPinia } from "pinia";
import { beforeEach, describe, expect, it } from "vitest";
import { useImportStore } from "../import";

describe("useImportStore", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it("starts with empty task state", () => {
    const store = useImportStore();
    // 根据实际导出的状态调整断言
    expect(store.taskId).toBeNull();  // 或对应的初始值
  });
});
```

注意：具体断言需对照 `aiImportTask.ts` 实际导出的状态名。先读完源码再确定断言。

- [ ] **Step 4: 运行测试确认失败**

Run: `cd frontend && npx vitest run src/stores/__tests__/import.spec.ts`
Expected: FAIL

- [ ] **Step 5: 创建 Pinia 版 import store**

Create `frontend/src/stores/import.ts`，将 `aiImportTask.ts` 的逻辑迁移为 Pinia setup store，保持所有导出的状态和方法名。

迁移模式与 Task 9 的 auth 一致：把模块级 `ref` 放进 `defineStore` 的 setup 函数内，`function` 保持不变，最后 `return` 所有需要暴露的成员。

- [ ] **Step 6: 运行测试**

Run: `cd frontend && npx vitest run src/stores/__tests__/import.spec.ts`
Expected: PASS

- [ ] **Step 7: 更新调用点，删除旧文件**

将所有 `useAiImportTask` 调用改为 `useImportStore`。删除 `frontend/src/stores/aiImportTask.ts`。

- [ ] **Step 8: 运行前端测试 + typecheck**

Run: `cd frontend && npm run typecheck && npx vitest run`
Expected: PASS

- [ ] **Step 9: 提交**

```bash
git add -A
git commit -m "refactor: migrate ai import task store to Pinia"
```

---

## Task 11: 创建 notification store

**Files:**
- Create: `frontend/src/stores/notification.ts`
- Test: `frontend/src/stores/__tests__/notification.spec.ts`

- [ ] **Step 1: 写测试**

Create `frontend/src/stores/__tests__/notification.spec.ts`:

```typescript
import { setActivePinia, createPinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useNotificationStore } from "../notification";

describe("useNotificationStore", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.useFakeTimers();
  });

  it("starts with empty notifications", () => {
    const store = useNotificationStore();
    expect(store.notifications).toHaveLength(0);
  });

  it("notify adds a notification with generated id", () => {
    const store = useNotificationStore();
    store.notify({ type: "success", message: "ok" });
    expect(store.notifications).toHaveLength(1);
    expect(store.notifications[0].message).toBe("ok");
    expect(store.notifications[0].id).toBeDefined();
  });

  it("dismiss removes by id", () => {
    const store = useNotificationStore();
    store.notify({ type: "info", message: "hi" });
    const id = store.notifications[0].id;
    store.dismiss(id);
    expect(store.notifications).toHaveLength(0);
  });
});
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd frontend && npx vitest run src/stores/__tests__/notification.spec.ts`
Expected: FAIL

- [ ] **Step 3: 实现 notification store**

Create `frontend/src/stores/notification.ts`:

```typescript
import { ref } from "vue";
import { defineStore } from "pinia";

export type NotificationType = "success" | "error" | "info" | "warning";

export interface Notification {
  id: number;
  type: NotificationType;
  message: string;
}

let nextId = 1;

export const useNotificationStore = defineStore("notification", () => {
  const notifications = ref<Notification[]>([]);

  function notify(payload: { type: NotificationType; message: string; duration?: number }): number {
    const id = nextId++;
    notifications.value.push({ id, type: payload.type, message: payload.message });
    const duration = payload.duration ?? 4000;
    if (duration > 0) {
      setTimeout(() => dismiss(id), duration);
    }
    return id;
  }

  function dismiss(id: number): void {
    const idx = notifications.value.findIndex((n) => n.id === id);
    if (idx >= 0) notifications.value.splice(idx, 1);
  }

  function clear(): void {
    notifications.value = [];
  }

  return { notifications, notify, dismiss, clear };
});
```

- [ ] **Step 4: 运行测试**

Run: `cd frontend && npx vitest run src/stores/__tests__/notification.spec.ts`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add frontend/src/stores/notification.ts frontend/src/stores/__tests__/notification.spec.ts
git commit -m "feat: add global notification store"
```

---

## Task 12: 路由全部改为懒加载 + CSS 拆分骨架

**Files:**
- Modify: `frontend/src/router.ts`
- Create: `frontend/src/styles/base.css`、`transitions.css`、`utilities.css`
- Modify: `frontend/src/main.ts`

- [ ] **Step 1: 记录当前首屏 JS 体积作为基线**

Run: `cd frontend && npm run build 2>&1 | grep -E "dist/assets/.*\.js"` 
记录各 chunk 大小，作为懒加载后的对比依据。

- [ ] **Step 2: 改 router.ts 为动态 import**

修改 `frontend/src/router.ts`，删除所有 view 的静态 import（保留 `AppLayout`、`AuthLayout` 两个 layout，它们是布局壳子，保留静态 import 无妨），改为在路由配置中用动态 import：

将顶部 import 区（第 5-22 行的 view import）全部删除，只保留：
```typescript
import { createRouter, createWebHistory, type RouteRecordRaw } from "vue-router";
import { getToken } from "./api/request";
import AppLayout from "./layouts/AppLayout.vue";
import AuthLayout from "./layouts/AuthLayout.vue";
```

然后在每个路由的 `component:` 改为动态 import，例如：
```typescript
{
  path: "",
  name: "home",
  component: () => import("./views/Home.vue"),
  meta: { title: "首页", description: "快速进入题库、AI 导入和练习流程。", navKey: "home" },
},
```

对全部 17 个路由逐一替换 `component: Home` → `component: () => import("./views/Home.vue")`。每个路由的 `meta` 保持不变。

- [ ] **Step 3: 创建 CSS 拆分骨架文件**

Create `frontend/src/styles/base.css`（从 style.css 提取 CSS 变量部分 —— `:root { ... }` 块）:

先 Run: `grep -n ":root" frontend/src/style.css` 定位变量块，将整个 `:root { ... }` 复制到 `base.css`。

Create `frontend/src/styles/transitions.css`（从 style.css 提取 `@keyframes` 和 transition 相关规则）:
Run: `grep -n "@keyframes\|transition:" frontend/src/style.css` 定位，复制到 transitions.css。

Create `frontend/src/styles/utilities.css`（剩余自定义工具类，先建空文件占位）:
```css
/* Custom utilities not covered by Tailwind. Populated in Phase 2. */
```

注意：Phase 1 **不删除** `style.css`（Tailwind 迁移留到 Phase 2）。本步只是建立拆分骨架，验证 import 路径正确即可。

- [ ] **Step 4: 在 main.ts 引入新 CSS（不删除 style.css）**

修改 `frontend/src/main.ts`，在 `import "./style.css";` 之前添加：
```typescript
import "./styles/base.css";
import "./styles/transitions.css";
import "./styles/utilities.css";
import "./style.css";  // Phase 2 将移除此行并迁移到 Tailwind
```

- [ ] **Step 5: typecheck + build**

Run: `cd frontend && npm run typecheck && npm run build`
Expected: build 成功。对比 Step 1 的 JS 体积，确认主 chunk 减小、出现多个按需加载的 chunk。

- [ ] **Step 6: 运行前端测试**

Run: `cd frontend && npx vitest run`
Expected: PASS

- [ ] **Step 7: 提交**

```bash
git add frontend/src/router.ts frontend/src/styles/ frontend/src/main.ts
git commit -m "perf: lazy-load all routes; scaffold CSS split"
```

---

# 里程碑 M4：前端 — 巨石组件拆分 + CI

## Task 13: 拆分 ImportQuestions.vue

**Files:**
- Create: `frontend/src/components/import/ImportFileUpload.vue`
- Create: `frontend/src/components/import/ImportAiConfig.vue`
- Create: `frontend/src/components/import/ImportResultList.vue`
- Create: `frontend/src/components/import/ImportTaskMonitor.vue`
- Modify: `frontend/src/views/ImportQuestions.vue`
- 保留：`frontend/src/components/import/ImportPreview.vue`（已存在）

- [ ] **Step 1: 通读 ImportQuestions.vue，识别职责边界**

Run: `cd frontend && cat src/views/ImportQuestions.vue`（868 行）

识别 5 个区域：
1. 文件上传 + 拖拽区 → `ImportFileUpload`
2. AI 配置（模型、prompt 等选项）→ `ImportAiConfig`
3. 预览（已有 `ImportPreview.vue`，确认它是否已被充分使用）
4. 导入结果列表 → `ImportResultList`
5. 异步任务监控（轮询进度）→ `ImportTaskMonitor`

记录每个区域的 template 范围（行号）和对应的 script 逻辑（ref、function）。

- [ ] **Step 2: 提取 ImportFileUpload.vue**

Create `frontend/src/components/import/ImportFileUpload.vue`。

提取文件上传的 template 和相关逻辑。父子通过 props/emits 通信：
- props: `disabled: boolean`
- emits: `upload`（payload: File）、`text-import`（payload: string）

把原组件中处理文件选择、拖拽、文本粘贴的方法移入此组件，通过 emit 把 File 或文本交给父组件。

模板（基于原组件对应区域的结构，保留原有 class 和交互）：

```vue
<script setup lang="ts">
import { ref } from "vue";

defineProps<{ disabled: boolean }>();
const emit = defineEmits<{
  (e: "upload", file: File): void;
  (e: "text-import", text: string): void;
}>();

const isDragging = ref(false);
const pastedText = ref("");

function onFileChange(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (file) emit("upload", file);
}

function onDrop(event: DragEvent) {
  isDragging.value = false;
  const file = event.dataTransfer?.files?.[0];
  if (file) emit("upload", file);
}

function submitText() {
  if (pastedText.value.trim()) {
    emit("text-import", pastedText.value.trim());
  }
}
</script>

<!-- template 复制原文件上传区的 HTML，把事件绑定改为上面的方法 -->
```

**重要**：template 部分必须从原 ImportQuestions.vue 对应区域**逐字复制**，保留所有 class、文案、图标。本计划不重写 UI，只搬移。

- [ ] **Step 3: 提取 ImportAiConfig.vue**

同样模式，提取 AI 配置区。props 接收当前配置值，emits `update:` 事件实现 v-model 双向绑定。

- [ ] **Step 4: 提取 ImportResultList.vue**

提取结果展示区。props: `results: ImportedQuestion[]`、`warnings: string[]`。

- [ ] **Step 5: 提取 ImportTaskMonitor.vue**

提取异步任务轮询区。props: `taskId: string | null`，emits `complete`、`error`。把轮询逻辑（setInterval / setTimeout 调 API）移入。

- [ ] **Step 6: 改写 ImportQuestions.vue 为组合器**

将 `ImportQuestions.vue` 改为：仅负责状态编排和子组件组合，template 引入 5 个子组件，把对应逻辑分发下去。每个子组件通过 `v-model` / props / emits 与父组件交互。

最终 `ImportQuestions.vue` 应从 868 行降到约 200-300 行（只剩状态管理和子组件组装）。

- [ ] **Step 7: typecheck + build + test**

Run: `cd frontend && npm run typecheck && npm run build && npx vitest run`
Expected: PASS

- [ ] **Step 8: 手动验证（dev server）**

Run: `cd frontend && npm run dev`
在浏览器打开导入页，验证：上传、AI 配置、预览、导入、任务监控全部正常工作。对照重构前行为一致。

- [ ] **Step 9: 提交**

```bash
git add frontend/src/components/import/ frontend/src/views/ImportQuestions.vue
git commit -m "refactor: split ImportQuestions into focused subcomponents"
```

---

## Task 14: 拆分 CourseDetail.vue

**Files:**
- Create: `frontend/src/components/course/CourseQuestionList.vue`
- Create: `frontend/src/components/course/CoursePracticeSettings.vue`
- Modify: `frontend/src/views/CourseDetail.vue`

- [ ] **Step 1: 通读识别边界**

Run: `cd frontend && cat src/views/CourseDetail.vue`（237 行）

识别两个区域：
1. 题目列表（表格 + 分页 + 操作）→ `CourseQuestionList`
2. 练习设置（随机题数、题型筛选等）→ `CoursePracticeSettings`

- [ ] **Step 2: 提取 CourseQuestionList.vue**

Create `frontend/src/components/course/CourseQuestionList.vue`。
props: `courseId: number`、`questions: Question[]`、`loading: boolean`。
emits: `edit`、`delete`、`page-change`。

template 从原组件复制题目列表区域。

- [ ] **Step 3: 提取 CoursePracticeSettings.vue**

Create `frontend/src/components/course/CoursePracticeSettings.vue`。
props 接收当前设置，emits `update:` 实现双向绑定。

- [ ] **Step 4: 改写 CourseDetail.vue**

改为组合两个子组件 + 顶部的课程信息区。从 237 行降到约 100-120 行。

- [ ] **Step 5: typecheck + build + test + 手动验证**

Run: `cd frontend && npm run typecheck && npm run build && npx vitest run`
Expected: PASS
手动验证课程详情页的题目列表和练习设置正常。

- [ ] **Step 6: 提交**

```bash
git add frontend/src/components/course/ frontend/src/views/CourseDetail.vue
git commit -m "refactor: split CourseDetail into CourseQuestionList and CoursePracticeSettings"
```

---

## Task 15: 拆分 PracticeHub.vue

**Files:**
- Create: `frontend/src/components/practice/DailyStatsCard.vue`
- Create: `frontend/src/components/practice/QuickPracticeEntry.vue`
- Modify: `frontend/src/views/PracticeHub.vue`

- [ ] **Step 1: 通读识别边界**

Run: `cd frontend && cat src/views/PracticeHub.vue`（422 行）

注意：`components/practice/` 目录已存在其他 8 个练习组件，本任务添加 2 个新的。

识别：
1. 每日数据统计卡片 → `DailyStatsCard`
2. 快速练习入口（错题练习、到期复习、随机练习等入口卡片）→ `QuickPracticeEntry`

- [ ] **Step 2: 提取 DailyStatsCard.vue**

Create `frontend/src/components/practice/DailyStatsCard.vue`。
props: `stats: PracticeStats`（今日练习数、正确率等）。
纯展示组件，无 emits。

- [ ] **Step 3: 提取 QuickPracticeEntry.vue**

Create `frontend/src/components/practice/QuickPracticeEntry.vue`。
props: `entries: PracticeEntry[]`（每个 entry 含图标、标题、描述、路由目标）。
emits: `select`（payload: entry id）。

- [ ] **Step 4: 改写 PracticeHub.vue**

组合两个子组件。从 422 行降到约 150-200 行。

- [ ] **Step 5: typecheck + build + test + 手动验证**

Run: `cd frontend && npm run typecheck && npm run build && npx vitest run`
Expected: PASS
手动验证练习 Hub 页数据卡片和入口正常。

- [ ] **Step 6: 提交**

```bash
git add frontend/src/components/practice/ frontend/src/views/PracticeHub.vue
git commit -m "refactor: split PracticeHub into DailyStatsCard and QuickPracticeEntry"
```

---

## Task 16: 在 CI 中启用前端 vitest

**Files:**
- Modify: `.github/workflows/ci.yml`

- [ ] **Step 1: 修改 ci.yml 的 frontend job**

修改 `.github/workflows/ci.yml` 的 `frontend` job，在 Build 步骤前添加 Test 步骤：

将：
```yaml
      - name: Build
        working-directory: frontend
        run: npm run build
```

改为：
```yaml
      - name: Typecheck
        working-directory: frontend
        run: npm run typecheck

      - name: Test
        working-directory: frontend
        run: npm run test

      - name: Build
        working-directory: frontend
        run: npm run build
```

- [ ] **Step 2: 本地验证 CI 会跑的命令**

Run: `cd frontend && npm run typecheck && npm run test && npm run build`
Expected: 全部 PASS（这是 CI 将执行的精确命令序列）

- [ ] **Step 3: 提交**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: run frontend typecheck and vitest in CI"
```

---

## Task 17: Phase 1 完整性验证

**Files:** 无（纯验证任务）

- [ ] **Step 1: 后端全量测试**

Run: `cd backend && python -m pytest -q`
Expected: PASS（所有测试，包括新增的 crud_base、file_parser、ai_extractor、orchestrator、logging 测试）

- [ ] **Step 2: 前端全量测试**

Run: `cd frontend && npm run test`
Expected: PASS

- [ ] **Step 3: 前端 typecheck**

Run: `cd frontend && npm run typecheck`
Expected: 无错误

- [ ] **Step 4: 前端 build**

Run: `cd frontend && npm run build`
Expected: build 成功

- [ ] **Step 5: 验证文件大小目标达成**

Run:
```bash
wc -l frontend/src/views/ImportQuestions.vue frontend/src/views/CourseDetail.vue frontend/src/views/PracticeHub.vue
```
Expected: 三个文件都显著缩小（ImportQuestions < 400 行，CourseDetail < 150 行，PracticeHub < 250 行）

- [ ] **Step 6: 验证 imports_service.py 已被包取代**

Run: `cd backend && python -c "from backend.services.imports_service import preview_import_from_text; print('shim ok')"`
Expected: 输出 `shim ok`（证明兼容 shim 工作）

- [ ] **Step 7: 验证 GenericCRUD 被复用**

Run: `grep -rn "apply_pagination\|GenericCRUD" backend/ --include="*.py"`
Expected: 至少在 crud_base.py、crud_common.py、crud_courses.py 中出现

- [ ] **Step 8: 对照 spec 验收标准逐项确认**

对照 `docs/superpowers/specs/2026-06-27-major-refactor-design.md` §3.9 的 8 项验收标准，逐项标记完成。

- [ ] **Step 9: 最终提交（如有遗漏的改动）**

```bash
git add -A
git status  # 确认无遗漏
```

---

## 完成标准（对照 Spec §3.9）

- [x] `style.css` 暂存（Phase 2 才删），CSS 拆分骨架已建立（base/transitions/utilities）
- [x] 所有路由使用动态 import
- [x] Pinia stores 替代裸模块（auth、import、notification）
- [x] 三个巨石组件拆分完成，单文件显著缩小
- [x] `imports_service.py` 拆分为 imports 包（file_parser/ai_extractor/ai_client_calls/import_validator/import_orchestrator）
- [x] `GenericCRUD` + `apply_pagination` 被 CRUD 模块复用
- [x] CI 同时跑前后端测试
- [x] 现有 300+ 后端测试全部通过，前端测试通过

---

## 自查备注（Self-Review）

**Spec 覆盖**: Spec §3 的 3.1–3.8 全部映射到任务：
- 3.1 CSS 拆分 → Task 12（Phase 1 建骨架，Phase 2 完整 Tailwind 迁移，符合"渐进式"原则）
- 3.2 路由懒加载 → Task 12
- 3.3 Pinia → Task 9, 10, 11
- 3.4 拆巨石组件 → Task 13, 14, 15
- 3.5 拆 God Service → Task 4, 5, 6, 7
- 3.6 通用 CRUD → Task 1, 2, 3
- 3.7 结构化日志 + 配置 → Task 8
- 3.8 测试补全 → 各任务内含测试 + Task 16 CI

**类型一致性**: `GenericCRUD`、`PaginatedResult`、`apply_pagination` 命名在 Task 1–3 间一致。`useAuthStore`/`useImportStore`/`useNotificationStore` 命名一致。`preview_import_from_text`、`validate_question_item` 等函数名迁移前后保持不变。

**注**: Spec §3.1 提到废弃 style.css，但完整 Tailwind 迁移是 Phase 2 的工作。本计划 Task 12 只建立拆分骨架（base/transitions/utilities）并保留 style.css，避免 Phase 1 一次性引入 Tailwind 导致样式大面积破损（符合 Spec §2"增量迁移、行为保持"原则）。这是有意的阶段划分，非遗漏。
