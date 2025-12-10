"""
Servicio de Movimientos de Inventario.
Maneja operaciones de movimientos con validaciones y auditoría.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from typing import List, Optional
from decimal import Decimal
from app.repositories.inventory.inventory_movements_repository import InventoryMovementsRepository
from app.repositories.inventory.inventory_items_repository import InventoryItemsRepository
from app.repositories.audit.audit_repository import AuditRepository
from app.schemas.inventory.inventory_movement_schema import (
    MovementResponse,
    RevertMovementRequest,
)
from app.models.users.user_model import User, UserRole
from app.models.inventory.inventory_enums import MovementType


class InventoryMovementsService:
    """
    Servicio de movimientos de inventario.
    Maneja operaciones de movimientos con validaciones y auditoría completa.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.movements_repo = InventoryMovementsRepository(db)
        self.items_repo = InventoryItemsRepository(db)
        self.audit_repo = AuditRepository(db)

    async def create_movement(
        self,
        inventory_item_id: int,
        business_id: int,
        created_by_user_id: Optional[int],
        movement_type: MovementType,
        quantity: Decimal,
        reason: Optional[str] = None,
        reference_id: Optional[int] = None,
    ) -> MovementResponse:
        """
        Crea un nuevo movimiento de inventario.
        Método interno usado por otros servicios.

        Args:
            inventory_item_id: ID del ítem
            business_id: ID del negocio
            created_by_user_id: ID del usuario que crea el movimiento
            movement_type: Tipo de movimiento
            quantity: Cantidad (positiva o negativa)
            reason: Motivo (obligatorio para movimientos manuales)
            reference_id: ID de referencia (venta, traslado, etc.)

        Returns:
            MovementResponse con los datos del movimiento creado
        """
        # Validar que el ítem existe
        item = await self.items_repo.get_by_id(inventory_item_id, business_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ítem de inventario no encontrado.",
            )

        # Crear el movimiento
        movement = await self.movements_repo.create(
            inventory_item_id=inventory_item_id,
            business_id=business_id,
            created_by_user_id=created_by_user_id,
            movement_type=movement_type,
            quantity=quantity,
            reason=reason,
            reference_id=reference_id,
        )

        # Preparar respuesta
        response = MovementResponse.model_validate(movement)
        response.inventory_item_name = item.name
        response.created_by_user_name = movement.created_by.full_name if movement.created_by else None

        return response

    async def get_movement_by_id(
        self,
        movement_id: int,
        current_user: User,
    ) -> MovementResponse:
        """Obtiene un movimiento por ID"""
        movement = await self.movements_repo.get_by_id(movement_id, current_user.business_id)

        if not movement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Movimiento no encontrado.",
            )

        response = MovementResponse.model_validate(movement)
        response.inventory_item_name = movement.inventory_item.name if movement.inventory_item else "Desconocido"
        response.created_by_user_name = movement.created_by.full_name if movement.created_by else None

        return response

    async def get_movement_history_by_item(
        self,
        item_id: int,
        current_user: User,
        skip: int = 0,
        limit: int = 100,
    ) -> List[MovementResponse]:
        """Obtiene el historial de movimientos de un ítem específico"""
        # Verificar que el ítem existe y pertenece al negocio
        item = await self.items_repo.get_by_id(item_id, current_user.business_id)
        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ítem de inventario no encontrado.",
            )

        movements = await self.movements_repo.get_by_item(
            item_id=item_id,
            business_id=current_user.business_id,
            skip=skip,
            limit=limit,
        )

        responses = []
        for movement in movements:
            response = MovementResponse.model_validate(movement)
            response.inventory_item_name = item.name
            response.created_by_user_name = movement.created_by.full_name if movement.created_by else None
            responses.append(response)

        return responses

    async def get_all_movements(
        self,
        current_user: User,
        skip: int = 0,
        limit: int = 100,
        movement_type: Optional[MovementType] = None,
    ) -> List[MovementResponse]:
        """Obtiene todos los movimientos del negocio con filtros"""
        movements = await self.movements_repo.get_by_business(
            business_id=current_user.business_id,
            skip=skip,
            limit=limit,
            movement_type=movement_type,
        )

        responses = []
        for movement in movements:
            response = MovementResponse.model_validate(movement)
            response.inventory_item_name = movement.inventory_item.name if movement.inventory_item else "Desconocido"
            response.created_by_user_name = movement.created_by.full_name if movement.created_by else None
            responses.append(response)

        return responses

    async def revert_movement(
        self,
        movement_id: int,
        data: RevertMovementRequest,
        current_user: User,
    ) -> MovementResponse:
        """
        Revierte un movimiento creando un movimiento inverso.
        Solo OWNER puede revertir movimientos.

        Validaciones:
        - Solo OWNER puede revertir
        - No se puede revertir un movimiento ya revertido
        - El stock resultante no puede ser negativo

        Args:
            movement_id: ID del movimiento a revertir
            data: Datos con el motivo de la reversión
            current_user: Usuario que realiza la reversión

        Returns:
            MovementResponse del movimiento de reversión creado
        """
        # Solo OWNER puede revertir
        if current_user.role != UserRole.OWNER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo el OWNER puede revertir movimientos.",
            )

        # Obtener el movimiento original
        original_movement = await self.movements_repo.get_by_id(movement_id, current_user.business_id)

        if not original_movement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Movimiento no encontrado.",
            )

        # Validar que no esté ya revertido
        if original_movement.reverted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Este movimiento ya fue revertido.",
            )

        # Obtener el ítem para validar stock
        item = await self.items_repo.get_by_id(
            original_movement.inventory_item_id,
            current_user.business_id,
        )

        if not item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ítem de inventario no encontrado.",
            )

        # Calcular nuevo stock después de revertir
        new_stock = item.quantity_in_stock - original_movement.quantity

        if new_stock < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No se puede revertir: el stock resultante sería negativo ({new_stock} {item.unit_of_measure}).",
            )

        # Crear movimiento de reversión (cantidad inversa)
        reverting_movement = await self.movements_repo.create(
            inventory_item_id=original_movement.inventory_item_id,
            business_id=current_user.business_id,
            created_by_user_id=current_user.id,
            movement_type=MovementType.REVERT.value,
            quantity=-original_movement.quantity,  # Cantidad inversa
            reason=f"Reversión del movimiento #{original_movement.id}. Motivo: {data.reason}",
            reference_id=original_movement.id,
        )

        # Marcar el movimiento original como revertido
        await self.movements_repo.mark_as_reverted(original_movement, reverting_movement.id)

        # Actualizar el stock del ítem
        await self.items_repo.update_stock(item, new_stock)

        # Registrar auditoría
        await self.audit_repo.create_log(
            business_id=current_user.business_id,
            user_id=current_user.id,
            action=f"Movimiento revertido: {item.name} (Movimiento original #{original_movement.id}, tipo: {original_movement.movement_type.value}, cantidad: {original_movement.quantity}). Motivo: {data.reason}. Revertido por {current_user.full_name}",
        )

        # Preparar respuesta
        response = MovementResponse.model_validate(reverting_movement)
        response.inventory_item_name = item.name
        response.created_by_user_name = current_user.full_name

        return response
