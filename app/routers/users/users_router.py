from fastapi import APIRouter, Query, Depends
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.config.database import get_db
from app.controllers.users.users_controller import UsersController
from app.schemas.users.user_schema import UserResponse
from app.dependencies.auth_dependencies import get_current_user
from app.models.users.user_model import User

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Obtiene el perfil del usuario actual.
    Requiere autenticación.
    """
    return await UsersController.get_me(current_user)


@router.get("/", response_model=List[UserResponse])
async def get_users(
    skip: int = Query(0, ge=0, description="Número de registros a omitir"),
    limit: int = Query(100, ge=1, le=100, description="Número máximo de registros"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Obtiene todos los usuarios del negocio.
    Requiere autenticación.
    Solo retorna usuarios del mismo business_id.
    """
    return await UsersController.get_users(skip, limit, current_user, db)
