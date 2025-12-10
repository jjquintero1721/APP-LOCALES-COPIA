"""
Repositorio para operaciones de InventoryTransfer en la base de datos.
Gestiona traslados de inventario entre negocios relacionados.
"""
from typing import List, Optional
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import func
from app.models.inventory.inventory_transfer_model import InventoryTransfer, TransferItem
from app.models.inventory.inventory_enums import TransferStatus


class InventoryTransfersRepository:
    """
    Repositorio para gestionar operaciones de InventoryTransfer y TransferItem.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_transfer(
        self,
        from_business_id: int,
        to_business_id: int,
        created_by_user_id: int,
        notes: Optional[str],
        items: List[dict],  # [{"inventory_item_id": int, "quantity": Decimal, "notes": str}]
    ) -> InventoryTransfer:
        """
        Crear un nuevo traslado de inventario con sus ítems.

        Args:
            from_business_id: ID del negocio origen
            to_business_id: ID del negocio destino
            created_by_user_id: ID del usuario que crea el traslado
            notes: Notas del traslado
            items: Lista de ítems a trasladar

        Returns:
            InventoryTransfer creado con sus ítems
        """
        # Crear el traslado
        transfer = InventoryTransfer(
            from_business_id=from_business_id,
            to_business_id=to_business_id,
            created_by_user_id=created_by_user_id,
            status=TransferStatus.PENDING.value,
            notes=notes,
        )
        self.db.add(transfer)
        await self.db.flush()  # Flush para obtener el ID del traslado

        # Crear los ítems del traslado
        for item_data in items:
            transfer_item = TransferItem(
                transfer_id=transfer.id,
                inventory_item_id=item_data["inventory_item_id"],
                quantity=item_data["quantity"],
                notes=item_data.get("notes"),
            )
            self.db.add(transfer_item)

        await self.db.commit()
        await self.db.refresh(transfer)
        return transfer

    async def get_by_id(self, transfer_id: int) -> Optional[InventoryTransfer]:
        """Obtener traslado por ID con todas las relaciones"""
        result = await self.db.execute(
            select(InventoryTransfer)
            .options(
                selectinload(InventoryTransfer.from_business),
                selectinload(InventoryTransfer.to_business),
                selectinload(InventoryTransfer.created_by),
                selectinload(InventoryTransfer.items).selectinload(TransferItem.inventory_item),
            )
            .where(InventoryTransfer.id == transfer_id)
        )
        return result.scalar_one_or_none()

    async def get_transfers_for_business(
        self,
        business_id: int,
        status_filter: Optional[TransferStatus] = None,
        direction: Optional[str] = None,  # "outgoing", "incoming", None = both
    ) -> List[InventoryTransfer]:
        """
        Obtener traslados de un negocio.

        Args:
            business_id: ID del negocio
            status_filter: Filtrar por estado (opcional)
            direction: "outgoing" (enviados), "incoming" (recibidos), None (ambos)

        Returns:
            Lista de traslados
        """
        query = select(InventoryTransfer).options(
            selectinload(InventoryTransfer.from_business),
            selectinload(InventoryTransfer.to_business),
            selectinload(InventoryTransfer.items).selectinload(TransferItem.inventory_item),
        )

        # Filtrar por dirección
        if direction == "outgoing":
            query = query.where(InventoryTransfer.from_business_id == business_id)
        elif direction == "incoming":
            query = query.where(InventoryTransfer.to_business_id == business_id)
        else:
            query = query.where(
                or_(
                    InventoryTransfer.from_business_id == business_id,
                    InventoryTransfer.to_business_id == business_id,
                )
            )

        # Filtrar por estado
        if status_filter:
            query = query.where(InventoryTransfer.status == status_filter)

        query = query.order_by(InventoryTransfer.created_at.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_status(
        self,
        transfer: InventoryTransfer,
        new_status: TransferStatus,
    ) -> InventoryTransfer:
        """
        Actualizar el estado de un traslado.

        Args:
            transfer: Objeto InventoryTransfer
            new_status: Nuevo estado

        Returns:
            InventoryTransfer actualizado
        """
        transfer.status = new_status

        # Si el estado es COMPLETED, registrar fecha de completado
        if new_status == TransferStatus.COMPLETED:
            transfer.completed_at = func.now()

        await self.db.commit()
        await self.db.refresh(transfer)
        return transfer

    async def cancel_transfer(self, transfer: InventoryTransfer) -> InventoryTransfer:
        """
        Cancelar un traslado.

        Args:
            transfer: Objeto InventoryTransfer

        Returns:
            InventoryTransfer cancelado
        """
        transfer.status = TransferStatus.CANCELLED.value
        await self.db.commit()
        await self.db.refresh(transfer)
        return transfer
