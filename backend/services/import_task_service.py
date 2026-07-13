"""Persistent task lifecycle for long-running AI file imports.

The router owns HTTP concerns and schedules this service with FastAPI's
background runner. Keeping task state here makes the contract testable and
lets a future Redis/Celery worker reuse the same processor without changing
the frontend API.
"""

from __future__ import annotations

import json
import os
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable
from uuid import uuid4

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from .. import schemas
from ..crud import derive_course_name_from_filename
from ..database import SessionLocal
from ..models import ImportTask
from . import imports_service


TASK_UPLOAD_DIR = Path(__file__).resolve().parents[1] / "uploads" / "import_tasks"
RECOVERABLE_STATUSES = ("queued", "extracting", "parsing")


def _now() -> datetime:
    return datetime.now(UTC)


def _decode_list(value: str | None) -> list:
    try:
        data = json.loads(value or "[]")
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def _decode_dict(value: str | None) -> dict:
    try:
        data = json.loads(value or "{}")
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


def task_to_schema(task: ImportTask) -> schemas.ImportTaskOut:
    question_data = _decode_list(task.preview_questions_json)
    timing_data = _decode_dict(task.timing_json)
    warnings = [str(item) for item in _decode_list(task.warnings_json)]
    if task.status == "ready" and task.error_message:
        warnings.append(task.error_message)
    return schemas.ImportTaskOut(
        id=task.id,
        status=task.status,
        source_filename=task.source_filename,
        course_id=task.course_id,
        course_name=task.course_name or "",
        progress_current=task.progress_current,
        progress_total=task.progress_total,
        questions=[schemas.ImportedQuestion.model_validate(item) for item in question_data],
        suggested_course_name=task.course_name or "未分类题库",
        warnings=warnings,
        total_valid=task.total_valid,
        total_invalid=task.total_invalid,
        timing=schemas.ImportTiming.model_validate(timing_data) if timing_data else None,
        error_message=task.error_message or "",
        created_at=task.created_at.isoformat() if task.created_at else None,
        started_at=task.started_at.isoformat() if task.started_at else None,
        finished_at=task.finished_at.isoformat() if task.finished_at else None,
    )


async def save_upload_for_task(file: UploadFile) -> tuple[str, str]:
    """Persist a validated upload until the worker has consumed it."""

    saved = await imports_service.save_upload_to_temp(file)
    TASK_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    target = TASK_UPLOAD_DIR / f"{uuid4().hex}{saved.ext}"
    try:
        shutil.move(saved.path, target)
    except Exception:
        imports_service.cleanup_temp_file(saved.path)
        raise
    return saved.filename, str(target)


def create_task(
    db: Session,
    *,
    owner_id: int,
    source_filename: str,
    file_path: str,
    course_id: int = 0,
    course_name: str = "",
) -> ImportTask:
    task = ImportTask(
        id=str(uuid4()),
        owner_id=owner_id,
        status="queued",
        source_filename=source_filename,
        file_path=file_path,
        course_id=course_id or None,
        course_name=course_name or derive_course_name_from_filename(source_filename),
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def get_owned_task(db: Session, *, task_id: str, owner_id: int) -> ImportTask:
    task = db.query(ImportTask).filter(ImportTask.id == task_id, ImportTask.owner_id == owner_id).first()
    if task is None:
        # Do not disclose whether a task exists for another account.
        raise HTTPException(status_code=404, detail="导入任务不存在")
    return task


def _save(db: Session, task: ImportTask) -> None:
    db.add(task)
    db.commit()
    db.refresh(task)


def _mark_failed(db: Session, task: ImportTask, message: str) -> None:
    task.status = "failed"
    task.error_message = message
    task.finished_at = _now()
    _save(db, task)


def recover_pending_tasks(
    session_factory: Callable[[], Session] = SessionLocal,
    schedule: Callable[[str], None] | None = None,
    *,
    limit: int = 2,
) -> list[str]:
    """Requeue persisted parsing tasks after an application restart.

    Files are kept until parsing reaches a terminal state, so queued and
    interrupted extraction/parsing tasks can safely restart. Import
    confirmation is never replayed: an interrupted write is returned to
    ``ready`` so the user can review the preview and confirm it again.
    """

    db = session_factory()
    recovered: list[str] = []
    try:
        tasks = (
            db.query(ImportTask)
            .filter(ImportTask.status.in_((*RECOVERABLE_STATUSES, "importing")))
            .order_by(ImportTask.created_at.asc())
            .limit(max(limit, 0))
            .all()
        )
        for task in tasks:
            if task.status == "importing":
                task.status = "ready"
                task.error_message = "服务重启时确认导入被中断，题目尚未写入；请确认后重试。"
                continue
            if task.file_path and os.path.exists(task.file_path):
                task.status = "queued"
                task.error_message = ""
                task.progress_current = 0
                task.progress_total = 0
                recovered.append(task.id)
            else:
                task.status = "failed"
                task.error_message = "服务重启时未找到待解析文件，请重新上传。"
                task.finished_at = _now()
        db.commit()
    finally:
        db.close()

    if schedule is not None:
        for task_id in recovered:
            schedule(task_id)
    return recovered


def process_task(
    task_id: str,
    sync_ai_overrides: Callable[[], None] | None = None,
    session_factory: Callable[[], Session] = SessionLocal,
) -> None:
    """Run one task in the background and persist every observable outcome."""

    db = session_factory()
    task: ImportTask | None = None
    try:
        task = db.query(ImportTask).filter(ImportTask.id == task_id).first()
        if task is None or task.status != "queued":
            return
        if not task.file_path or not os.path.exists(task.file_path):
            _mark_failed(db, task, "导入文件已过期，请重新上传。")
            return

        total_start = __import__("time").perf_counter()
        task.status = "extracting"
        task.started_at = _now()
        _save(db, task)

        extract_start = __import__("time").perf_counter()
        text, extract_warnings = imports_service.extract_text_or_raise(task.file_path)
        images, image_warnings = imports_service.extract_images_from_file(task.file_path)
        extract_ms = imports_service.elapsed_ms(extract_start)

        task.status = "parsing"
        task.progress_current = 0
        task.progress_total = 0
        _save(db, task)

        if sync_ai_overrides is not None:
            sync_ai_overrides()
        questions, ai_warnings, parse_timing = imports_service.preview_import_from_file_content(text, images)
        if not questions:
            _mark_failed(db, task, "AI 未能解析出可导入题目，请检查文档内容后重试。")
            return

        timing = imports_service.build_timing(
            total_start=total_start,
            extract_ms=extract_ms,
            parse_timing=parse_timing,
        )
        task.status = "ready"
        task.progress_current = timing.chunks
        task.progress_total = timing.chunks
        task.preview_questions_json = json.dumps(questions, ensure_ascii=False)
        task.warnings_json = json.dumps(extract_warnings + image_warnings + ai_warnings, ensure_ascii=False)
        task.timing_json = json.dumps(timing.model_dump(), ensure_ascii=False)
        task.total_valid = len(questions)
        task.total_invalid = sum(1 for warning in ai_warnings if "格式有误" in warning)
        task.error_message = ""
        task.finished_at = _now()
        _save(db, task)
    except HTTPException as exc:
        if task is not None:
            _mark_failed(db, task, str(exc.detail))
    except Exception:
        if task is not None:
            _mark_failed(db, task, "AI 解析失败，请稍后重试。")
    finally:
        if task is not None and task.file_path:
            imports_service.cleanup_temp_file(task.file_path)
            task.file_path = None
            _save(db, task)
        db.close()
