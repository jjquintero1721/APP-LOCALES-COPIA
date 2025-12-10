"""
Router para Movimientos de Inventario.
Define los endpoints REST para gestión de movimientos de inventario.
"""
from fastapi import APIRouter, Query, Depends, Path
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.config.database import get_db
from app.controllers.inventory.inventory_movements_controller import InventoryMovementsController
from app.schemas.inventory.inventory_movement_schema import (
    MovementResponse,
    RevertMovementRequest,
)
from app.dependencies.auth_dependencies import (
    require_owner,
    get_current_user,
)
from app.models.users.user_model import User
from app.models.inventory.inventory_enums import MovementType

router = APIRouter(
    prefix="/inventory/movements",
    tags=["Inventory Movements"],
)


@router.get("/", response_model=List[MovementResponse])
async def get_movements(
    skip: int = Query(0, ge=0, description="Número de registros a omitir"),
    limit: int = Query(100, ge=1, le=100, description="Número máximo de registros"),
    movement_type: Optional[MovementType] = Query(None, description="Filtrar por tipo de movimiento"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Obtiene todos los movimientos de inventario del negocio con paginación y filtros.

    Requiere autenticación.

    Solo retorna movimientos del mismo business_id (multi-tenant).
    """
    return await InventoryMovementsController.get_all_movements(
        skip, limit, movement_type, current_user, db
    )


@router.get("/item/{item_id}", response_model=List[MovementResponse])
async def get_movement_history_by_item(
    item_id: int = Path(..., description="ID del ítem de inventario"),
    skip: int = Query(0, ge=0, description="Número de registros a omitir"),
    limit: int = Query(100, ge=1, le=100, description="Número máximo de registros"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Obtiene el historial de movimientos de un ítem específico.

    Requiere autenticación.

    Retorna todos los movimientos (entradas, salidas, ajustes, etc.) del ítem ordenados por fecha.
    """
    return await InventoryMovementsController.get_movement_history_by_item(
        item_id, skip, limit, current_user, db
    )


@router.get("/{movement_id}", response_model=MovementResponse)
async def get_movement(
    movement_id: int = Path(..., description="ID del movimiento"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Obtiene un movimiento de inventario por ID.

    Requiere autenticación.

    Solo se pueden obtener movimientos del mismo business_id (multi-tenant).
    """
    return await InventoryMovementsController.get_movement_by_id(
        movement_id, current_user, db
    )


@router.post("/{movement_id}/revert", response_model=MovementResponse)
async def revert_movement(
    movement_id: int = Path(..., description="ID del movimiento a revertir"),
    data: RevertMovementRequest = ...,
    current_user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    """
    Revierte un movimiento de inventario creando un movimiento inverso.

    Requiere rol: OWNER únicamente

    Validaciones:
    - No se puede revertir un movimiento ya revertido
    - El stock resultante no puede ser negativo
    - Se crea un nuevo movimiento tipo REVERT con cantidad inversa
    - El movimiento original se marca como revertido

    El motivo de la reversión es obligatorio y se registra en auditoría.
    """
    return await InventoryMovementsController.revert_movement(
        movement_id, data, current_user, db
    )
