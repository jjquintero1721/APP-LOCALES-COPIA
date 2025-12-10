"""
Repositorio para operaciones de Modifiers en la base de datos.
"""
from typing import List, Optional
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from app.models.modifiers.modifier_model import (
    ModifierGroup,
    Modifier,
    ModifierInventoryItem,
    ProductModifier,
)


class ModifiersRepository:
    """
    Repositorio para gestionar operaciones CRUD de ModifierGroup, Modifier y ProductModifier.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # ============= MODIFIER GROUP METHODS =============

    async def create_modifier_group(
        self,
        business_id: int,
        name: str,
        description: Optional[str],
        allow_multiple: bool,
        is_required: bool,
    ) -> ModifierGroup:
        """Crear un nuevo grupo de modificadores"""
        group = ModifierGroup(
            business_id=business_id,
            name=name,
            description=description,
            allow_multiple=allow_multiple,
            is_required=is_required,
        )
        self.db.add(group)
        await self.db.commit()
        await self.db.refresh(group)
        return group

    async def get_modifier_group_by_id(
        self,
        group_id: int,
        business_id: int,
    ) -> Optional[ModifierGroup]:
        """Obtener grupo de modificadores por ID"""
        result = await self.db.execute(
            select(ModifierGroup)
            .options(selectinload(ModifierGroup.modifiers))
            .where(and_(ModifierGroup.id == group_id, ModifierGroup.business_id == business_id))
        )
        return result.scalar_one_or_none()

    async def get_all_modifier_groups(
        self,
        business_id: int,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = False,
    ) -> List[ModifierGroup]:
        """Obtener todos los grupos de modificadores de un negocio"""
        query = select(ModifierGroup).options(
            selectinload(ModifierGroup.modifiers)
        ).where(ModifierGroup.business_id == business_id)

        if active_only:
            query = query.where(ModifierGroup.is_active == True)

        query = query.order_by(ModifierGroup.name).offset(skip).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_modifier_group(self, group: ModifierGroup) -> ModifierGroup:
        """Actualizar un grupo de modificadores"""
        await self.db.commit()
        await self.db.refresh(group)
        return group

    # ============= MODIFIER METHODS =============

    async def create_modifier(
        self,
        modifier_group_id: int,
        name: str,
        description: Optional[str],
        price_extra: Decimal,
    ) -> Modifier:
        """Crear un nuevo modificador"""
        modifier = Modifier(
            modifier_group_id=modifier_group_id,
            name=name,
            description=description,
            price_extra=price_extra,
        )
        self.db.add(modifier)
        await self.db.flush()
        return modifier

    async def add_modifier_inventory_item(
        self,
        modifier_id: int,
        inventory_item_id: int,
        quantity: Decimal,
    ) -> ModifierInventoryItem:
        """Agregar un ítem de inventario a un modificador"""
        item = ModifierInventoryItem(
            modifier_id=modifier_id,
            inventory_item_id=inventory_item_id,
            quantity=quantity,
        )
        self.db.add(item)
        await self.db.flush()
        return item

    async def get_modifier_by_id(self, modifier_id: int) -> Optional[Modifier]:
        """Obtener modificador por ID con todas sus relaciones"""
        result = await self.db.execute(
            select(Modifier)
            .options(
                selectinload(Modifier.modifier_group),
                selectinload(Modifier.inventory_items).selectinload(ModifierInventoryItem.inventory_item),
            )
            .where(Modifier.id == modifier_id)
        )
        return result.scalar_one_or_none()

    async def get_modifiers_by_group(
        self,
        modifier_group_id: int,
        active_only: bool = False,
    ) -> List[Modifier]:
        """Obtener todos los modificadores de un grupo"""
        query = select(Modifier).options(
            selectinload(Modifier.inventory_items).selectinload(ModifierInventoryItem.inventory_item)
        ).where(Modifier.modifier_group_id == modifier_group_id)

        if active_only:
            query = query.where(Modifier.is_active == True)

        query = query.order_by(Modifier.name)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def modifier_name_exists_in_group(
        self,
        name: str,
        modifier_group_id: int,
        exclude_id: Optional[int] = None,
    ) -> bool:
        """Verificar si un nombre de modificador ya existe en el grupo"""
        query = select(Modifier).where(
            and_(
                Modifier.modifier_group_id == modifier_group_id,
                Modifier.name == name,
            )
        )

        if exclude_id:
            query = query.where(Modifier.id != exclude_id)

        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None

    async def update_modifier(self, modifier: Modifier) -> Modifier:
        """Actualizar un modificador"""
        await self.db.commit()
        await self.db.refresh(modifier)
        return modifier

    async def delete_modifier_inventory_items(self, modifier: Modifier):
        """Eliminar todos los ítems de inventario de un modificador"""
        for item in modifier.inventory_items:
            await self.db.delete(item)
        await self.db.flush()

    # ============= PRODUCT MODIFIER METHODS =============

    async def assign_modifier_to_product(
        self,
        product_id: int,
        modifier_id: int,
    ) -> ProductModifier:
        """Asignar un modificador a un producto"""
        product_modifier = ProductModifier(
            product_id=product_id,
            modifier_id=modifier_id,
        )
        self.db.add(product_modifier)
        await self.db.commit()
        await self.db.refresh(product_modifier)
        return product_modifier

    async def get_product_modifier(
        self,
        product_id: int,
        modifier_id: int,
    ) -> Optional[ProductModifier]:
        """Verificar si un modificador está asignado a un producto"""
        result = await self.db.execute(
            select(ProductModifier).where(
                and_(
                    ProductModifier.product_id == product_id,
                    ProductModifier.modifier_id == modifier_id,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_modifiers_for_product(self, product_id: int) -> List[ProductModifier]:
        """Obtener todos los modificadores asignados a un producto"""
        result = await self.db.execute(
            select(ProductModifier)
            .options(
                selectinload(ProductModifier.modifier)
                .selectinload(Modifier.modifier_group),
                selectinload(ProductModifier.modifier)
                .selectinload(Modifier.inventory_items),
            )
            .where(ProductModifier.product_id == product_id)
        )
        return list(result.scalars().all())

    async def remove_modifier_from_product(
        self,
        product_id: int,
        modifier_id: int,
    ):
        """Desasignar un modificador de un producto"""
        result = await self.db.execute(
            select(ProductModifier).where(
                and_(
                    ProductModifier.product_id == product_id,
                    ProductModifier.modifier_id == modifier_id,
                )
            )
        )
        product_modifier = result.scalar_one_or_none()
        if product_modifier:
            await self.db.delete(product_modifier)
            await self.db.commit()

    async def commit(self):
        """Hacer commit de los cambios"""
        await self.db.commit()
