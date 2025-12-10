"""
Controller para Traslados de Inventario.
Capa delgada que delega al servicio de traslados de inventario.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.services.inventory.inventory_transfers_service import InventoryTransfersService
from app.schemas.inventory.inventory_transfer_schema import (
    TransferCreate,
    TransferResponse,
    TransferListResponse,
)
from app.models.users.user_model import User


class InventoryTransfersController:
    """
    Controller para gestionar endpoints de traslados de inventario.
    """

    @staticmethod
    async def create_transfer(
        data: TransferCreate,
        current_user: User,
        db: AsyncSession,
    ) -> TransferResponse:
        """Crear un nuevo traslado de inventario"""
        service = InventoryTransfersService(db)
        return await service.create_transfer(data, current_user)

    @staticmethod
    async def accept_transfer(
        transfer_id: int,
        current_user: User,
        db: AsyncSession,
    ) -> TransferResponse:
        """Aceptar un traslado de inventario"""
        service = InventoryTransfersService(db)
        return await service.accept_transfer(transfer_id, current_user)

    @staticmethod
    async def reject_transfer(
        transfer_id: int,
        current_user: User,
        db: AsyncSession,
    ) -> TransferResponse:
        """Rechazar un traslado de inventario"""
        service = InventoryTransfersService(db)
        return await service.reject_transfer(transfer_id, current_user)

    @staticmethod
    async def cancel_transfer(
        transfer_id: int,
        current_user: User,
        db: AsyncSession,
    ) -> TransferResponse:
        """Cancelar un traslado de inventario"""
        service = InventoryTransfersService(db)
        return await service.cancel_transfer(transfer_id, current_user)

    @staticmethod
    async def get_transfer_by_id(
        transfer_id: int,
        current_user: User,
        db: AsyncSession,
    ) -> TransferResponse:
        """Obtener un traslado por ID"""
        service = InventoryTransfersService(db)
        return await service.get_transfer_by_id(transfer_id, current_user)

    @staticmethod
    async def get_transfers(
        status_filter: Optional[str],
        direction: Optional[str],
        current_user: User,
        db: AsyncSession,
    ) -> List[TransferListResponse]:
        """Obtener todos los traslados del negocio"""
        service = InventoryTransfersService(db)
        return await service.get_transfers(
            current_user,
            status_filter=status_filter,
            direction=direction,
        )
