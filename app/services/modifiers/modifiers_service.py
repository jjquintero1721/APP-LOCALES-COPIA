"""
Servicio de Modificadores.
Maneja operaciones CRUD de modificadores con validaciones de compatibilidad y auditoría.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from typing import List
from decimal import Decimal
from app.repositories.modifiers.modifiers_repository import ModifiersRepository
from app.repositories.products.products_repository import ProductsRepository
from app.repositories.inventory.inventory_items_repository import InventoryItemsRepository
from app.repositories.audit.audit_repository import AuditRepository
from app.schemas.modifiers.modifier_schema import (
    ModifierGroupCreate,
    ModifierGroupUpdate,
    ModifierGroupResponse,
    ModifierCreate,
    ModifierUpdate,
    ModifierResponse,
    ModifierListResponse,
    ModifierInventoryItemResponse,
    ProductModifierAssign,
    ProductModifierResponse,
)
from app.models.users.user_model import User, UserRole


class ModifiersService:
    """
    Servicio de modificadores.
    Maneja operaciones CRUD de grupos de modificadores, modificadores y compatibilidad con productos.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.modifiers_repo = ModifiersRepository(db)
        self.products_repo = ProductsRepository(db)
        self.items_repo = InventoryItemsRepository(db)
        self.audit_repo = AuditRepository(db)

    # ============= MODIFIER GROUP METHODS =============

    async def create_modifier_group(
        self,
        data: ModifierGroupCreate,
        current_user: User,
    ) -> ModifierGroupResponse:
        """
        Crea un nuevo grupo de modificadores.

        Validaciones:
        - Solo OWNER, ADMIN y COOK pueden crear grupos

        Args:
            data: Datos del grupo
            current_user: Usuario que crea el grupo

        Returns:
            ModifierGroupResponse con los datos del grupo creado
        """
        # Validar que el usuario sea OWNER, ADMIN o COOK
        if current_user.role not in [UserRole.OWNER, UserRole.ADMIN, UserRole.COOK]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo los roles OWNER, ADMIN y COOK pueden crear grupos de modificadores.",
            )

        # Crear el grupo
        group = await self.modifiers_repo.create_modifier_group(
            business_id=current_user.business_id,
            name=data.name,
            description=data.description,
            allow_multiple=data.allow_multiple,
            is_required=data.is_required,
        )

        # Registrar auditoría
        await self.audit_repo.create_log(
            business_id=current_user.business_id,
            user_id=current_user.id,
            action=f"Grupo de modificadores creado: {group.name} (ID: {group.id}) por {current_user.full_name}",
        )

        return ModifierGroupResponse(
            id=group.id,
            business_id=group.business_id,
            name=group.name,
            description=group.description,
            allow_multiple=group.allow_multiple,
            is_required=group.is_required,
            is_active=group.is_active,
            created_at=group.created_at,
            updated_at=group.updated_at,
            modifiers_count=0,
        )

    async def get_modifier_group_by_id(
        self,
        group_id: int,
        current_user: User,
    ) -> ModifierGroupResponse:
        """Obtiene un grupo de modificadores por ID"""
        group = await self.modifiers_repo.get_modifier_group_by_id(group_id, current_user.business_id)

        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Grupo de modificadores no encontrado.",
            )

        return ModifierGroupResponse(
            id=group.id,
            business_id=group.business_id,
            name=group.name,
            description=group.description,
            allow_multiple=group.allow_multiple,
            is_required=group.is_required,
            is_active=group.is_active,
            created_at=group.created_at,
            updated_at=group.updated_at,
            modifiers_count=len(group.modifiers),
        )

    async def get_all_modifier_groups(
        self,
        current_user: User,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = False,
    ) -> List[ModifierGroupResponse]:
        """Obtiene todos los grupos de modificadores del negocio"""
        groups = await self.modifiers_repo.get_all_modifier_groups(
            business_id=current_user.business_id,
            skip=skip,
            limit=limit,
            active_only=active_only,
        )

        return [
            ModifierGroupResponse(
                id=group.id,
                business_id=group.business_id,
                name=group.name,
                description=group.description,
                allow_multiple=group.allow_multiple,
                is_required=group.is_required,
                is_active=group.is_active,
                created_at=group.created_at,
                updated_at=group.updated_at,
                modifiers_count=len(group.modifiers),
            )
            for group in groups
        ]

    async def update_modifier_group(
        self,
        group_id: int,
        data: ModifierGroupUpdate,
        current_user: User,
    ) -> ModifierGroupResponse:
        """Actualiza un grupo de modificadores"""
        # Validar que el usuario sea OWNER, ADMIN o COOK
        if current_user.role not in [UserRole.OWNER, UserRole.ADMIN, UserRole.COOK]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo los roles OWNER, ADMIN y COOK pueden actualizar grupos de modificadores.",
            )

        # Obtener el grupo
        group = await self.modifiers_repo.get_modifier_group_by_id(group_id, current_user.business_id)

        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Grupo de modificadores no encontrado.",
            )

        # Registrar cambios para auditoría
        changes = []
        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            old_value = getattr(group, field)
            if value != old_value:
                setattr(group, field, value)
                changes.append(f"{field}: '{old_value}' → '{value}'")

        # Solo actualizar si hay cambios
        if changes:
            updated_group = await self.modifiers_repo.update_modifier_group(group)

            # Registrar auditoría
            await self.audit_repo.create_log(
                business_id=current_user.business_id,
                user_id=current_user.id,
                action=f"Grupo de modificadores actualizado: {updated_group.name} (ID: {updated_group.id}). Cambios: {', '.join(changes)}. Actualizado por {current_user.full_name}",
            )

            return ModifierGroupResponse(
                id=updated_group.id,
                business_id=updated_group.business_id,
                name=updated_group.name,
                description=updated_group.description,
                allow_multiple=updated_group.allow_multiple,
                is_required=updated_group.is_required,
                is_active=updated_group.is_active,
                created_at=updated_group.created_at,
                updated_at=updated_group.updated_at,
                modifiers_count=len(updated_group.modifiers),
            )

        return ModifierGroupResponse(
            id=group.id,
            business_id=group.business_id,
            name=group.name,
            description=group.description,
            allow_multiple=group.allow_multiple,
            is_required=group.is_required,
            is_active=group.is_active,
            created_at=group.created_at,
            updated_at=group.updated_at,
            modifiers_count=len(group.modifiers),
        )

    # ============= MODIFIER METHODS =============

    async def create_modifier(
        self,
        data: ModifierCreate,
        current_user: User,
    ) -> ModifierResponse:
        """
        Crea un nuevo modificador con sus ítems de inventario.

        Validaciones:
        - Solo OWNER, ADMIN y COOK pueden crear modificadores
        - El grupo de modificadores debe existir y pertenecer al negocio
        - El nombre no debe repetirse dentro del mismo grupo
        - Todos los ítems de inventario deben existir y estar activos
        - quantity no puede ser 0

        Args:
            data: Datos del modificador
            current_user: Usuario que crea el modificador

        Returns:
            ModifierResponse con los datos del modificador creado
        """
        # Validar que el usuario sea OWNER, ADMIN o COOK
        if current_user.role not in [UserRole.OWNER, UserRole.ADMIN, UserRole.COOK]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo los roles OWNER, ADMIN y COOK pueden crear modificadores.",
            )

        # Validar que el grupo exista y pertenezca al negocio
        group = await self.modifiers_repo.get_modifier_group_by_id(
            data.modifier_group_id,
            current_user.business_id,
        )
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Grupo de modificadores no encontrado o no pertenece a tu negocio.",
            )

        # Validar que el nombre no se repita en el grupo
        if await self.modifiers_repo.modifier_name_exists_in_group(data.name, data.modifier_group_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El nombre '{data.name}' ya existe en el grupo '{group.name}'.",
            )

        # Validar todos los ítems de inventario
        for item_data in data.inventory_items:
            # Validar que el ítem exista y pertenezca al negocio
            item = await self.items_repo.get_by_id(item_data.inventory_item_id, current_user.business_id)
            if not item:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"El ítem con ID {item_data.inventory_item_id} no existe o no pertenece a tu negocio.",
                )

            # Validar que el ítem esté activo
            if not item.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"El ítem '{item.name}' está inactivo. No se puede usar en el modificador.",
                )

        # Crear el modificador
        modifier = await self.modifiers_repo.create_modifier(
            modifier_group_id=data.modifier_group_id,
            name=data.name,
            description=data.description,
            price_extra=data.price_extra,
        )

        # Crear los ítems de inventario del modificador
        for item_data in data.inventory_items:
            await self.modifiers_repo.add_modifier_inventory_item(
                modifier_id=modifier.id,
                inventory_item_id=item_data.inventory_item_id,
                quantity=item_data.quantity,
            )

        await self.modifiers_repo.commit()

        # Registrar auditoría
        await self.audit_repo.create_log(
            business_id=current_user.business_id,
            user_id=current_user.id,
            action=f"Modificador creado: {modifier.name} (ID: {modifier.id}) en grupo '{group.name}' con {len(data.inventory_items)} ítems por {current_user.full_name}",
        )

        # Cargar el modificador con todas las relaciones
        modifier_with_relations = await self.modifiers_repo.get_modifier_by_id(modifier.id)

        return self._build_modifier_response(modifier_with_relations)

    async def get_modifier_by_id(
        self,
        modifier_id: int,
        current_user: User,
    ) -> ModifierResponse:
        """Obtiene un modificador por ID"""
        modifier = await self.modifiers_repo.get_modifier_by_id(modifier_id)

        if not modifier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Modificador no encontrado.",
            )

        # Validar que pertenezca al negocio
        group = await self.modifiers_repo.get_modifier_group_by_id(
            modifier.modifier_group_id,
            current_user.business_id,
        )
        if not group:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="El modificador no pertenece a tu negocio.",
            )

        return self._build_modifier_response(modifier)

    async def get_modifiers_by_group(
        self,
        group_id: int,
        current_user: User,
        active_only: bool = False,
    ) -> List[ModifierListResponse]:
        """Obtiene todos los modificadores de un grupo"""
        # Validar que el grupo exista y pertenezca al negocio
        group = await self.modifiers_repo.get_modifier_group_by_id(group_id, current_user.business_id)
        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Grupo de modificadores no encontrado.",
            )

        modifiers = await self.modifiers_repo.get_modifiers_by_group(group_id, active_only)

        return [self._build_modifier_list_response(modifier) for modifier in modifiers]

    async def update_modifier(
        self,
        modifier_id: int,
        data: ModifierUpdate,
        current_user: User,
    ) -> ModifierResponse:
        """Actualiza un modificador (sin modificar ítems de inventario)"""
        # Validar que el usuario sea OWNER, ADMIN o COOK
        if current_user.role not in [UserRole.OWNER, UserRole.ADMIN, UserRole.COOK]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo los roles OWNER, ADMIN y COOK pueden actualizar modificadores.",
            )

        # Obtener el modificador
        modifier = await self.modifiers_repo.get_modifier_by_id(modifier_id)

        if not modifier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Modificador no encontrado.",
            )

        # Validar que pertenezca al negocio
        group = await self.modifiers_repo.get_modifier_group_by_id(
            modifier.modifier_group_id,
            current_user.business_id,
        )
        if not group:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="El modificador no pertenece a tu negocio.",
            )

        # Validar nombre único en el grupo si se está cambiando
        if data.name and data.name != modifier.name:
            if await self.modifiers_repo.modifier_name_exists_in_group(
                data.name,
                modifier.modifier_group_id,
                exclude_id=modifier.id,
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"El nombre '{data.name}' ya existe en el grupo '{group.name}'.",
                )

        # Registrar cambios para auditoría
        changes = []
        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            old_value = getattr(modifier, field)
            if value != old_value:
                setattr(modifier, field, value)
                changes.append(f"{field}: '{old_value}' → '{value}'")

        # Solo actualizar si hay cambios
        if changes:
            updated_modifier = await self.modifiers_repo.update_modifier(modifier)

            # Registrar auditoría
            await self.audit_repo.create_log(
                business_id=current_user.business_id,
                user_id=current_user.id,
                action=f"Modificador actualizado: {updated_modifier.name} (ID: {updated_modifier.id}). Cambios: {', '.join(changes)}. Actualizado por {current_user.full_name}",
            )

            return self._build_modifier_response(updated_modifier)

        return self._build_modifier_response(modifier)

    # ============= PRODUCT MODIFIER METHODS =============

    async def assign_modifier_to_product(
        self,
        product_id: int,
        data: ProductModifierAssign,
        current_user: User,
    ) -> ProductModifierResponse:
        """
        Asigna un modificador a un producto.

        VALIDACIÓN CRÍTICA: Todos los inventory_item_id del modificador
        deben existir en los ingredientes del producto.

        Args:
            product_id: ID del producto
            data: ID del modificador
            current_user: Usuario que asigna

        Returns:
            ProductModifierResponse
        """
        # Validar que el usuario sea OWNER, ADMIN o COOK
        if current_user.role not in [UserRole.OWNER, UserRole.ADMIN, UserRole.COOK]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo los roles OWNER, ADMIN y COOK pueden asignar modificadores.",
            )

        # Validar que el producto exista y pertenezca al negocio
        product = await self.products_repo.get_by_id(product_id, current_user.business_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Producto no encontrado.",
            )

        # Validar que el modificador exista
        modifier = await self.modifiers_repo.get_modifier_by_id(data.modifier_id)
        if not modifier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Modificador no encontrado.",
            )

        # Validar que el modificador pertenezca al negocio
        group = await self.modifiers_repo.get_modifier_group_by_id(
            modifier.modifier_group_id,
            current_user.business_id,
        )
        if not group:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="El modificador no pertenece a tu negocio.",
            )

        # Validar que no esté ya asignado
        existing = await self.modifiers_repo.get_product_modifier(product_id, data.modifier_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El modificador ya está asignado a este producto.",
            )

        # VALIDACIÓN DE COMPATIBILIDAD
        # Obtener los inventory_item_id de los ingredientes del producto
        product_ingredient_ids = {ing.inventory_item_id for ing in product.ingredients}

        # Obtener los inventory_item_id del modificador
        modifier_item_ids = {item.inventory_item_id for item in modifier.inventory_items}

        # Validar que todos los ítems del modificador existan en los ingredientes del producto
        if not modifier_item_ids.issubset(product_ingredient_ids):
            missing_items = modifier_item_ids - product_ingredient_ids
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El modificador '{modifier.name}' no es compatible con el producto '{product.name}'. Los ingredientes del modificador deben existir en el producto.",
            )

        # Asignar el modificador
        product_modifier = await self.modifiers_repo.assign_modifier_to_product(
            product_id=product_id,
            modifier_id=data.modifier_id,
        )

        # Registrar auditoría
        await self.audit_repo.create_log(
            business_id=current_user.business_id,
            user_id=current_user.id,
            action=f"Modificador '{modifier.name}' asignado al producto '{product.name}' por {current_user.full_name}",
        )

        return ProductModifierResponse(
            id=product_modifier.id,
            product_id=product_modifier.product_id,
            modifier_id=product_modifier.modifier_id,
            modifier_name=modifier.name,
            modifier_group_name=modifier.modifier_group.name,
            price_extra=modifier.price_extra,
        )

    async def get_modifiers_for_product(
        self,
        product_id: int,
        current_user: User,
    ) -> List[ProductModifierResponse]:
        """Obtiene todos los modificadores asignados a un producto"""
        # Validar que el producto exista y pertenezca al negocio
        product = await self.products_repo.get_by_id(product_id, current_user.business_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Producto no encontrado.",
            )

        product_modifiers = await self.modifiers_repo.get_modifiers_for_product(product_id)

        return [
            ProductModifierResponse(
                id=pm.id,
                product_id=pm.product_id,
                modifier_id=pm.modifier_id,
                modifier_name=pm.modifier.name,
                modifier_group_name=pm.modifier.modifier_group.name,
                price_extra=pm.modifier.price_extra,
            )
            for pm in product_modifiers
        ]

    async def remove_modifier_from_product(
        self,
        product_id: int,
        modifier_id: int,
        current_user: User,
    ):
        """Desasigna un modificador de un producto"""
        # Validar que el usuario sea OWNER, ADMIN o COOK
        if current_user.role not in [UserRole.OWNER, UserRole.ADMIN, UserRole.COOK]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo los roles OWNER, ADMIN y COOK pueden desasignar modificadores.",
            )

        # Validar que el producto exista y pertenezca al negocio
        product = await self.products_repo.get_by_id(product_id, current_user.business_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Producto no encontrado.",
            )

        # Validar que el modificador esté asignado
        existing = await self.modifiers_repo.get_product_modifier(product_id, modifier_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="El modificador no está asignado a este producto.",
            )

        # Obtener el modificador para auditoría
        modifier = await self.modifiers_repo.get_modifier_by_id(modifier_id)

        # Desasignar
        await self.modifiers_repo.remove_modifier_from_product(product_id, modifier_id)

        # Registrar auditoría
        await self.audit_repo.create_log(
            business_id=current_user.business_id,
            user_id=current_user.id,
            action=f"Modificador '{modifier.name}' desasignado del producto '{product.name}' por {current_user.full_name}",
        )

    # ============= HELPER METHODS =============

    def _build_modifier_response(self, modifier) -> ModifierResponse:
        """Construye la respuesta completa del modificador con ítems"""
        items_response = [
            ModifierInventoryItemResponse(
                id=item.id,
                modifier_id=item.modifier_id,
                inventory_item_id=item.inventory_item_id,
                inventory_item_name=item.inventory_item.name,
                quantity=item.quantity,
            )
            for item in modifier.inventory_items
        ]

        return ModifierResponse(
            id=modifier.id,
            modifier_group_id=modifier.modifier_group_id,
            modifier_group_name=modifier.modifier_group.name,
            name=modifier.name,
            description=modifier.description,
            price_extra=modifier.price_extra,
            is_active=modifier.is_active,
            created_at=modifier.created_at,
            updated_at=modifier.updated_at,
            inventory_items=items_response,
        )

    def _build_modifier_list_response(self, modifier) -> ModifierListResponse:
        """Construye la respuesta resumida del modificador sin ítems"""
        return ModifierListResponse(
            id=modifier.id,
            modifier_group_id=modifier.modifier_group_id,
            modifier_group_name=modifier.modifier_group.name,
            name=modifier.name,
            price_extra=modifier.price_extra,
            is_active=modifier.is_active,
            items_count=len(modifier.inventory_items),
        )
