"""
Repositorio para operaciones de BusinessRelationship en la base de datos.
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
from app.models.business.business_relationship_model import BusinessRelationship
from app.models.inventory.inventory_enums import RelationshipStatus


class BusinessRelationshipsRepository:
    """
    Repositorio para gestionar operaciones de BusinessRelationship.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        requester_business_id: int,
        target_business_id: int,
    ) -> BusinessRelationship:
        """Crear una nueva solicitud de relación"""
        relationship = BusinessRelationship(
            requester_business_id=requester_business_id,
            target_business_id=target_business_id,
            status=RelationshipStatus.PENDING,
        )
        self.db.add(relationship)
        await self.db.commit()
        await self.db.refresh(relationship)
        return relationship

    async def get_by_id(self, relationship_id: int) -> Optional[BusinessRelationship]:
        """Obtener relación por ID con joins"""
        result = await self.db.execute(
            select(BusinessRelationship)
            .options(
                selectinload(BusinessRelationship.requester_business),
                selectinload(BusinessRelationship.target_business),
            )
            .where(BusinessRelationship.id == relationship_id)
        )
        return result.scalar_one_or_none()

    async def get_by_businesses(
        self,
        business_id_1: int,
        business_id_2: int,
    ) -> Optional[BusinessRelationship]:
        """Buscar relación entre dos negocios (en cualquier dirección)"""
        result = await self.db.execute(
            select(BusinessRelationship).where(
                or_(
                    and_(
                        BusinessRelationship.requester_business_id == business_id_1,
                        BusinessRelationship.target_business_id == business_id_2,
                    ),
                    and_(
                        BusinessRelationship.requester_business_id == business_id_2,
                        BusinessRelationship.target_business_id == business_id_1,
                    ),
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_pending_for_business(self, business_id: int) -> List[BusinessRelationship]:
        """Obtener solicitudes de relación pendientes recibidas"""
        result = await self.db.execute(
            select(BusinessRelationship)
            .options(
                selectinload(BusinessRelationship.requester_business),
                selectinload(BusinessRelationship.target_business),
            )
            .where(
                and_(
                    BusinessRelationship.target_business_id == business_id,
                    BusinessRelationship.status == RelationshipStatus.PENDING,
                )
            )
            .order_by(BusinessRelationship.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_active_for_business(self, business_id: int) -> List[BusinessRelationship]:
        """Obtener relaciones activas para un negocio"""
        result = await self.db.execute(
            select(BusinessRelationship)
            .options(
                selectinload(BusinessRelationship.requester_business),
                selectinload(BusinessRelationship.target_business),
            )
            .where(
                and_(
                    or_(
                        BusinessRelationship.requester_business_id == business_id,
                        BusinessRelationship.target_business_id == business_id,
                    ),
                    BusinessRelationship.status == RelationshipStatus.ACTIVE,
                )
            )
            .order_by(BusinessRelationship.created_at.desc())
        )
        return list(result.scalars().all())

    async def update_status(
        self,
        relationship: BusinessRelationship,
        new_status: RelationshipStatus,
    ) -> BusinessRelationship:
        """Actualizar el estado de una relación"""
        relationship.status = new_status
        await self.db.commit()
        await self.db.refresh(relationship)
        return relationship
