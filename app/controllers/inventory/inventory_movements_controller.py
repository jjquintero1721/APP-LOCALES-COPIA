"""
Controller para Movimientos de Inventario.
Capa delgada que delega al servicio de movimientos de inventario.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.services.inventory.inventory_movements_service import InventoryMovementsService
from app.schemas.inventory.inventory_movement_schema import (
    MovementResponse,
    RevertMovementRequest,
)
from app.models.users.user_model import User
from app.models.inventory.inventory_enums import MovementType


class InventoryMovementsController:
    """
    Controller para gestionar endpoints de movimientos de inventario.
    """

    @staticmethod
    async def get_movement_by_id(
        movement_id: int,
        current_user: User,
        db: AsyncSession,
    ) -> MovementResponse:
        """Obtener un movimiento por ID"""
        movements_service = InventoryMovementsService(db)
        return await movements_service.get_movement_by_id(movement_id, current_user)

    @staticmethod
    async def get_movement_history_by_item(
        item_id: int,
        skip: int,
        limit: int,
        current_user: User,
        db: AsyncSession,
    ) -> List[MovementResponse]:
        """Obtener historial de movimientos de un ítem"""
        movements_service = InventoryMovementsService(db)
        return await movements_service.get_movement_history_by_item(
            item_id, current_user, skip, limit
        )

    @staticmethod
    async def get_all_movements(
        skip: int,
        limit: int,
        movement_type: Optional[MovementType],
        current_user: User,
        db: AsyncSession,
    ) -> List[MovementResponse]:
        """Obtener todos los movimientos con filtros"""
        movements_service = InventoryMovementsService(db)
        return await movements_service.get_all_movements(
            current_user, skip, limit, movement_type
        )

    @staticmethod
    async def revert_movement(
        movement_id: int,
        data: RevertMovementRequest,
        current_user: User,
        db: AsyncSession,
    ) -> MovementResponse:
        """Revertir un movimiento"""
        movements_service = InventoryMovementsService(db)
        return await movements_service.revert_movement(movement_id, data, current_user)
