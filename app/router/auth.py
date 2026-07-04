from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.dependencies import get_current_user, require_super_admin
from core.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    get_token_expiration,
    hash_token,
)
from database.database import get_db
from models.refresh_token import RefreshToken
from models.usuario import Usuario
from schemas.auth import (
    ApproveUserRequest,
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    RefreshTokenRequest,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


def _user_payload(user: Usuario) -> dict:
    return {
        "sub": user.email,
        "user_id": user.id,
        "name": user.nome,
        "role": user.perfil,
        "school_id": user.escola_id,
        "permissions": {
            "pode_ver_dashboard": bool(user.pode_ver_dashboard),
            "pode_transferir": bool(user.pode_transferir),
            "pode_editar_equipamento": bool(user.pode_editar_equipamento),
        },
    }


def _user_response(user: Usuario) -> dict:
    return {
        "id": user.id,
        "nome": user.nome,
        "email": user.email,
        "perfil": user.perfil,
        "escola_id": user.escola_id,
        "aprovado": bool(user.aprovado),
        "aprovado_por": user.aprovado_por,
        "aprovado_em": user.aprovado_em,
        "permissoes": {
            "pode_ver_dashboard": bool(user.pode_ver_dashboard),
            "pode_transferir": bool(user.pode_transferir),
            "pode_editar_equipamento": bool(user.pode_editar_equipamento),
        },
    }


def _persist_refresh_token(db: Session, user_id: int, refresh_token: str) -> None:
    expires_at = get_token_expiration(refresh_token)
    if expires_at is None:
        raise HTTPException(status_code=500, detail="Refresh token sem expiracao")

    db.add(
        RefreshToken(
            usuario_id=user_id,
            token_hash=hash_token(refresh_token),
            expires_at=expires_at.replace(tzinfo=None),
        )
    )
    db.commit()


def _issue_tokens(db: Session, user: Usuario) -> dict:
    access_token = create_access_token(_user_payload(user))
    refresh_token = create_refresh_token({"sub": user.email, "user_id": user.id})
    _persist_refresh_token(db, user.id, refresh_token)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": _user_response(user),
    }


@router.post("/login", response_model=LoginResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(Usuario).filter(Usuario.email == data.email).first()

    if not user or user.senha_hash != data.password:
        raise HTTPException(status_code=401, detail="E-mail ou senha invalidos")

    if not user.ativo:
        raise HTTPException(status_code=403, detail="Usuario inativo")

    if not user.aprovado and user.perfil != "SUPER_ADMIN":
        raise HTTPException(status_code=403, detail="Usuario pendente de aprovacao")

    return _issue_tokens(db, user)


@router.post("/refresh", response_model=LoginResponse)
def refresh_token(data: RefreshTokenRequest, db: Session = Depends(get_db)):
    payload = decode_refresh_token(data.refresh_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Refresh token invalido ou expirado")

    token_record = (
        db.query(RefreshToken)
        .filter(RefreshToken.token_hash == hash_token(data.refresh_token))
        .first()
    )

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if not token_record or token_record.revoked or token_record.expires_at <= now:
        raise HTTPException(status_code=401, detail="Refresh token revogado ou expirado")

    user = db.query(Usuario).filter(Usuario.id == payload.get("user_id")).first()
    if not user or not user.ativo:
        raise HTTPException(status_code=401, detail="Usuario invalido ou inativo")

    if not user.aprovado and user.perfil != "SUPER_ADMIN":
        raise HTTPException(status_code=403, detail="Usuario pendente de aprovacao")

    token_record.revoked = True
    token_record.revoked_at = now
    db.commit()

    return _issue_tokens(db, user)


@router.post("/logout")
def logout(data: LogoutRequest, db: Session = Depends(get_db)):
    token_record = (
        db.query(RefreshToken)
        .filter(RefreshToken.token_hash == hash_token(data.refresh_token))
        .first()
    )

    if token_record and not token_record.revoked:
        token_record.revoked = True
        token_record.revoked_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.commit()

    return {"message": "Logout realizado"}


@router.get("/pending")
def list_pending_users(
    _: dict = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    users = (
        db.query(Usuario)
        .filter(Usuario.aprovado == False)  # noqa: E712
        .order_by(Usuario.criado_em.asc())
        .all()
    )

    return [_user_response(user) for user in users]


@router.post("/users/{user_id}/approve")
def approve_user(
    user_id: int,
    data: ApproveUserRequest,
    current_user: dict = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    user = db.query(Usuario).filter(Usuario.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="Usuario nao encontrado")

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    user.perfil = data.perfil
    user.escola_id = data.escola_id
    user.aprovado = True
    user.aprovado_por = current_user["id"]
    user.aprovado_em = now
    user.pode_ver_dashboard = data.pode_ver_dashboard
    user.pode_transferir = data.pode_transferir
    user.pode_editar_equipamento = data.pode_editar_equipamento

    if data.perfil == "SUPER_ADMIN":
        user.escola_id = None
        user.pode_ver_dashboard = True
        user.pode_transferir = True
        user.pode_editar_equipamento = True

    db.commit()
    db.refresh(user)

    return _user_response(user)


@router.get("/me")
def me(current_user: dict = Depends(get_current_user)):
    return current_user
