from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import auth as auth_module
from .. import crud, schemas
from ..database import get_db
from ..routers.courses import _get_accessible_course

router = APIRouter(prefix="/practice", tags=["practice"])


def _parse_exclude_ids(raw: str) -> list[int]:
    result: list[int] = []
    for item in (raw or "").split(","):
        item = item.strip()
        if not item:
            continue
        try:
            value = int(item)
        except ValueError:
            continue
        if value > 0:
            result.append(value)
    return result


@router.get("/random")
def random_question(
    type: str = "",
    chapter: str = "",
    exclude_ids: str = Query("", description="本轮练习中需要排除的题目 ID，逗号分隔"),
    course_id: int = Query(0, ge=0, description="课程 ID，0 表示从全部可见题目中随机抽题"),
    db: Session = Depends(get_db),
    current_user=Depends(auth_module.get_current_user),
):
    excluded = _parse_exclude_ids(exclude_ids)
    if course_id > 0:
        _get_accessible_course(db, course_id, current_user.id)
        question = crud.get_random_question_in_course(
            db,
            course_id,
            user_id=current_user.id,
            q_type=type,
            chapter=chapter,
            excluded_ids=excluded,
        )
        if not question:
            raise HTTPException(status_code=404, detail="本轮题目已完成或该课程暂无可用题目")
    else:
        question = crud.get_random_question(
            db,
            user_id=current_user.id,
            q_type=type,
            chapter=chapter,
            excluded_ids=excluded,
        )
        if not question:
            raise HTTPException(status_code=404, detail="本轮题目已完成或题库为空")
    return schemas.QuestionOut.model_validate(question).model_dump()


@router.post("/submit", response_model=schemas.SubmitResponse)
def submit_answer(
    body: schemas.SubmitRequest,
    db: Session = Depends(get_db),
    current_user=Depends(auth_module.get_current_user),
):
    question = crud.get_visible_question_by_id(db, body.question_id, current_user.id)
    if not question:
        raise HTTPException(status_code=404, detail="题目不存在")

    is_correct = crud.check_answer(question, body.user_answer)

    if is_correct:
        crud.clear_wrong_record_if_correct(db, current_user.id, question.id)
        wrongbook_recorded = False
    else:
        record = crud.upsert_wrong_record(db, current_user.id, question.id, body.user_answer)
        wrongbook_recorded = record is not None

    crud.create_practice_record(
        db,
        user_id=current_user.id,
        question_id=question.id,
        course_id=question.course_id,
        question_type=question.type,
        is_correct=is_correct,
        user_answer=body.user_answer,
        correct_answer=question.answer,
    )

    crud.upsert_user_question_review(
        db,
        user_id=current_user.id,
        question_id=question.id,
        course_id=question.course_id,
        is_correct=is_correct,
    )

    db.commit()

    return schemas.SubmitResponse(
        is_correct=is_correct,
        correct_answer=question.answer,
        analysis=question.analysis or "",
        wrongbook_recorded=wrongbook_recorded,
    )


@router.get("/stats", response_model=schemas.PracticeStatsOut)
def get_stats(
    db: Session = Depends(get_db),
    current_user=Depends(auth_module.get_current_user),
):
    """Return practice statistics for the current user only."""
    return crud.get_practice_stats(db, user_id=current_user.id)


@router.get("/history", response_model=schemas.PracticeHistoryOut)
def get_history(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_user=Depends(auth_module.get_current_user),
):
    records, total = crud.get_practice_history(
        db,
        user_id=current_user.id,
        page=page,
        page_size=page_size,
    )

    items = []
    for r in records:
        question_text = ""
        if r.question is not None:
            qt = r.question.question or ""
            question_text = qt[:80] + ("..." if len(qt) > 80 else "")

        items.append(
            schemas.PracticeRecordOut(
                id=r.id,
                question_id=r.question_id,
                course_id=r.course_id,
                question_type=r.question_type,
                question_text=question_text,
                is_correct=bool(r.is_correct),
                user_answer=r.user_answer or "",
                correct_answer=r.correct_answer or "",
                answered_at=r.answered_at.isoformat() if r.answered_at else None,
            )
        )

    return schemas.PracticeHistoryOut(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/review/wrong")
def review_wrong_question(
    course_id: int = Query(0, ge=0, description="课程 ID，0 表示全部课程"),
    type: str = "",
    exclude_ids: str = Query("", description="本轮练习中需要排除的题目 ID，逗号分隔"),
    db: Session = Depends(get_db),
    current_user=Depends(auth_module.get_current_user),
):
    if course_id > 0:
        _get_accessible_course(db, course_id, current_user.id)

    question = crud.get_random_wrong_question(
        db,
        user_id=current_user.id,
        course_id=course_id if course_id > 0 else None,
        q_type=type,
        excluded_ids=_parse_exclude_ids(exclude_ids),
    )
    if not question:
        raise HTTPException(status_code=404, detail="本轮错题已完成或暂无错题")
    return schemas.QuestionOut.model_validate(question).model_dump()


@router.get("/review/today", response_model=schemas.TodayReviewOut)
def review_today(
    db: Session = Depends(get_db),
    current_user=Depends(auth_module.get_current_user),
):
    return crud.get_today_review_summary(db, user_id=current_user.id)


@router.get("/review/due")
def review_due(
    course_id: int = Query(0, ge=0, description="课程 ID，0 表示全部课程"),
    limit: int = Query(20, ge=1, le=100, description="最多返回题目数量"),
    exclude_ids: str = Query("", description="本轮练习中需要排除的题目 ID，逗号分隔"),
    db: Session = Depends(get_db),
    current_user=Depends(auth_module.get_current_user),
):
    if course_id > 0:
        _get_accessible_course(db, course_id, current_user.id)

    reviews = crud.get_due_reviews(
        db,
        user_id=current_user.id,
        course_id=course_id if course_id > 0 else None,
        limit=limit,
        excluded_ids=_parse_exclude_ids(exclude_ids),
    )

    items = []
    for rev in reviews:
        item = {
            "id": rev.id,
            "review_level": rev.review_level,
            "next_review_at": rev.next_review_at.isoformat() if rev.next_review_at else None,
            "last_reviewed_at": rev.last_reviewed_at.isoformat() if rev.last_reviewed_at else None,
            "consecutive_correct": rev.consecutive_correct,
            "review_mode": rev.review_mode or "",
            "question": schemas.QuestionOut.model_validate(rev.question).model_dump()
            if rev.question and rev.question_id
            else None,
        }
        items.append(item)

    return {"items": items, "total": len(items)}


@router.get("/insights/weak-types", response_model=list[schemas.WeakTypeOut])
def weak_types(
    db: Session = Depends(get_db),
    current_user=Depends(auth_module.get_current_user),
):
    return crud.get_weak_types(db, user_id=current_user.id)
