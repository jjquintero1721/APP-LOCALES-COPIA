"""
Router para Relaciones entre Negocios.
Define los endpoints REST para gestión de relaciones entre negocios.
"""
from fastapi import APIRouter, Depends, Path
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.config.database import get_db
from app.controllers.business.business_relationships_controller import BusinessRelationshipsController
from app.schemas.business.business_relationship_schema import (
    RelationshipCreateRequest,
    RelationshipResponse,
)
from app.dependencies.auth_dependencies import require_owner
from app.models.users.user_model import User

router = APIRouter(
    prefix="/business/relationships",
    tags=["Business Relationships"],
)


@router.post("/", response_model=RelationshipResponse, status_code=201)
async def create_relationship_request(
    data: RelationshipCreateRequest,
    current_user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    """
    Crea una solicitud de relación con otro negocio.

    Requiere rol: OWNER únicamente

    Validaciones:
    - No puede relacionarse consigo mismo
    - El negocio destino debe existir
    - No debe existir ya una relación entre los dos negocios

    Una vez creada, la solicitud queda en estado PENDING.
    El OWNER del negocio destino debe aceptarla o rechazarla.
    """
    return await BusinessRelationshipsController.create_relationship_request(
        data, current_user, db
    )


@router.get("/pending", response_model=List[RelationshipResponse])
async def get_pending_requests(
    current_user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    """
    Obtiene las solicitudes de relación pendientes recibidas.

    Requiere rol: OWNER únicamente

    Retorna solo las solicitudes donde este negocio es el destino (target)
    y están en estado PENDING.
    """
    return await BusinessRelationshipsController.get_pending_requests(
        current_user, db
    )


@router.get("/active", response_model=List[RelationshipResponse])
async def get_active_relationships(
    current_user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    """
    Obtiene las relaciones activas del negocio.

    Requiere rol: OWNER únicamente

    Retorna todas las relaciones en estado ACTIVE donde el negocio
    es requester o target. Estas relaciones permiten traslados de inventario.
    """
    return await BusinessRelationshipsController.get_active_relationships(
        current_user, db
    )


@router.post("/{relationship_id}/accept", response_model=RelationshipResponse)
async def accept_relationship(
    relationship_id: int = Path(..., description="ID de la relación"),
    current_user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    """
    Acepta una solicitud de relación.

    Requiere rol: OWNER únicamente

    Validaciones:
    - El usuario debe ser el OWNER del negocio destino
    - La relación debe estar en estado PENDING

    Al aceptar, la relación pasa a estado ACTIVE y permite traslados.
    """
    return await BusinessRelationshipsController.accept_relationship(
        relationship_id, current_user, db
    )


@router.post("/{relationship_id}/reject", response_model=RelationshipResponse)
async def reject_relationship(
    relationship_id: int = Path(..., description="ID de la relación"),
    current_user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    """
    Rechaza una solicitud de relación.

    Requiere rol: OWNER únicamente

    Validaciones:
    - El usuario debe ser el OWNER del negocio destino
    - La relación debe estar en estado PENDING

    Al rechazar, la relación pasa a estado REJECTED.
    """
    return await BusinessRelationshipsController.reject_relationship(
        relationship_id, current_user, db
    )
