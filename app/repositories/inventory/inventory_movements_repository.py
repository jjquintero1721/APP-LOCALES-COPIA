"""
Repositorio para operaciones de InventoryMovement en la base de datos.
TODOS los queries filtran por business_id (multi-tenant).
"""
from typing import List, Optional
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from sqlalchemy.orm import selectinload
from app.models.inventory.inventory_movement_model import InventoryMovement
from app.models.inventory.inventory_enums import MovementType


class InventoryMovementsRepository:
    """
    Repositorio para gestionar operaciones de InventoryMovement.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        inventory_item_id: int,
        business_id: int,
        created_by_user_id: Optional[int],
        movement_type: MovementType,
        quantity: Decimal,
        reason: Optional[str] = None,
        reference_id: Optional[int] = None,
    ) -> InventoryMovement:
        """Crear un nuevo movimiento de inventario"""
        movement = InventoryMovement(
            inventory_item_id=inventory_item_id,
            business_id=business_id,
            created_by_user_id=created_by_user_id,
            movement_type=movement_type,
            quantity=quantity,
            reason=reason,
            reference_id=reference_id,
        )
        self.db.add(movement)
        await self.db.commit()
        await self.db.refresh(movement)
        return movement

    async def get_by_id(self, movement_id: int, business_id: int) -> Optional[InventoryMovement]:
        """Obtener movimiento por ID (filtrado por business_id) con relaciones"""
        result = await self.db.execute(
            select(InventoryMovement)
            .options(
                selectinload(InventoryMovement.inventory_item),
                selectinload(InventoryMovement.created_by),
                selectinload(InventoryMovement.business),
            )
            .where(and_(InventoryMovement.id == movement_id, InventoryMovement.business_id == business_id))
        )
        return result.scalar_one_or_none()

    async def get_by_item(
        self,
        item_id: int,
        business_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> List[InventoryMovement]:
        """Obtener historial de movimientos de un ítem específico"""
        result = await self.db.execute(
            select(InventoryMovement)
            .options(
                selectinload(InventoryMovement.created_by),
            )
            .where(
                and_(
                    InventoryMovement.inventory_item_id == item_id,
                    InventoryMovement.business_id == business_id,
                )
            )
            .order_by(desc(InventoryMovement.created_at))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_business(
        self,
        business_id: int,
        skip: int = 0,
        limit: int = 100,
        movement_type: Optional[MovementType] = None,
    ) -> List[InventoryMovement]:
        """Obtener todos los movimientos del negocio con paginación"""
        query = select(InventoryMovement).options(
            selectinload(InventoryMovement.inventory_item),
            selectinload(InventoryMovement.created_by),
        ).where(InventoryMovement.business_id == business_id)

        if movement_type:
            query = query.where(InventoryMovement.movement_type == movement_type)

        query = query.order_by(desc(InventoryMovement.created_at)).offset(skip).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def mark_as_reverted(
        self,
        movement: InventoryMovement,
        reverting_movement_id: int,
    ) -> InventoryMovement:
        """Marcar un movimiento como revertido"""
        movement.reverted = True
        movement.reverted_by_movement_id = reverting_movement_id
        await self.db.commit()
        await self.db.refresh(movement)
        return movement
