"""
Controller para Relaciones entre Negocios.
Capa delgada que delega al servicio de relaciones entre negocios.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.services.business.business_relationships_service import BusinessRelationshipsService
from app.schemas.business.business_relationship_schema import (
    RelationshipCreateRequest,
    RelationshipResponse,
)
from app.models.users.user_model import User


class BusinessRelationshipsController:
    """
    Controller para gestionar endpoints de relaciones entre negocios.
    """

    @staticmethod
    async def create_relationship_request(
        data: RelationshipCreateRequest,
        current_user: User,
        db: AsyncSession,
    ) -> RelationshipResponse:
        """Crear una solicitud de relación entre negocios"""
        service = BusinessRelationshipsService(db)
        return await service.create_relationship_request(data, current_user)

    @staticmethod
    async def accept_relationship(
        relationship_id: int,
        current_user: User,
        db: AsyncSession,
    ) -> RelationshipResponse:
        """Aceptar una solicitud de relación"""
        service = BusinessRelationshipsService(db)
        return await service.accept_relationship(relationship_id, current_user)

    @staticmethod
    async def reject_relationship(
        relationship_id: int,
        current_user: User,
        db: AsyncSession,
    ) -> RelationshipResponse:
        """Rechazar una solicitud de relación"""
        service = BusinessRelationshipsService(db)
        return await service.reject_relationship(relationship_id, current_user)

    @staticmethod
    async def get_pending_requests(
        current_user: User,
        db: AsyncSession,
    ) -> List[RelationshipResponse]:
        """Obtener solicitudes de relación pendientes recibidas"""
        service = BusinessRelationshipsService(db)
        return await service.get_pending_requests(current_user)

    @staticmethod
    async def get_active_relationships(
        current_user: User,
        db: AsyncSession,
    ) -> List[RelationshipResponse]:
        """Obtener relaciones activas del negocio"""
        service = BusinessRelationshipsService(db)
        return await service.get_active_relationships(current_user)
