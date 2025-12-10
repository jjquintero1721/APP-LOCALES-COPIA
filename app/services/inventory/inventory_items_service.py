"""
Servicio de Ítems de Inventario.
Maneja operaciones CRUD de ítems con validaciones y auditoría.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from typing import List, Optional
from decimal import Decimal
from app.repositories.inventory.inventory_items_repository import InventoryItemsRepository
from app.repositories.inventory.inventory_movements_repository import InventoryMovementsRepository
from app.repositories.suppliers.suppliers_repository import SuppliersRepository
from app.repositories.audit.audit_repository import AuditRepository
from app.schemas.inventory.inventory_item_schema import (
    InventoryItemCreate,
    InventoryItemUpdate,
    InventoryItemResponse,
    StockAdjustmentRequest,
)
from app.models.users.user_model import User, UserRole
from app.models.inventory.inventory_enums import MovementType


class InventoryItemsService:
    """
    Servicio de ítems de inventario.
    Maneja operaciones CRUD de ítems con validaciones y auditoría completa.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.items_repo = InventoryItemsRepository(db)
        self.movements_repo = InventoryMovementsRepository(db)
        self.suppliers_repo = SuppliersRepository(db)
        self.audit_repo = AuditRepository(db)

    def _calculate_is_below_min_stock(self, quantity: Decimal, min_stock: Optional[Decimal]) -> bool:
        """Calcular si el ítem está por debajo del stock mínimo"""
        if min_stock is None:
            return False
        return quantity < min_stock

    async def create_item(
        self,
        data: InventoryItemCreate,
        current_user: User,
    ) -> InventoryItemResponse:
        """
        Crea un nuevo ítem de inventario.

        Validaciones:
        - Solo OWNER y ADMIN pueden crear ítems
        - SKU único por negocio (si se proporciona)
        - Supplier debe existir y pertenecer al negocio (si se proporciona)
        - min_stock <= max_stock

        Args:
            data: Datos del ítem a crear
            current_user: Usuario que crea el ítem

        Returns:
            InventoryItemResponse con los datos del ítem creado
        """
        # Validar que el usuario sea OWNER o ADMIN
        if current_user.role not in [UserRole.OWNER, UserRole.ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo los roles OWNER y ADMIN pueden crear ítems de inventario.",
            )

        # Validar SKU único (si se proporciona)
        if data.sku:
            if await self.items_repo.sku_exists(data.sku, current_user.business_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"El SKU {data.sku} ya está registrado en este negocio.",
                )

        # Validar supplier (si se proporciona)
        if data.supplier_id:
            supplier = await self.suppliers_repo.get_by_id(data.supplier_id, current_user.business_id)
            if not supplier:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Proveedor no encontrado o no pertenece a este negocio.",
                )
            if not supplier.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El proveedor está inactivo.",
                )

        # Crear el ítem
        item = await self.items_repo.create(
            business_id=current_user.business_id,
            name=data.name,
            category=data.category,
            unit_of_measure=data.unit_of_measure,
            sku=data.sku,
            quantity_in_stock=data.quantity_in_stock,
            min_stock=data.min_stock,
            max_stock=data.max_stock,
            unit_price=data.unit_price,
            tax_percentage=data.tax_percentage,
            include_tax=data.include_tax,
            supplier_id=data.supplier_id,
        )

        # Registrar auditoría
        supplier_info = f" (Proveedor: {supplier.name})" if data.supplier_id else ""
        await self.audit_repo.create_log(
            business_id=current_user.business_id,
            user_id=current_user.id,
            action=f"Ítem de inventario creado: {item.name} (ID: {item.id}, Stock inicial: {item.quantity_in_stock} {item.unit_of_measure}){supplier_info} por {current_user.full_name}",
        )

        # Preparar respuesta
        response = InventoryItemResponse.model_validate(item)
        response.supplier_name = supplier.name if data.supplier_id and supplier else None
        response.is_below_min_stock = self._calculate_is_below_min_stock(
            item.quantity_in_stock, item.min_stock
        )

        return response

    async def get_item_by_id(
        self,
        item_id: int,
        current_user: User,
    ) -> InventoryItemResponse:
        """Obtiene un ítem por ID"""
        item = await self.items_repo.get_by_id(item_id, current_user.business_id)

        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ítem de inventario no encontrado.",
            )

        response = InventoryItemResponse.model_validate(item)
        response.supplier_name = item.supplier.name if item.supplier else None
        response.is_below_min_stock = self._calculate_is_below_min_stock(
            item.quantity_in_stock, item.min_stock
        )

        return response

    async def get_all_items(
        self,
        current_user: User,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = False,
        category: Optional[str] = None,
        supplier_id: Optional[int] = None,
    ) -> List[InventoryItemResponse]:
        """Obtiene todos los ítems del negocio con filtros"""
        items = await self.items_repo.get_all_by_business(
            business_id=current_user.business_id,
            skip=skip,
            limit=limit,
            active_only=active_only,
            category=category,
            supplier_id=supplier_id,
        )

        responses = []
        for item in items:
            response = InventoryItemResponse.model_validate(item)
            response.supplier_name = item.supplier.name if item.supplier else None
            response.is_below_min_stock = self._calculate_is_below_min_stock(
                item.quantity_in_stock, item.min_stock
            )
            responses.append(response)

        return responses

    async def update_item(
        self,
        item_id: int,
        data: InventoryItemUpdate,
        current_user: User,
    ) -> InventoryItemResponse:
        """Actualiza un ítem existente (solo metadatos, no stock)"""
        # Validar que el usuario sea OWNER o ADMIN
        if current_user.role not in [UserRole.OWNER, UserRole.ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo los roles OWNER y ADMIN pueden actualizar ítems de inventario.",
            )

        # Obtener el ítem
        item = await self.items_repo.get_by_id(item_id, current_user.business_id)

        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ítem de inventario no encontrado.",
            )

        # Validar SKU único (si se proporciona y cambió)
        if data.sku and data.sku != item.sku:
            if await self.items_repo.sku_exists(data.sku, current_user.business_id, exclude_id=item_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"El SKU {data.sku} ya está registrado en este negocio.",
                )

        # Validar supplier (si se proporciona y cambió)
        supplier = None
        if data.supplier_id and data.supplier_id != item.supplier_id:
            supplier = await self.suppliers_repo.get_by_id(data.supplier_id, current_user.business_id)
            if not supplier:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Proveedor no encontrado o no pertenece a este negocio.",
                )
            if not supplier.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El proveedor está inactivo.",
                )

        # Registrar cambios para auditoría
        changes = []
        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            old_value = getattr(item, field)
            if value != old_value:
                setattr(item, field, value)
                changes.append(f"{field}: '{old_value}' → '{value}'")

        # Solo actualizar si hay cambios
        if changes:
            # Validar min_stock <= max_stock si ambos fueron actualizados
            if item.min_stock is not None and item.max_stock is not None:
                if item.max_stock < item.min_stock:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="max_stock debe ser mayor o igual que min_stock.",
                    )

            updated_item = await self.items_repo.update(item)

            # Registrar auditoría
            await self.audit_repo.create_log(
                business_id=current_user.business_id,
                user_id=current_user.id,
                action=f"Ítem de inventario actualizado: {updated_item.name} (ID: {updated_item.id}). Cambios: {', '.join(changes)}. Actualizado por {current_user.full_name}",
            )

            # Recargar con relaciones
            item = await self.items_repo.get_by_id(item_id, current_user.business_id)

        response = InventoryItemResponse.model_validate(item)
        response.supplier_name = item.supplier.name if item.supplier else None
        response.is_below_min_stock = self._calculate_is_below_min_stock(
            item.quantity_in_stock, item.min_stock
        )

        return response

    async def deactivate_item(
        self,
        item_id: int,
        current_user: User,
    ) -> InventoryItemResponse:
        """Inactiva un ítem de inventario (soft delete)"""
        # Validar que el usuario sea OWNER o ADMIN
        if current_user.role not in [UserRole.OWNER, UserRole.ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo los roles OWNER y ADMIN pueden inactivar ítems de inventario.",
            )

        # Obtener el ítem
        item = await self.items_repo.get_by_id(item_id, current_user.business_id)

        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ítem de inventario no encontrado.",
            )

        if not item.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El ítem ya está inactivo.",
            )

        # Inactivar
        item.is_active = False
        updated_item = await self.items_repo.update(item)

        # Registrar auditoría
        await self.audit_repo.create_log(
            business_id=current_user.business_id,
            user_id=current_user.id,
            action=f"Ítem de inventario inactivado: {updated_item.name} (ID: {updated_item.id}) por {current_user.full_name}",
        )

        response = InventoryItemResponse.model_validate(updated_item)
        response.supplier_name = updated_item.supplier.name if updated_item.supplier else None
        response.is_below_min_stock = self._calculate_is_below_min_stock(
            updated_item.quantity_in_stock, updated_item.min_stock
        )

        return response

    async def get_low_stock_alerts(
        self,
        current_user: User,
    ) -> List[InventoryItemResponse]:
        """Obtiene ítems con stock por debajo del mínimo"""
        items = await self.items_repo.get_items_below_min_stock(current_user.business_id)

        responses = []
        for item in items:
            response = InventoryItemResponse.model_validate(item)
            response.supplier_name = item.supplier.name if item.supplier else None
            response.is_below_min_stock = True  # Ya sabemos que está bajo el mínimo
            responses.append(response)

        return responses

    async def adjust_stock_manually(
        self,
        item_id: int,
        data: StockAdjustmentRequest,
        current_user: User,
    ) -> InventoryItemResponse:
        """
        Ajusta el stock de un ítem manualmente (entrada o salida).
        Crea un movimiento MANUAL_IN o MANUAL_OUT según el signo de quantity_change.

        Validaciones:
        - Solo OWNER y ADMIN pueden ajustar stock
        - El stock resultante no puede ser negativo
        - El motivo es obligatorio

        Args:
            item_id: ID del ítem a ajustar
            data: Datos del ajuste (quantity_change y reason)
            current_user: Usuario que realiza el ajuste

        Returns:
            InventoryItemResponse con el stock actualizado
        """
        # Validar que el usuario sea OWNER o ADMIN
        if current_user.role not in [UserRole.OWNER, UserRole.ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo los roles OWNER y ADMIN pueden ajustar el stock manualmente.",
            )

        # Obtener el ítem
        item = await self.items_repo.get_by_id(item_id, current_user.business_id)

        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ítem de inventario no encontrado.",
            )

        if not item.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se puede ajustar el stock de un ítem inactivo.",
            )

        # Calcular nuevo stock
        new_stock = item.quantity_in_stock + data.quantity_change

        if new_stock < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stock insuficiente. Stock actual: {item.quantity_in_stock} {item.unit_of_measure}, cambio solicitado: {data.quantity_change}. Stock resultante sería negativo.",
            )

        # Determinar tipo de movimiento
        movement_type = MovementType.MANUAL_IN if data.quantity_change > 0 else MovementType.MANUAL_OUT

        # Crear movimiento
        await self.movements_repo.create(
            inventory_item_id=item_id,
            business_id=current_user.business_id,
            created_by_user_id=current_user.id,
            movement_type=movement_type.value,
            quantity=data.quantity_change,
            reason=data.reason,
        )

        # Actualizar stock
        updated_item = await self.items_repo.update_stock(item, new_stock)

        # Registrar auditoría
        action_type = "Entrada manual" if data.quantity_change > 0 else "Salida manual"
        await self.audit_repo.create_log(
            business_id=current_user.business_id,
            user_id=current_user.id,
            action=f"{action_type} de stock: {updated_item.name} (ID: {updated_item.id}). Cantidad: {abs(data.quantity_change)} {updated_item.unit_of_measure}. Stock anterior: {item.quantity_in_stock}, Stock nuevo: {new_stock}. Motivo: {data.reason}. Por {current_user.full_name}",
        )

        # Preparar respuesta
        response = InventoryItemResponse.model_validate(updated_item)
        response.supplier_name = updated_item.supplier.name if updated_item.supplier else None
        response.is_below_min_stock = self._calculate_is_below_min_stock(
            updated_item.quantity_in_stock, updated_item.min_stock
        )

        return response
