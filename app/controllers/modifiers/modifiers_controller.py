"""
Controller para Modificadores.
Capa delgada que delega al servicio de modificadores.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.services.modifiers.modifiers_service import ModifiersService
from app.schemas.modifiers.modifier_schema import (
    ModifierGroupCreate,
    ModifierGroupUpdate,
    ModifierGroupResponse,
    ModifierCreate,
    ModifierUpdate,
    ModifierResponse,
    ModifierListResponse,
    ProductModifierAssign,
    ProductModifierResponse,
)
from app.models.users.user_model import User


class ModifiersController:
    """
    Controller para gestionar endpoints de modificadores.
    """

    # ============= MODIFIER GROUP METHODS =============

    @staticmethod
    async def create_modifier_group(
        data: ModifierGroupCreate,
        current_user: User,
        db: AsyncSession,
    ) -> ModifierGroupResponse:
        """Crear un nuevo grupo de modificadores"""
        service = ModifiersService(db)
        return await service.create_modifier_group(data, current_user)

    @staticmethod
    async def get_modifier_group_by_id(
        group_id: int,
        current_user: User,
        db: AsyncSession,
    ) -> ModifierGroupResponse:
        """Obtener un grupo de modificadores por ID"""
        service = ModifiersService(db)
        return await service.get_modifier_group_by_id(group_id, current_user)

    @staticmethod
    async def get_all_modifier_groups(
        skip: int,
        limit: int,
        active_only: bool,
        current_user: User,
        db: AsyncSession,
    ) -> List[ModifierGroupResponse]:
        """Obtener todos los grupos de modificadores"""
        service = ModifiersService(db)
        return await service.get_all_modifier_groups(
            current_user,
            skip=skip,
            limit=limit,
            active_only=active_only,
        )

    @staticmethod
    async def update_modifier_group(
        group_id: int,
        data: ModifierGroupUpdate,
        current_user: User,
        db: AsyncSession,
    ) -> ModifierGroupResponse:
        """Actualizar un grupo de modificadores"""
        service = ModifiersService(db)
        return await service.update_modifier_group(group_id, data, current_user)

    # ============= MODIFIER METHODS =============

    @staticmethod
    async def create_modifier(
        data: ModifierCreate,
        current_user: User,
        db: AsyncSession,
    ) -> ModifierResponse:
        """Crear un nuevo modificador"""
        service = ModifiersService(db)
        return await service.create_modifier(data, current_user)

    @staticmethod
    async def get_modifier_by_id(
        modifier_id: int,
        current_user: User,
        db: AsyncSession,
    ) -> ModifierResponse:
        """Obtener un modificador por ID"""
        service = ModifiersService(db)
        return await service.get_modifier_by_id(modifier_id, current_user)

    @staticmethod
    async def get_modifiers_by_group(
        group_id: int,
        active_only: bool,
        current_user: User,
        db: AsyncSession,
    ) -> List[ModifierListResponse]:
        """Obtener todos los modificadores de un grupo"""
        service = ModifiersService(db)
        return await service.get_modifiers_by_group(group_id, current_user, active_only)

    @staticmethod
    async def update_modifier(
        modifier_id: int,
        data: ModifierUpdate,
        current_user: User,
        db: AsyncSession,
    ) -> ModifierResponse:
        """Actualizar un modificador"""
        service = ModifiersService(db)
        return await service.update_modifier(modifier_id, data, current_user)

    # ============= PRODUCT MODIFIER METHODS =============

    @staticmethod
    async def assign_modifier_to_product(
        product_id: int,
        data: ProductModifierAssign,
        current_user: User,
        db: AsyncSession,
    ) -> ProductModifierResponse:
        """Asignar un modificador a un producto"""
        service = ModifiersService(db)
        return await service.assign_modifier_to_product(product_id, data, current_user)

    @staticmethod
    async def get_modifiers_for_product(
        product_id: int,
        current_user: User,
        db: AsyncSession,
    ) -> List[ProductModifierResponse]:
        """Obtener todos los modificadores de un producto"""
        service = ModifiersService(db)
        return await service.get_modifiers_for_product(product_id, current_user)

    @staticmethod
    async def remove_modifier_from_product(
        product_id: int,
        modifier_id: int,
        current_user: User,
        db: AsyncSession,
    ):
        """Desasignar un modificador de un producto"""
        service = ModifiersService(db)
        return await service.remove_modifier_from_product(product_id, modifier_id, current_user)
