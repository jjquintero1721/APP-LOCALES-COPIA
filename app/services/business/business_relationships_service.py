"""
Servicio de Relaciones entre Negocios.
Maneja operaciones CRUD de relaciones entre negocios con validaciones y auditoría.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from typing import List
from app.repositories.business.business_relationships_repository import BusinessRelationshipsRepository
from app.repositories.business.business_repository import BusinessRepository
from app.repositories.audit.audit_repository import AuditRepository
from app.schemas.business.business_relationship_schema import (
    RelationshipCreateRequest,
    RelationshipResponse,
)
from app.models.users.user_model import User, UserRole
from app.models.inventory.inventory_enums import RelationshipStatus


class BusinessRelationshipsService:
    """
    Servicio de relaciones entre negocios.
    Maneja operaciones de relaciones con validaciones y auditoría completa.
    Solo OWNER puede crear, aceptar o rechazar relaciones.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.relationships_repo = BusinessRelationshipsRepository(db)
        self.business_repo = BusinessRepository(db)
        self.audit_repo = AuditRepository(db)

    async def create_relationship_request(
        self,
        data: RelationshipCreateRequest,
        current_user: User,
    ) -> RelationshipResponse:
        """
        Crea una solicitud de relación entre negocios.

        Validaciones:
        - Solo OWNER puede crear relaciones
        - No puede relacionarse consigo mismo
        - El negocio destino debe existir
        - No debe existir ya una relación entre los dos negocios

        Args:
            data: Datos de la solicitud (target_business_id)
            current_user: Usuario que crea la solicitud (OWNER)

        Returns:
            RelationshipResponse con los datos de la relación creada
        """
        # Validar que el usuario sea OWNER
        if current_user.role != UserRole.OWNER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo el OWNER puede crear solicitudes de relación entre negocios.",
            )

        # Validar que no se relacione consigo mismo
        if data.target_business_id == current_user.business_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No puedes crear una relación con tu propio negocio.",
            )

        # Validar que el negocio destino exista
        target_business = await self.business_repo.get_by_id(data.target_business_id)
        if not target_business:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"El negocio con ID {data.target_business_id} no existe.",
            )

        # Validar que no exista ya una relación
        existing_relationship = await self.relationships_repo.get_by_businesses(
            business_id_1=current_user.business_id,
            business_id_2=data.target_business_id,
        )
        if existing_relationship:
            status_messages = {
                RelationshipStatus.PENDING: "Ya existe una solicitud de relación pendiente entre estos negocios.",
                RelationshipStatus.ACTIVE: "Ya existe una relación activa entre estos negocios.",
                RelationshipStatus.REJECTED: "Existe una relación rechazada entre estos negocios. Contacta al administrador.",
            }
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=status_messages.get(
                    existing_relationship.status,
                    "Ya existe una relación entre estos negocios.",
                ),
            )

        # Crear la relación
        relationship = await self.relationships_repo.create(
            requester_business_id=current_user.business_id,
            target_business_id=data.target_business_id,
        )

        # Registrar auditoría en el negocio solicitante
        requester_business = await self.business_repo.get_by_id(current_user.business_id)
        await self.audit_repo.create_log(
            business_id=current_user.business_id,
            user_id=current_user.id,
            action=f"Solicitud de relación enviada al negocio '{target_business.name}' (ID: {target_business.id}) por {current_user.full_name}",
        )

        # Registrar auditoría en el negocio destino
        await self.audit_repo.create_log(
            business_id=data.target_business_id,
            user_id=current_user.id,
            action=f"Solicitud de relación recibida del negocio '{requester_business.name}' (ID: {requester_business.id})",
        )

        # Cargar la relación con los negocios para construir la respuesta
        relationship_with_businesses = await self.relationships_repo.get_by_id(relationship.id)

        return self._build_response(relationship_with_businesses)

    async def accept_relationship(
        self,
        relationship_id: int,
        current_user: User,
    ) -> RelationshipResponse:
        """
        Acepta una solicitud de relación.

        Validaciones:
        - Solo OWNER puede aceptar relaciones
        - La relación debe existir
        - El usuario debe ser el OWNER del negocio destino
        - La relación debe estar en estado PENDING

        Args:
            relationship_id: ID de la relación a aceptar
            current_user: Usuario que acepta la solicitud (OWNER del negocio destino)

        Returns:
            RelationshipResponse con los datos de la relación actualizada
        """
        # Validar que el usuario sea OWNER
        if current_user.role != UserRole.OWNER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo el OWNER puede aceptar solicitudes de relación.",
            )

        # Obtener la relación
        relationship = await self.relationships_repo.get_by_id(relationship_id)
        if not relationship:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Relación no encontrada.",
            )

        # Validar que el usuario sea el OWNER del negocio destino
        if relationship.target_business_id != current_user.business_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo el OWNER del negocio destino puede aceptar esta relación.",
            )

        # Validar que esté en estado PENDING
        if relationship.status != RelationshipStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No se puede aceptar una relación en estado {relationship.status.value}.",
            )

        # Actualizar estado
        updated_relationship = await self.relationships_repo.update_status(
            relationship=relationship,
            new_status=RelationshipStatus.ACTIVE,
        )

        # Registrar auditoría en ambos negocios
        await self.audit_repo.create_log(
            business_id=relationship.target_business_id,
            user_id=current_user.id,
            action=f"Relación aceptada con el negocio '{relationship.requester_business.name}' (ID: {relationship.requester_business_id}) por {current_user.full_name}",
        )

        await self.audit_repo.create_log(
            business_id=relationship.requester_business_id,
            user_id=current_user.id,
            action=f"Relación aceptada por el negocio '{relationship.target_business.name}' (ID: {relationship.target_business_id})",
        )

        return self._build_response(updated_relationship)

    async def reject_relationship(
        self,
        relationship_id: int,
        current_user: User,
    ) -> RelationshipResponse:
        """
        Rechaza una solicitud de relación.

        Validaciones:
        - Solo OWNER puede rechazar relaciones
        - La relación debe existir
        - El usuario debe ser el OWNER del negocio destino
        - La relación debe estar en estado PENDING

        Args:
            relationship_id: ID de la relación a rechazar
            current_user: Usuario que rechaza la solicitud (OWNER del negocio destino)

        Returns:
            RelationshipResponse con los datos de la relación actualizada
        """
        # Validar que el usuario sea OWNER
        if current_user.role != UserRole.OWNER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo el OWNER puede rechazar solicitudes de relación.",
            )

        # Obtener la relación
        relationship = await self.relationships_repo.get_by_id(relationship_id)
        if not relationship:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Relación no encontrada.",
            )

        # Validar que el usuario sea el OWNER del negocio destino
        if relationship.target_business_id != current_user.business_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo el OWNER del negocio destino puede rechazar esta relación.",
            )

        # Validar que esté en estado PENDING
        if relationship.status != RelationshipStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No se puede rechazar una relación en estado {relationship.status.value}.",
            )

        # Actualizar estado
        updated_relationship = await self.relationships_repo.update_status(
            relationship=relationship,
            new_status=RelationshipStatus.REJECTED,
        )

        # Registrar auditoría en ambos negocios
        await self.audit_repo.create_log(
            business_id=relationship.target_business_id,
            user_id=current_user.id,
            action=f"Relación rechazada con el negocio '{relationship.requester_business.name}' (ID: {relationship.requester_business_id}) por {current_user.full_name}",
        )

        await self.audit_repo.create_log(
            business_id=relationship.requester_business_id,
            user_id=current_user.id,
            action=f"Relación rechazada por el negocio '{relationship.target_business.name}' (ID: {relationship.target_business_id})",
        )

        return self._build_response(updated_relationship)

    async def get_pending_requests(
        self,
        current_user: User,
    ) -> List[RelationshipResponse]:
        """
        Obtiene las solicitudes de relación pendientes recibidas por el negocio.

        Args:
            current_user: Usuario actual (OWNER)

        Returns:
            Lista de RelationshipResponse con las solicitudes pendientes
        """
        # Validar que el usuario sea OWNER
        if current_user.role != UserRole.OWNER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo el OWNER puede ver las solicitudes de relación.",
            )

        relationships = await self.relationships_repo.get_pending_for_business(
            business_id=current_user.business_id,
        )

        return [self._build_response(rel) for rel in relationships]

    async def get_active_relationships(
        self,
        current_user: User,
    ) -> List[RelationshipResponse]:
        """
        Obtiene las relaciones activas del negocio.

        Args:
            current_user: Usuario actual (OWNER)

        Returns:
            Lista de RelationshipResponse con las relaciones activas
        """
        # Validar que el usuario sea OWNER
        if current_user.role != UserRole.OWNER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo el OWNER puede ver las relaciones activas.",
            )

        relationships = await self.relationships_repo.get_active_for_business(
            business_id=current_user.business_id,
        )

        return [self._build_response(rel) for rel in relationships]

    def _build_response(self, relationship) -> RelationshipResponse:
        """
        Construye la respuesta con los nombres de los negocios.

        Args:
            relationship: Objeto BusinessRelationship con los negocios cargados

        Returns:
            RelationshipResponse con los datos completos
        """
        return RelationshipResponse(
            id=relationship.id,
            requester_business_id=relationship.requester_business_id,
            requester_business_name=relationship.requester_business.name,
            target_business_id=relationship.target_business_id,
            target_business_name=relationship.target_business.name,
            status=relationship.status,
            created_at=relationship.created_at,
            updated_at=relationship.updated_at,
        )
