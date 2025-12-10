"""
Repositorio para operaciones de InventoryItem en la base de datos.
TODOS los queries filtran por business_id (multi-tenant).
"""
from typing import List, Optional
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
from app.models.inventory.inventory_item_model import InventoryItem


class InventoryItemsRepository:
    """
    Repositorio para gestionar operaciones CRUD de InventoryItem.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        business_id: int,
        name: str,
        category: Optional[str],
        unit_of_measure: str,
        sku: Optional[str],
        quantity_in_stock: Decimal,
        min_stock: Optional[Decimal],
        max_stock: Optional[Decimal],
        unit_price: Decimal,
        tax_percentage: Optional[Decimal],
        include_tax: bool,
        supplier_id: Optional[int],
    ) -> InventoryItem:
        """Crear un nuevo ítem de inventario"""
        item = InventoryItem(
            business_id=business_id,
            supplier_id=supplier_id,
            name=name,
            category=category,
            unit_of_measure=unit_of_measure,
            sku=sku,
            quantity_in_stock=quantity_in_stock,
            min_stock=min_stock,
            max_stock=max_stock,
            unit_price=unit_price,
            tax_percentage=tax_percentage,
            include_tax=include_tax,
        )
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def get_by_id(self, item_id: int, business_id: int) -> Optional[InventoryItem]:
        """Obtener ítem por ID (filtrado por business_id) con relaciones"""
        result = await self.db.execute(
            select(InventoryItem)
            .options(
                selectinload(InventoryItem.business),
                selectinload(InventoryItem.supplier),
            )
            .where(and_(InventoryItem.id == item_id, InventoryItem.business_id == business_id))
        )
        return result.scalar_one_or_none()

    async def get_all_by_business(
        self,
        business_id: int,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = False,
        category: Optional[str] = None,
        supplier_id: Optional[int] = None,
    ) -> List[InventoryItem]:
        """Obtener todos los ítems de un negocio con paginación y filtros"""
        query = select(InventoryItem).options(
            selectinload(InventoryItem.supplier)
        ).where(InventoryItem.business_id == business_id)

        if active_only:
            query = query.where(InventoryItem.is_active == True)

        if category:
            query = query.where(InventoryItem.category == category)

        if supplier_id:
            query = query.where(InventoryItem.supplier_id == supplier_id)

        query = query.offset(skip).limit(limit).order_by(InventoryItem.name)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_sku(self, sku: str, business_id: int) -> Optional[InventoryItem]:
        """Buscar ítem por SKU"""
        result = await self.db.execute(
            select(InventoryItem).where(
                and_(
                    InventoryItem.sku == sku,
                    InventoryItem.business_id == business_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def sku_exists(self, sku: str, business_id: int, exclude_id: Optional[int] = None) -> bool:
        """Verificar si un SKU ya existe para el negocio"""
        query = select(InventoryItem).where(
            and_(
                InventoryItem.sku == sku,
                InventoryItem.business_id == business_id,
            )
        )

        if exclude_id:
            query = query.where(InventoryItem.id != exclude_id)

        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None

    async def get_items_below_min_stock(self, business_id: int) -> List[InventoryItem]:
        """Obtener ítems por debajo del stock mínimo"""
        result = await self.db.execute(
            select(InventoryItem)
            .options(selectinload(InventoryItem.supplier))
            .where(
                and_(
                    InventoryItem.business_id == business_id,
                    InventoryItem.is_active == True,
                    InventoryItem.min_stock.isnot(None),
                    InventoryItem.quantity_in_stock < InventoryItem.min_stock,
                )
            )
            .order_by(InventoryItem.name)
        )
        return list(result.scalars().all())

    async def check_stock_availability(
        self,
        item_id: int,
        business_id: int,
        required_quantity: Decimal,
    ) -> bool:
        """Verificar si hay stock suficiente"""
        item = await self.get_by_id(item_id, business_id)
        if not item:
            return False
        return item.quantity_in_stock >= required_quantity

    async def update_stock(
        self,
        item: InventoryItem,
        new_quantity: Decimal,
    ) -> InventoryItem:
        """Actualizar solo la cantidad en stock"""
        if new_quantity < 0:
            raise ValueError("Stock no puede ser negativo")

        item.quantity_in_stock = new_quantity
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def update(self, item: InventoryItem) -> InventoryItem:
        """Actualizar ítem existente (metadatos, no stock)"""
        await self.db.commit()
        await self.db.refresh(item)
        return item
