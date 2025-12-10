from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.config.database import Base


class Business(Base):
    """
    Modelo Business (Negocio).
    Representa un tenant en el sistema multi-tenant.
    """

    __tablename__ = "business"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    users = relationship("User", back_populates="business", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="business", cascade="all, delete-orphan")
    attendance_records = relationship("Attendance", back_populates="business", cascade="all, delete-orphan")

    # Inventory
    suppliers = relationship("Supplier", back_populates="business", cascade="all, delete-orphan")
    inventory_items = relationship("InventoryItem", back_populates="business", cascade="all, delete-orphan")
    inventory_movements = relationship("InventoryMovement", back_populates="business", cascade="all, delete-orphan")

    # Business Relationships
    outgoing_relationships = relationship(
        "BusinessRelationship",
        foreign_keys="[BusinessRelationship.requester_business_id]",
        back_populates="requester_business"
    )
    incoming_relationships = relationship(
        "BusinessRelationship",
        foreign_keys="[BusinessRelationship.target_business_id]",
        back_populates="target_business"
    )

    # Transfers
    outgoing_transfers = relationship(
        "InventoryTransfer",
        foreign_keys="[InventoryTransfer.from_business_id]",
        back_populates="from_business"
    )
    incoming_transfers = relationship(
        "InventoryTransfer",
        foreign_keys="[InventoryTransfer.to_business_id]",
        back_populates="to_business"
    )

    # Products
    products = relationship("Product", back_populates="business", cascade="all, delete-orphan")

    # Modifiers
    modifier_groups = relationship("ModifierGroup", back_populates="business", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Business(id={self.id}, name='{self.name}')>"
