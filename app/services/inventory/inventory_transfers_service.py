"""
Servicio de Traslados de Inventario.
Maneja operaciones de traslados de inventario entre negocios relacionados.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from typing import List
from decimal import Decimal
from app.repositories.inventory.inventory_transfers_repository import InventoryTransfersRepository
from app.repositories.inventory.inventory_items_repository import InventoryItemsRepository
from app.repositories.inventory.inventory_movements_repository import InventoryMovementsRepository
from app.repositories.business.business_relationships_repository import BusinessRelationshipsRepository
from app.repositories.business.business_repository import BusinessRepository
from app.repositories.audit.audit_repository import AuditRepository
from app.schemas.inventory.inventory_transfer_schema import (
    TransferCreate,
    TransferResponse,
    TransferListResponse,
    TransferItemResponse,
)
from app.models.users.user_model import User, UserRole
from app.models.inventory.inventory_enums import TransferStatus, RelationshipStatus, MovementType


class InventoryTransfersService:
    """
    Servicio de traslados de inventario.
    Maneja traslados entre negocios con validaciones y auditoría completa.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.transfers_repo = InventoryTransfersRepository(db)
        self.items_repo = InventoryItemsRepository(db)
        self.movements_repo = InventoryMovementsRepository(db)
        self.relationships_repo = BusinessRelationshipsRepository(db)
        self.business_repo = BusinessRepository(db)
        self.audit_repo = AuditRepository(db)

    async def create_transfer(
        self,
        data: TransferCreate,
        current_user: User,
    ) -> TransferResponse:
        """
        Crea un nuevo traslado de inventario.

        Validaciones:
        - Solo OWNER y ADMIN pueden crear traslados
        - Debe existir una relación ACTIVE entre los negocios
        - No puede trasladar al mismo negocio
        - Todos los ítems deben pertenecer al negocio origen
        - Debe haber stock suficiente en el negocio origen
        - No puede haber ítems duplicados en el traslado

        Args:
            data: Datos del traslado
            current_user: Usuario que crea el traslado

        Returns:
            TransferResponse con los datos del traslado creado
        """
        # Validar que el usuario sea OWNER o ADMIN
        if current_user.role not in [UserRole.OWNER, UserRole.ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo los roles OWNER y ADMIN pueden crear traslados de inventario.",
            )

        # Validar que no traslade al mismo negocio
        if data.to_business_id == current_user.business_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No puedes crear un traslado hacia tu propio negocio.",
            )

        # Validar que el negocio destino exista
        target_business = await self.business_repo.get_by_id(data.to_business_id)
        if not target_business:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"El negocio destino con ID {data.to_business_id} no existe.",
            )

        # Validar que exista una relación ACTIVE entre los negocios
        relationship = await self.relationships_repo.get_by_businesses(
            business_id_1=current_user.business_id,
            business_id_2=data.to_business_id,
        )
        if not relationship or relationship.status != RelationshipStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No existe una relación activa entre los negocios. Primero deben establecer una relación.",
            )

        # Validar todos los ítems y stock
        items_data = []
        for item_data in data.items:
            # Validar que el ítem exista y pertenezca al negocio origen
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
                    detail=f"El ítem '{item.name}' está inactivo.",
                )

            # Validar stock suficiente
            if item.quantity_in_stock < item_data.quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Stock insuficiente para '{item.name}'. Disponible: {item.quantity_in_stock}, Solicitado: {item_data.quantity}",
                )

            items_data.append({
                "inventory_item_id": item_data.inventory_item_id,
                "quantity": item_data.quantity,
                "notes": item_data.notes,
            })

        # Crear el traslado
        transfer = await self.transfers_repo.create_transfer(
            from_business_id=current_user.business_id,
            to_business_id=data.to_business_id,
            created_by_user_id=current_user.id,
            notes=data.notes,
            items=items_data,
        )

        # Registrar auditoría en el negocio origen
        origin_business = await self.business_repo.get_by_id(current_user.business_id)
        await self.audit_repo.create_log(
            business_id=current_user.business_id,
            user_id=current_user.id,
            action=f"Traslado de inventario creado hacia '{target_business.name}' (ID: {transfer.id}) por {current_user.full_name}. Estado: PENDING",
        )

        # Registrar auditoría en el negocio destino
        await self.audit_repo.create_log(
            business_id=data.to_business_id,
            user_id=current_user.id,
            action=f"Solicitud de traslado de inventario recibida desde '{origin_business.name}' (ID: {transfer.id}). Estado: PENDING",
        )

        # Cargar el traslado con todas las relaciones
        transfer_with_relations = await self.transfers_repo.get_by_id(transfer.id)

        return self._build_response(transfer_with_relations)

    async def accept_transfer(
        self,
        transfer_id: int,
        current_user: User,
    ) -> TransferResponse:
        """
        Acepta un traslado de inventario.

        Validaciones:
        - Solo OWNER y ADMIN del negocio destino pueden aceptar
        - El traslado debe estar en estado PENDING
        - Debe haber stock suficiente en el negocio origen (puede haber cambiado)

        Al aceptar:
        - Crea movimientos TRANSFER_OUT en el negocio origen
        - Crea movimientos TRANSFER_IN en el negocio destino
        - Actualiza el stock en ambos negocios
        - Cambia el estado a COMPLETED

        Args:
            transfer_id: ID del traslado
            current_user: Usuario que acepta el traslado

        Returns:
            TransferResponse con los datos del traslado actualizado
        """
        # Validar que el usuario sea OWNER o ADMIN
        if current_user.role not in [UserRole.OWNER, UserRole.ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo los roles OWNER y ADMIN pueden aceptar traslados.",
            )

        # Obtener el traslado
        transfer = await self.transfers_repo.get_by_id(transfer_id)
        if not transfer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Traslado no encontrado.",
            )

        # Validar que el usuario sea del negocio destino
        if transfer.to_business_id != current_user.business_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo el negocio destino puede aceptar este traslado.",
            )

        # Validar que esté en estado PENDING
        if transfer.status != TransferStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No se puede aceptar un traslado en estado {transfer.status.value}.",
            )

        # Validar nuevamente el stock (puede haber cambiado desde que se creó)
        for transfer_item in transfer.items:
            origin_item = await self.items_repo.get_by_id(
                transfer_item.inventory_item_id,
                transfer.from_business_id,
            )
            if not origin_item:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"El ítem con ID {transfer_item.inventory_item_id} ya no existe en el negocio origen.",
                )

            if origin_item.quantity_in_stock < transfer_item.quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Stock insuficiente para '{origin_item.name}' en el negocio origen. Disponible: {origin_item.quantity_in_stock}, Solicitado: {transfer_item.quantity}",
                )

        # Procesar el traslado
        for transfer_item in transfer.items:
            # Obtener el ítem en el negocio origen
            origin_item = await self.items_repo.get_by_id(
                transfer_item.inventory_item_id,
                transfer.from_business_id,
            )

            # Crear movimiento TRANSFER_OUT en el negocio origen
            await self.movements_repo.create(
                inventory_item_id=origin_item.id,
                business_id=transfer.from_business_id,
                created_by_user_id=current_user.id,
                movement_type=MovementType.TRANSFER_OUT,
                quantity=transfer_item.quantity,
                reason=f"Traslado a '{transfer.to_business.name}' (ID: {transfer.id})",
                reference_id=transfer.id,
            )

            # Actualizar stock en el negocio origen (reducir)
            origin_item.quantity_in_stock -= transfer_item.quantity
            await self.items_repo.update(origin_item)

            # Buscar o crear el ítem en el negocio destino
            # IMPORTANTE: Buscar por nombre y unidad de medida (o SKU si existe)
            dest_items = await self.items_repo.get_all_by_business(
                business_id=transfer.to_business_id,
                skip=0,
                limit=1000,
            )

            # Buscar ítem compatible (mismo nombre y unidad de medida)
            dest_item = None
            for item in dest_items:
                if (item.name == origin_item.name and
                    item.unit_of_measure == origin_item.unit_of_measure):
                    dest_item = item
                    break

            # Si no existe, crear el ítem en el negocio destino
            if not dest_item:
                dest_item = await self.items_repo.create(
                    business_id=transfer.to_business_id,
                    name=origin_item.name,
                    category=origin_item.category,
                    unit_of_measure=origin_item.unit_of_measure,
                    sku=None,  # No copiar SKU para evitar conflictos
                    quantity_in_stock=Decimal(0),
                    min_stock=origin_item.min_stock,
                    max_stock=origin_item.max_stock,
                    unit_price=origin_item.unit_price,
                    tax_percentage=origin_item.tax_percentage,
                    include_tax=origin_item.include_tax,
                    supplier_id=None,  # El proveedor puede no existir en el negocio destino
                )

            # Crear movimiento TRANSFER_IN en el negocio destino
            await self.movements_repo.create(
                inventory_item_id=dest_item.id,
                business_id=transfer.to_business_id,
                created_by_user_id=current_user.id,
                movement_type=MovementType.TRANSFER_IN,
                quantity=transfer_item.quantity,
                reason=f"Traslado desde '{transfer.from_business.name}' (ID: {transfer.id})",
                reference_id=transfer.id,
            )

            # Actualizar stock en el negocio destino (aumentar)
            dest_item.quantity_in_stock += transfer_item.quantity
            await self.items_repo.update(dest_item)

        # Actualizar estado del traslado
        updated_transfer = await self.transfers_repo.update_status(
            transfer=transfer,
            new_status=TransferStatus.COMPLETED,
        )

        # Registrar auditoría en ambos negocios
        await self.audit_repo.create_log(
            business_id=transfer.to_business_id,
            user_id=current_user.id,
            action=f"Traslado de inventario aceptado (ID: {transfer.id}) desde '{transfer.from_business.name}' por {current_user.full_name}. Estado: COMPLETED",
        )

        await self.audit_repo.create_log(
            business_id=transfer.from_business_id,
            user_id=current_user.id,
            action=f"Traslado de inventario completado (ID: {transfer.id}) hacia '{transfer.to_business.name}'. Estado: COMPLETED",
        )

        return self._build_response(updated_transfer)

    async def reject_transfer(
        self,
        transfer_id: int,
        current_user: User,
    ) -> TransferResponse:
        """
        Rechaza un traslado de inventario.

        Validaciones:
        - Solo OWNER y ADMIN del negocio destino pueden rechazar
        - El traslado debe estar en estado PENDING

        Args:
            transfer_id: ID del traslado
            current_user: Usuario que rechaza el traslado

        Returns:
            TransferResponse con los datos del traslado actualizado
        """
        # Validar que el usuario sea OWNER o ADMIN
        if current_user.role not in [UserRole.OWNER, UserRole.ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo los roles OWNER y ADMIN pueden rechazar traslados.",
            )

        # Obtener el traslado
        transfer = await self.transfers_repo.get_by_id(transfer_id)
        if not transfer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Traslado no encontrado.",
            )

        # Validar que el usuario sea del negocio destino
        if transfer.to_business_id != current_user.business_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo el negocio destino puede rechazar este traslado.",
            )

        # Validar que esté en estado PENDING
        if transfer.status != TransferStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No se puede rechazar un traslado en estado {transfer.status.value}.",
            )

        # Actualizar estado
        updated_transfer = await self.transfers_repo.update_status(
            transfer=transfer,
            new_status=TransferStatus.REJECTED,
        )

        # Registrar auditoría en ambos negocios
        await self.audit_repo.create_log(
            business_id=transfer.to_business_id,
            user_id=current_user.id,
            action=f"Traslado de inventario rechazado (ID: {transfer.id}) desde '{transfer.from_business.name}' por {current_user.full_name}. Estado: REJECTED",
        )

        await self.audit_repo.create_log(
            business_id=transfer.from_business_id,
            user_id=current_user.id,
            action=f"Traslado de inventario rechazado (ID: {transfer.id}) hacia '{transfer.to_business.name}'. Estado: REJECTED",
        )

        return self._build_response(updated_transfer)

    async def cancel_transfer(
        self,
        transfer_id: int,
        current_user: User,
    ) -> TransferResponse:
        """
        Cancela un traslado de inventario.

        Validaciones:
        - Solo OWNER y ADMIN del negocio origen pueden cancelar
        - El traslado debe estar en estado PENDING

        Args:
            transfer_id: ID del traslado
            current_user: Usuario que cancela el traslado

        Returns:
            TransferResponse con los datos del traslado actualizado
        """
        # Validar que el usuario sea OWNER o ADMIN
        if current_user.role not in [UserRole.OWNER, UserRole.ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo los roles OWNER y ADMIN pueden cancelar traslados.",
            )

        # Obtener el traslado
        transfer = await self.transfers_repo.get_by_id(transfer_id)
        if not transfer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Traslado no encontrado.",
            )

        # Validar que el usuario sea del negocio origen
        if transfer.from_business_id != current_user.business_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo el negocio origen puede cancelar este traslado.",
            )

        # Validar que esté en estado PENDING
        if transfer.status != TransferStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No se puede cancelar un traslado en estado {transfer.status.value}.",
            )

        # Cancelar el traslado
        updated_transfer = await self.transfers_repo.cancel_transfer(transfer)

        # Registrar auditoría en ambos negocios
        await self.audit_repo.create_log(
            business_id=transfer.from_business_id,
            user_id=current_user.id,
            action=f"Traslado de inventario cancelado (ID: {transfer.id}) hacia '{transfer.to_business.name}' por {current_user.full_name}. Estado: CANCELLED",
        )

        await self.audit_repo.create_log(
            business_id=transfer.to_business_id,
            user_id=current_user.id,
            action=f"Traslado de inventario cancelado (ID: {transfer.id}) desde '{transfer.from_business.name}'. Estado: CANCELLED",
        )

        return self._build_response(updated_transfer)

    async def get_transfer_by_id(
        self,
        transfer_id: int,
        current_user: User,
    ) -> TransferResponse:
        """
        Obtiene un traslado por ID.

        Validaciones:
        - El usuario debe pertenecer al negocio origen o destino

        Args:
            transfer_id: ID del traslado
            current_user: Usuario actual

        Returns:
            TransferResponse con los datos del traslado
        """
        transfer = await self.transfers_repo.get_by_id(transfer_id)

        if not transfer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Traslado no encontrado.",
            )

        # Validar que el usuario pertenezca al negocio origen o destino
        if (transfer.from_business_id != current_user.business_id and
            transfer.to_business_id != current_user.business_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para ver este traslado.",
            )

        return self._build_response(transfer)

    async def get_transfers(
        self,
        current_user: User,
        status_filter: str = None,
        direction: str = None,
    ) -> List[TransferListResponse]:
        """
        Obtiene todos los traslados del negocio.

        Args:
            current_user: Usuario actual
            status_filter: Filtro por estado (opcional)
            direction: "outgoing", "incoming", None (ambos)

        Returns:
            Lista de TransferListResponse
        """
        # Validar status_filter
        status_enum = None
        if status_filter:
            try:
                status_enum = TransferStatus(status_filter)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Estado inválido: {status_filter}",
                )

        transfers = await self.transfers_repo.get_transfers_for_business(
            business_id=current_user.business_id,
            status_filter=status_enum,
            direction=direction,
        )

        return [self._build_list_response(transfer) for transfer in transfers]

    def _build_response(self, transfer) -> TransferResponse:
        """Construye la respuesta completa del traslado con ítems"""
        items_response = [
            TransferItemResponse(
                id=item.id,
                transfer_id=item.transfer_id,
                inventory_item_id=item.inventory_item_id,
                inventory_item_name=item.inventory_item.name,
                quantity=item.quantity,
                notes=item.notes,
            )
            for item in transfer.items
        ]

        return TransferResponse(
            id=transfer.id,
            from_business_id=transfer.from_business_id,
            from_business_name=transfer.from_business.name,
            to_business_id=transfer.to_business_id,
            to_business_name=transfer.to_business.name,
            created_by_user_id=transfer.created_by_user_id,
            created_by_user_name=transfer.created_by.full_name if transfer.created_by else None,
            status=transfer.status,
            notes=transfer.notes,
            created_at=transfer.created_at,
            updated_at=transfer.updated_at,
            completed_at=transfer.completed_at,
            items=items_response,
        )

    def _build_list_response(self, transfer) -> TransferListResponse:
        """Construye la respuesta resumida del traslado sin ítems"""
        return TransferListResponse(
            id=transfer.id,
            from_business_id=transfer.from_business_id,
            from_business_name=transfer.from_business.name,
            to_business_id=transfer.to_business_id,
            to_business_name=transfer.to_business.name,
            status=transfer.status,
            items_count=len(transfer.items),
            created_at=transfer.created_at,
            completed_at=transfer.completed_at,
        )
