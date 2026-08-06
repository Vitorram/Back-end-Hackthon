from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.core.dependencies import get_current_user, require_super_admin
from backend.database.database import get_db
from backend.services import agent_service

router = APIRouter(prefix="/agent", tags=["Agent"])


class AgentReportRequest(BaseModel):
    prompt: str


class AgentReportRequest(BaseModel):
    prompt: str


@router.get("/summary")
def summary(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return agent_service.get_agent_summary(db, current_user)


@router.get("/search")
def search(
    q: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    can_search_users = (
        current_user["role"] == "SUPER_ADMIN"
        or current_user.get("permissions", {}).get("pode_gerenciar_usuarios")
    )
    return agent_service.search_agent_data(db, q, current_user, limit, can_search_users)


@router.get("/equipments/{identifier}")
def equipment_details(
    identifier: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return agent_service.find_equipment(db, identifier, current_user)


@router.get("/schools/{school_id}/equipments")
def school_equipments(
    school_id: int,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return agent_service.list_equipments_by_school(db, school_id, current_user, limit)


@router.post("/report")
def report(
    data: AgentReportRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return agent_service.generate_equipment_report(db, data.prompt, current_user)


@router.post("/report")
def report(
    data: AgentReportRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return agent_service.generate_equipment_report(db, data.prompt, current_user)


@router.get("/users")
def users(
    apenas_ativos: bool = False,
    limit: int = Query(50, ge=1, le=200),
    _: dict = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    return agent_service.list_users(db, apenas_ativos, limit)


@router.get("/users/{login}")
def user_details(
    login: str,
    _: dict = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    return agent_service.find_user(db, login)
