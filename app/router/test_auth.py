from fastapi import APIRouter, Depends

from core.dependencies import get_current_user, require_manager

router = APIRouter(prefix="/test", tags=["Test Auth"])


@router.get("/private")
def private_route(current_user: dict = Depends(get_current_user)):
    return {
        "message": "Você está autenticado",
        "user": current_user
    }


@router.get("/manager")
def manager_route(current_user: dict = Depends(require_manager)):
    return {
        "message": "Acesso de gestor liberado",
        "user": current_user
    }
