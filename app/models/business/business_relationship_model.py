"""
Modelo BusinessRelationship (Relación entre Negocios).
Permite traslados de inventario entre negocios relacionados.
"""
from sqlalchemy import Column, Integer, DateTime, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.config.database import Base
from app.models.inventory.inventory_enums import RelationshipStatus


class BusinessRelationship(Base):
    """
    Modelo BusinessRelationship (Relación entre Negocios).
    Permite establecer relaciones entre negocios para traslados de inventario.
    Solo OWNER puede crear, aceptar o rechazar relaciones.
    """
    __tablename__ = "business_relationships"

    id = Column(Integer, primary_key=True, index=True)
    requester_business_id = Column(Integer, ForeignKey("business.id", ondelete="CASCADE"), nullable=False, index=True)
    target_business_id = Column(Integer, ForeignKey("business.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(Enum(RelationshipStatus), nullable=False, default=RelationshipStatus.PENDING, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Constraints
    __table_args__ = (
        UniqueConstraint('requester_business_id', 'target_business_id', name='uq_business_relationship'),
    )

    # Relationships
    requester_business = relationship("Business", foreign_keys=[requester_business_id], back_populates="outgoing_relationships")
    target_business = relationship("Business", foreign_keys=[target_business_id], back_populates="incoming_relationships")

    def __repr__(self):
        return f"<BusinessRelationship(id={self.id}, requester={self.requester_business_id}, target={self.target_business_id}, status={self.status})>"
