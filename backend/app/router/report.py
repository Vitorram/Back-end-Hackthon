from datetime import datetime

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from backend.core.dependencies import get_current_user
from backend.database.database import get_db
from backend.schemas.report import (
    ReportCreateRequest,
    ReportShareResponse,
    ReportsOverviewResponse,
    SavedReportResponse,
)
from backend.services.report_service import (
    create_saved_report,
    delete_saved_report,
    get_reports_overview,
    get_saved_report,
    get_shared_report,
    list_saved_reports,
    report_to_csv,
    share_saved_report,
)

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/overview", response_model=ReportsOverviewResponse)
def overview(
    period_start: datetime | None = None,
    period_end: datetime | None = None,
    stale_days: int = Query(180, ge=1, le=3650),
    school_ids: list[int] = Query(default=[]),
    equipment_ids: list[int] = Query(default=[]),
    statuses: list[str] = Query(default=[]),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return get_reports_overview(
        db=db,
        current_user=current_user,
        period_start=period_start,
        period_end=period_end,
        stale_days=stale_days,
        school_ids=school_ids,
        equipment_ids=equipment_ids,
        statuses=statuses,
    )


@router.post("", response_model=SavedReportResponse)
def create_report(
    data: ReportCreateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return create_saved_report(db, current_user, data)


@router.get("", response_model=list[SavedReportResponse])
def list_reports(
    q: str | None = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return list_saved_reports(db, current_user, q)


@router.get("/shared/{token}", response_model=SavedReportResponse)
def shared_report(
    token: str,
    db: Session = Depends(get_db),
):
    return get_shared_report(db, token)


@router.get("/{report_id}", response_model=SavedReportResponse)
def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return get_saved_report(db, report_id, current_user)


@router.delete("/{report_id}", status_code=204)
def delete_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    delete_saved_report(db, report_id, current_user)


@router.post("/{report_id}/share", response_model=ReportShareResponse)
def share_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    report = share_saved_report(db, report_id, current_user)
    return {
        "token": report.compartilhamento_token,
        "url_path": f"/reports/shared/{report.compartilhamento_token}",
    }


@router.get("/{report_id}/export.csv")
def export_report_csv(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    report = get_saved_report(db, report_id, current_user)
    csv_content = report_to_csv(report)
    filename = f"relatorio-{report.id}.csv"
    return Response(
        content=csv_content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
