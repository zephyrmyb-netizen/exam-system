"""Layered course API router.

This router is intentionally not mounted in ``backend.main`` yet. It is a
Phase 2 migration template that proves read-only course endpoints can go
through the service layer while the stable legacy router keeps serving users.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from .. import schemas
from ..auth import get_current_user
from ..models import User
from ..services.course_service import CourseService
from .deps import get_course_service, require_permission

router = APIRouter(prefix="/courses", tags=["courses"])

CurrentUser = Annotated[User, Depends(get_current_user)]
CourseServiceDep = Annotated[CourseService, Depends(get_course_service)]
PageParam = Annotated[int, Query(ge=0)]


@router.post("/", status_code=201)
def create_course(
    body: schemas.CourseCreate,
    current_user: Annotated[User, Depends(require_permission("course:create"))],
    service: CourseServiceDep,
):
    bank = service.create_course(body, owner_id=current_user.id)
    return bank.to_dict()


@router.get("/")
def list_courses(
    current_user: CurrentUser,
    service: CourseServiceDep,
    page: PageParam = 0,
    page_size: PageParam = 0,
):
    banks, total = service.list_visible(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
    )
    items = [bank.to_dict() for bank in banks]
    if page <= 0 or page_size <= 0:
        return items
    return {"total": total, "page": page, "page_size": page_size, "items": items}


@router.get("/mine")
def list_my_courses(
    current_user: CurrentUser,
    service: CourseServiceDep,
    page: PageParam = 0,
    page_size: PageParam = 0,
):
    banks, total = service.list_owned(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
    )
    items = [bank.to_dict() for bank in banks]
    if page <= 0 or page_size <= 0:
        return items
    return {"total": total, "page": page, "page_size": page_size, "items": items}


@router.get("/{course_id}")
def get_course(
    course_id: int,
    current_user: CurrentUser,
    service: CourseServiceDep,
):
    bank = service.get_accessible_course(course_id, current_user.id)
    return bank.to_dict()
