import time

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from .. import auth as auth_module, schemas
from ..config import IMPORT_RATE_LIMIT_PER_HOUR
from ..crud import derive_course_name_from_filename
from ..database import get_db
from ..ratelimit import RateLimiter, get_limiter
from ..schemas import ImportedQuestion
from ..services import imports_service

router = APIRouter(prefix="/imports", tags=["imports"])

# Backward-compatible exports for existing tests and callers.
extract_text_and_warnings = imports_service.extract_text_and_warnings
extract_text_from_file = imports_service.extract_text_from_file
_validate_question_item = imports_service.validate_question_item
_question_items_from_parsed_json = imports_service.question_items_from_parsed_json
_json_candidates_from_text = imports_service.json_candidates_from_text
_extract_questions_from_ai_response = imports_service.extract_questions_from_ai_response
_call_ai_parse_chunk = imports_service.call_ai_parse_chunk
_deduplicate_questions = imports_service.deduplicate_questions
call_ai_parse = imports_service.call_ai_parse
OPENAI_API_KEY = imports_service.OPENAI_API_KEY
OPENAI_BASE_URL = imports_service.OPENAI_BASE_URL
OpenAI = imports_service.OpenAI


def _sync_ai_overrides() -> None:
    """Propagate router-level overrides (set by tests via mock.patch) to the service module."""
    imports_service.OPENAI_API_KEY = OPENAI_API_KEY
    imports_service.OPENAI_BASE_URL = OPENAI_BASE_URL
    imports_service.OpenAI = OpenAI


def rate_limiter() -> RateLimiter:
    """FastAPI dependency returning the active rate limiter.

    Override in tests via ``app.dependency_overrides[rate_limiter]``.
    """
    return get_limiter()


def _enforce_import_limit(user_id: int, limiter: RateLimiter) -> None:
    """Apply the per-user AI import rate limit.

    AI import calls are expensive (multiple model requests per file), so we
    cap how often a single user can hit them independently of chat limits.
    """
    limiter.check(key=f"import:user:{user_id}", limit=IMPORT_RATE_LIMIT_PER_HOUR)


@router.post("/file", response_model=schemas.FileExtractResponse)
async def upload_file(
    file: UploadFile = File(...),
    course_id: int = Query(0, ge=0, description="目标课程ID，0 表示自动创建/使用未分类题库"),
    db: Session = Depends(get_db),
    _current_user=Depends(auth_module.get_current_user),
):
    del course_id, db
    total_start = time.perf_counter()
    saved = None
    try:
        saved = await imports_service.save_upload_to_temp(file)
        extract_start = time.perf_counter()
        text, _ = imports_service.extract_text_and_warnings(saved.path)
        extract_ms = imports_service.elapsed_ms(extract_start)
        return schemas.FileExtractResponse(
            text=text,
            filename=saved.filename,
            suggested_course_name=derive_course_name_from_filename(saved.filename),
            timing=imports_service.build_timing(total_start=total_start, extract_ms=extract_ms),
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"文件提取失败: {exc}") from exc
    finally:
        imports_service.cleanup_temp_file(saved.path if saved else None)


@router.post("/file/preview", response_model=schemas.PreviewImportResponse)
async def preview_import(
    file: UploadFile = File(...),
    _current_user=Depends(auth_module.get_current_user),
    limiter: RateLimiter = Depends(rate_limiter),
):
    _enforce_import_limit(_current_user.id, limiter)
    total_start = time.perf_counter()
    saved = None
    try:
        saved = await imports_service.save_upload_to_temp(file)
        extract_start = time.perf_counter()
        text, extract_warnings = imports_service.extract_text_or_raise(saved.path)
        extract_ms = imports_service.elapsed_ms(extract_start)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"文件提取失败: {exc}") from exc
    finally:
        imports_service.cleanup_temp_file(saved.path if saved else None)

    try:
        _sync_ai_overrides()
        questions, ai_warnings, parse_timing = imports_service.preview_import_from_text(text)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI 解析失败: {exc}") from exc

    all_warnings = extract_warnings + ai_warnings
    total_valid = len(questions)
    total_invalid = sum(1 for warning in ai_warnings if "格式有误" in warning)

    return schemas.PreviewImportResponse(
        questions=[ImportedQuestion(**question) for question in questions],
        suggested_course_name=derive_course_name_from_filename(saved.filename if saved else (file.filename or "")),
        warnings=all_warnings,
        total_parsed=len(questions),
        total_valid=total_valid,
        total_invalid=total_invalid,
        timing=imports_service.build_timing(
            total_start=total_start,
            extract_ms=extract_ms,
            parse_timing=parse_timing,
        ),
    )


@router.post("/confirm", response_model=schemas.ConfirmImportResponse)
def confirm_import(
    body: schemas.ConfirmImportRequest,
    db: Session = Depends(get_db),
    current_user=Depends(auth_module.get_current_user),
):
    if not body.questions:
        raise HTTPException(status_code=422, detail="没有待导入的题目")

    validated_items, errors = imports_service.validate_imported_questions(body.questions)
    if errors:
        raise HTTPException(
            status_code=422,
            detail=f"部分题目校验不通过，未导入任何题目：{'；'.join(errors)}",
        )

    bank = imports_service.resolve_target_course(
        db,
        current_user.id,
        course_id=body.course_id or 0,
        course_name=body.course_name or "",
    )
    imported = imports_service.persist_imported_questions(
        db,
        user_id=current_user.id,
        course_id=bank.id,
        questions=validated_items,
    )

    return schemas.ConfirmImportResponse(
        imported_count=imported,
        course_id=bank.id,
        course_name=bank.name,
    )


@router.post("/file/auto", response_model=schemas.FileAutoResponse)
async def import_file_auto(
    file: UploadFile = File(...),
    course_id: int = Query(0, ge=0, description="目标课程ID，0 表示使用 course_name 或文件名推断"),
    course_name: str = Query("", description="目标课程名，course_id=0 时优先使用，为空则从文件名推断"),
    db: Session = Depends(get_db),
    current_user=Depends(auth_module.get_current_user),
    limiter: RateLimiter = Depends(rate_limiter),
):
    _enforce_import_limit(current_user.id, limiter)
    total_start = time.perf_counter()
    saved = None
    try:
        saved = await imports_service.save_upload_to_temp(file)
        extract_start = time.perf_counter()
        text, _ = imports_service.extract_text_or_raise(saved.path)
        extract_ms = imports_service.elapsed_ms(extract_start)
        _sync_ai_overrides()
        question_dicts, _warnings, parse_timing = imports_service.preview_import_from_text(text)
        bank = imports_service.resolve_target_course(
            db,
            current_user.id,
            course_id=course_id,
            course_name=course_name,
            filename=saved.filename,
        )
        imported = imports_service.persist_imported_questions(
            db,
            user_id=current_user.id,
            course_id=bank.id,
            questions=question_dicts,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"导入失败: {exc}") from exc
    finally:
        imports_service.cleanup_temp_file(saved.path if saved else None)

    return schemas.FileAutoResponse(
        imported_count=imported,
        course_id=bank.id,
        course_name=bank.name,
        timing=imports_service.build_timing(
            total_start=total_start,
            extract_ms=extract_ms,
            parse_timing=parse_timing,
        ),
    )
