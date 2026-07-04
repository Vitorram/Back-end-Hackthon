from typing import Literal

from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user: dict


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class ApproveUserRequest(BaseModel):
    perfil: Literal["COMMON", "MANAGER", "SUPER_ADMIN"]
    escola_id: int | None = None
    pode_ver_dashboard: bool = False
    pode_transferir: bool = False
    pode_editar_equipamento: bool = False
