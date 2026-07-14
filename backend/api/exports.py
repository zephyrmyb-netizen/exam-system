"""Download endpoints for course and practice data."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from .. import models
from ..auth import get_current_user
from ..services.export_service import ExportService
from .deps import get_export_service

router = APIRouter(prefix="/exports", tags=["exports"])

CurrentUser = Annotated[models.User, Depends(get_current_user)]
ExportServiceDep = Annotated[ExportService, Depends(get_export_service)]


@router.get("/courses/{course_id}.json")
def export_course_json(
    course_id: int,
    current_user: CurrentUser,
    service: ExportServiceDep,
):
    try:
        payload = service.export_course_json(course_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return Response(
        content=payload,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="course_{course_id}.json"'},
    )


@router.get("/courses/{course_id}.xlsx")
def export_course_excel(
    course_id: int,
    current_user: CurrentUser,
    service: ExportServiceDep,
):
    try:
        payload = service.export_course_excel(course_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return Response(
        content=payload,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="course_{course_id}.xlsx"'},
    )


@router.get("/practice-history.csv")
def export_practice_history_csv(
    current_user: CurrentUser,
    service: ExportServiceDep,
):
    payload = service.export_practice_history_csv(user_id=current_user.id)
    return Response(
        content=payload,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="practice_history.csv"'},
    )
