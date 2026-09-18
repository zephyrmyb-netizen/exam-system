import secrets

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .. import auth, models, schemas
from ..database import get_db

router = APIRouter(prefix="/study-groups", tags=["study-groups"])


def _commit(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "操作已更新，请刷新后重试")


def _out(db, group, member_count=None):
    if member_count is None:
        member_count = db.query(models.StudyGroupMember).filter_by(group_id=group.id).count()
    return schemas.StudyGroupOut(
        id=group.id, name=group.name, invite_code=group.invite_code, owner_id=group.owner_id, member_count=member_count
    )


@router.get("/mine", response_model=list[schemas.StudyGroupOut])
def mine(db: Session = Depends(get_db), current_user=Depends(auth.get_current_user)):
    counts = (
        db.query(models.StudyGroupMember.group_id, func.count(models.StudyGroupMember.id).label("total"))
        .group_by(models.StudyGroupMember.group_id)
        .subquery()
    )
    groups = (
        db.query(models.StudyGroup, counts.c.total)
        .join(models.StudyGroupMember)
        .join(counts, counts.c.group_id == models.StudyGroup.id)
        .filter(models.StudyGroupMember.user_id == current_user.id)
        .order_by(models.StudyGroup.id.desc())
        .all()
    )
    return [_out(db, group, total) for group, total in groups]


@router.post("/", response_model=schemas.StudyGroupOut, status_code=201)
def create(body: schemas.StudyGroupCreate, db: Session = Depends(get_db), current_user=Depends(auth.get_current_user)):
    if not body.name.strip():
        raise HTTPException(422, "请输入小组名称")
    group = models.StudyGroup(
        owner_id=current_user.id, name=body.name.strip(), invite_code=secrets.token_hex(4).upper()
    )
    db.add(group)
    db.flush()
    db.add(models.StudyGroupMember(group_id=group.id, user_id=current_user.id))
    _commit(db)
    return _out(db, group)


@router.post("/join/{invite_code}", response_model=schemas.StudyGroupOut)
def join(invite_code: str, db: Session = Depends(get_db), current_user=Depends(auth.get_current_user)):
    group = db.query(models.StudyGroup).filter(models.StudyGroup.invite_code == invite_code.strip().upper()).first()
    if not group:
        raise HTTPException(404, "Invite code not found")
    if not db.query(models.StudyGroupMember).filter_by(group_id=group.id, user_id=current_user.id).first():
        db.add(models.StudyGroupMember(group_id=group.id, user_id=current_user.id))
    shared = db.query(models.StudyGroupCourse.course_id).filter_by(group_id=group.id).all()
    existing = {row.course_id for row in db.query(models.Collaboration.course_id).filter_by(user_id=current_user.id)}
    for (course_id,) in shared:
        if course_id not in existing and current_user.id != group.owner_id:
            db.add(
                models.Collaboration(
                    course_id=course_id, user_id=current_user.id, role="viewer", invited_by=group.owner_id
                )
            )
    _commit(db)
    return _out(db, group)


@router.post("/{group_id}/courses/{course_id}")
def share_course(
    group_id: int, course_id: int, db: Session = Depends(get_db), current_user=Depends(auth.get_current_user)
):
    group = db.query(models.StudyGroup).filter_by(id=group_id).first()
    course = db.query(models.QuestionBank).filter_by(id=course_id).first()
    if not group or not course:
        raise HTTPException(404, "Group or course not found")
    if group.owner_id != current_user.id or course.owner_id != current_user.id:
        raise HTTPException(403, "Only the group owner may share an owned course")
    if not db.query(models.StudyGroupCourse).filter_by(group_id=group_id, course_id=course_id).first():
        db.add(models.StudyGroupCourse(group_id=group_id, course_id=course_id))
    existing = {row.user_id for row in db.query(models.Collaboration.user_id).filter_by(course_id=course_id)}
    members = db.query(models.StudyGroupMember).filter_by(group_id=group_id).all()
    for member in members:
        if member.user_id != current_user.id and member.user_id not in existing:
            db.add(
                models.Collaboration(
                    course_id=course_id, user_id=member.user_id, role="viewer", invited_by=current_user.id
                )
            )
    _commit(db)
    return {"group_id": group_id, "course_id": course_id, "shared_with": max(len(members) - 1, 0)}


def _member_or_404(db, group_id, user_id):
    if not db.query(models.StudyGroupMember).filter_by(group_id=group_id, user_id=user_id).first():
        raise HTTPException(404, "Study group not found")


@router.post("/{group_id}/exams/{exam_id}")
def share_exam(group_id: int, exam_id: int, db: Session = Depends(get_db), current_user=Depends(auth.get_current_user)):
    group = db.query(models.StudyGroup).filter_by(id=group_id).first()
    exam = db.query(models.Exam).filter_by(id=exam_id).first()
    if not group or not exam:
        raise HTTPException(404, "Group or exam not found")
    if group.owner_id != current_user.id or exam.creator_id != current_user.id:
        raise HTTPException(403, "Only the group owner may share an owned exam")
    if exam.status != "published":
        raise HTTPException(400, "Publish the exam before sharing it")
    if not db.query(models.StudyGroupExam).filter_by(group_id=group_id, exam_id=exam_id).first():
        db.add(models.StudyGroupExam(group_id=group_id, exam_id=exam_id))
        _commit(db)
    return {"group_id": group_id, "exam_id": exam_id}


@router.get("/{group_id}/resources", response_model=schemas.StudyGroupResourcesOut)
def resources(group_id: int, db: Session = Depends(get_db), current_user=Depends(auth.get_current_user)):
    _member_or_404(db, group_id, current_user.id)
    rows = (
        db.query(
            models.QuestionBank.id, models.QuestionBank.name, func.count(models.Question.id).label("question_count")
        )
        .join(models.StudyGroupCourse, models.StudyGroupCourse.course_id == models.QuestionBank.id)
        .outerjoin(models.Question, models.Question.course_id == models.QuestionBank.id)
        .filter(models.StudyGroupCourse.group_id == group_id)
        .group_by(models.QuestionBank.id, models.QuestionBank.name)
        .order_by(models.QuestionBank.id.desc())
        .all()
    )
    courses = [{"id": row.id, "name": row.name, "question_count": row.question_count} for row in rows]
    exams = [
        {"id": row.id, "title": row.title, "share_code": row.share_code, "status": row.status}
        for row in db.query(models.Exam)
        .join(models.StudyGroupExam)
        .filter(models.StudyGroupExam.group_id == group_id, models.Exam.status == "published")
        .all()
    ]
    return schemas.StudyGroupResourcesOut(group_id=group_id, courses=courses, exams=exams)
