"""
Router para Traslados de Inventario.
Define los endpoints REST para gestión de traslados de inventario entre negocios.
"""
from fastapi import APIRouter, Depends, Path, Query
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.config.database import get_db
from app.controllers.inventory.inventory_transfers_controller import InventoryTransfersController
from app.schemas.inventory.inventory_transfer_schema import (
    TransferCreate,
    TransferResponse,
    TransferListResponse,
)
from app.dependencies.auth_dependencies import require_owner_or_admin, get_current_user
from app.models.users.user_model import User

router = APIRouter(
    prefix="/inventory/transfers",
    tags=["Inventory Transfers"],
)


@router.post("/", response_model=TransferResponse, status_code=201)
async def create_transfer(
    data: TransferCreate,
    current_user: User = Depends(require_owner_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Crea un nuevo traslado de inventario hacia otro negocio.

    Requiere rol: OWNER o ADMIN

    Validaciones:
    - Debe existir una relación ACTIVE entre los negocios
    - Todos los ítems deben pertenecer al negocio origen
    - Debe haber stock suficiente
    - No puede haber ítems duplicados

    El traslado queda en estado PENDING hasta que el negocio destino lo acepte o rechace.
    """
    return await InventoryTransfersController.create_transfer(data, current_user, db)


@router.get("/", response_model=List[TransferListResponse])
async def get_transfers(
    status: Optional[str] = Query(None, description="Filtrar por estado (pending, completed, cancelled, rejected)"),
    direction: Optional[str] = Query(None, description="Filtrar por dirección (outgoing, incoming)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Obtiene todos los traslados del negocio.

    Requiere autenticación.

    Filtros opcionales:
    - status: pending, completed, cancelled, rejected
    - direction: outgoing (enviados), incoming (recibidos)
    """
    return await InventoryTransfersController.get_transfers(
        status, direction, current_user, db
    )


@router.get("/{transfer_id}", response_model=TransferResponse)
async def get_transfer(
    transfer_id: int = Path(..., description="ID del traslado"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Obtiene un traslado por ID con todos sus detalles.

    Requiere autenticación.

    Solo se puede ver si pertenece al negocio origen o destino.
    """
    return await InventoryTransfersController.get_transfer_by_id(
        transfer_id, current_user, db
    )


@router.post("/{transfer_id}/accept", response_model=TransferResponse)
async def accept_transfer(
    transfer_id: int = Path(..., description="ID del traslado"),
    current_user: User = Depends(require_owner_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Acepta un traslado de inventario.

    Requiere rol: OWNER o ADMIN del negocio destino

    Validaciones:
    - El traslado debe estar en estado PENDING
    - Debe haber stock suficiente en el negocio origen

    Al aceptar:
    - Se crean movimientos TRANSFER_OUT en el origen
    - Se crean movimientos TRANSFER_IN en el destino
    - Se actualiza el stock en ambos negocios
    - El estado cambia a COMPLETED
    """
    return await InventoryTransfersController.accept_transfer(
        transfer_id, current_user, db
    )


@router.post("/{transfer_id}/reject", response_model=TransferResponse)
async def reject_transfer(
    transfer_id: int = Path(..., description="ID del traslado"),
    current_user: User = Depends(require_owner_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Rechaza un traslado de inventario.

    Requiere rol: OWNER o ADMIN del negocio destino

    Validaciones:
    - El traslado debe estar en estado PENDING

    Al rechazar, el estado cambia a REJECTED y no se afecta el inventario.
    """
    return await InventoryTransfersController.reject_transfer(
        transfer_id, current_user, db
    )


@router.post("/{transfer_id}/cancel", response_model=TransferResponse)
async def cancel_transfer(
    transfer_id: int = Path(..., description="ID del traslado"),
    current_user: User = Depends(require_owner_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Cancela un traslado de inventario.

    Requiere rol: OWNER o ADMIN del negocio origen

    Validaciones:
    - El traslado debe estar en estado PENDING

    Al cancelar, el estado cambia a CANCELLED y no se afecta el inventario.
    """
    return await InventoryTransfersController.cancel_transfer(
        transfer_id, current_user, db
    )
