"""
Router para Business.
Define los endpoints REST para gestión de negocios.
"""
from fastapi import APIRouter, Depends
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.config.database import get_db
from app.controllers.business.business_controller import BusinessController
from app.schemas.business.business_schema import BusinessResponse
from app.dependencies.auth_dependencies import get_current_user
from app.models.users.user_model import User

router = APIRouter(
    prefix="/business",
    tags=["Business"],
)


@router.get("/", response_model=List[BusinessResponse])
async def get_all_businesses(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Obtiene todos los negocios registrados.

    Requiere autenticación.

    Retorna una lista de todos los negocios en el sistema.
    Útil para listar negocios disponibles para crear relaciones.
    """
    return await BusinessController.get_all_businesses(db)
