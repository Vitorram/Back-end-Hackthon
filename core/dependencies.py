from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from core.security import decode_access_token
from core.roles import UserRole

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials
    payload = decode_access_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")

    return {
        "id": payload.get("user_id"),
        "name": payload.get("name"),
        "email": payload.get("sub"),
        "role": payload.get("role"),
        "school_id": payload.get("school_id"),
        "school_name": payload.get("school_name"),
        "permissions": payload.get("permissions", {}),
    }


def require_super_admin(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Acesso permitido apenas para gestores centrais"
        )

    return current_user


def require_manager(current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in (UserRole.MANAGER, UserRole.SUPER_ADMIN):
        raise HTTPException(
            status_code=403,
            detail="Acesso permitido apenas para gestores"
        )

    return current_user


def can_access_school(school_id: int, current_user: dict):
    if current_user["role"] == UserRole.SUPER_ADMIN:
        return True

    return current_user["school_id"] == school_id


def require_permission(permission: str):
    def dependency(current_user: dict = Depends(get_current_user)):
        if current_user["role"] == UserRole.SUPER_ADMIN:
            return current_user

        if not current_user.get("permissions", {}).get(permission):
            raise HTTPException(status_code=403, detail="Permissao insuficiente")

        return current_user

    return dependency
