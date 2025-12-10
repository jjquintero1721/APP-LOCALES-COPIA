"""
Controller para Ítems de Inventario.
Capa delgada que delega al servicio de ítems de inventario.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.services.inventory.inventory_items_service import InventoryItemsService
from app.schemas.inventory.inventory_item_schema import (
    InventoryItemCreate,
    InventoryItemUpdate,
    InventoryItemResponse,
    StockAdjustmentRequest,
)
from app.models.users.user_model import User


class InventoryItemsController:
    """
    Controller para gestionar endpoints de ítems de inventario.
    """

    @staticmethod
    async def create_item(
        data: InventoryItemCreate,
        current_user: User,
        db: AsyncSession,
    ) -> InventoryItemResponse:
        """Crear un nuevo ítem de inventario"""
        items_service = InventoryItemsService(db)
        return await items_service.create_item(data, current_user)

    @staticmethod
    async def get_item_by_id(
        item_id: int,
        current_user: User,
        db: AsyncSession,
    ) -> InventoryItemResponse:
        """Obtener un ítem por ID"""
        items_service = InventoryItemsService(db)
        return await items_service.get_item_by_id(item_id, current_user)

    @staticmethod
    async def get_all_items(
        skip: int,
        limit: int,
        active_only: bool,
        category: Optional[str],
        supplier_id: Optional[int],
        current_user: User,
        db: AsyncSession,
    ) -> List[InventoryItemResponse]:
        """Obtener todos los ítems con filtros"""
        items_service = InventoryItemsService(db)
        return await items_service.get_all_items(
            current_user,
            skip=skip,
            limit=limit,
            active_only=active_only,
            category=category,
            supplier_id=supplier_id,
        )

    @staticmethod
    async def update_item(
        item_id: int,
        data: InventoryItemUpdate,
        current_user: User,
        db: AsyncSession,
    ) -> InventoryItemResponse:
        """Actualizar un ítem"""
        items_service = InventoryItemsService(db)
        return await items_service.update_item(item_id, data, current_user)

    @staticmethod
    async def deactivate_item(
        item_id: int,
        current_user: User,
        db: AsyncSession,
    ) -> InventoryItemResponse:
        """Inactivar un ítem (soft delete)"""
        items_service = InventoryItemsService(db)
        return await items_service.deactivate_item(item_id, current_user)

    @staticmethod
    async def get_low_stock_alerts(
        current_user: User,
        db: AsyncSession,
    ) -> List[InventoryItemResponse]:
        """Obtener alertas de stock bajo"""
        items_service = InventoryItemsService(db)
        return await items_service.get_low_stock_alerts(current_user)

    @staticmethod
    async def adjust_stock_manually(
        item_id: int,
        data: StockAdjustmentRequest,
        current_user: User,
        db: AsyncSession,
    ) -> InventoryItemResponse:
        """Ajustar stock manualmente"""
        items_service = InventoryItemsService(db)
        return await items_service.adjust_stock_manually(item_id, data, current_user)
