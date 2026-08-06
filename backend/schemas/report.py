from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel

ReportType = Literal[
    "general_summary",
    "equipments_by_school",
    "equipments_by_status",
    "maintenance_items",
    "transfers_by_period",
    "schools_with_most_defects",
    "stale_equipments",
]


class EquipmentBySchoolReport(BaseModel):
    school_id: int
    school_name: str
    school_code: str
    total: int


class EquipmentByStatusReport(BaseModel):
    status: str
    total: int


class MaintenanceItemReport(BaseModel):
    equipment_id: int
    patrimonio: str | None
    codigo_interno: str
    tipo: str
    marca: str | None
    modelo: str | None
    school_id: int
    school_name: str
    sala_atual: str | None
    atualizado_em: datetime | None


class TransfersByPeriodReport(BaseModel):
    period_start: datetime
    period_end: datetime
    total: int


class SchoolDefectReport(BaseModel):
    school_id: int
    school_name: str
    school_code: str
    defective_total: int


class StaleEquipmentReport(BaseModel):
    equipment_id: int
    patrimonio: str | None
    codigo_interno: str
    tipo: str
    school_id: int
    school_name: str
    last_movement_at: datetime | None
    days_without_movement: int | None


class ParkSummaryReport(BaseModel):
    total_equipments: int
    total_schools: int
    in_use: int
    available: int
    maintenance: int
    defective: int
    in_transfer: int
    discarded: int
    recent_transfers: int
    stale_equipments: int


class ReportsOverviewResponse(BaseModel):
    summary: ParkSummaryReport
    equipments_by_school: list[EquipmentBySchoolReport]
    equipments_by_status: list[EquipmentByStatusReport]
    maintenance_items: list[MaintenanceItemReport]
    transfers_by_period: TransfersByPeriodReport
    schools_with_most_defects: list[SchoolDefectReport]
    stale_equipments: list[StaleEquipmentReport]


class ReportCreateRequest(BaseModel):
    titulo: str
    tipo: ReportType
    period_start: datetime | None = None
    period_end: datetime | None = None
    stale_days: int = 180
    school_ids: list[int] = []
    equipment_ids: list[int] = []
    statuses: list[str] = []


class SavedReportResponse(BaseModel):
    id: int
    titulo: str
    tipo: str
    parametros: dict[str, Any]
    resultado: Any
    criado_por_id: int
    compartilhamento_token: str | None
    criado_em: datetime | None
    atualizado_em: datetime | None

    model_config = {"from_attributes": True}


class ReportShareResponse(BaseModel):
    token: str
    url_path: str
