"""
Modelo InventoryMovement (Movimiento de Inventario).
Registra todos los cambios en el inventario.
"""
from sqlalchemy import Column, Integer, Numeric, Boolean, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.config.database import Base
from app.models.inventory.inventory_enums import MovementType


class InventoryMovement(Base):
    """
    Modelo InventoryMovement (Movimiento de Inventario).
    Registra todos los cambios en el inventario con auditoría completa.
    """
    __tablename__ = "inventory_movements"

    id = Column(Integer, primary_key=True, index=True)
    inventory_item_id = Column(Integer, ForeignKey("inventory_items.id", ondelete="CASCADE"), nullable=False, index=True)
    business_id = Column(Integer, ForeignKey("business.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    movement_type = Column(Enum(MovementType), nullable=False, index=True)
    quantity = Column(Numeric(10, 3), nullable=False)  # Puede ser positiva o negativa
    reason = Column(Text, nullable=True)  # Obligatorio para manual
    reference_id = Column(Integer, nullable=True, index=True)  # ID de venta/traslado/etc

    reverted = Column(Boolean, default=False, nullable=False)
    reverted_by_movement_id = Column(Integer, ForeignKey("inventory_movements.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    # Relationships
    inventory_item = relationship("InventoryItem", back_populates="movements")
    business = relationship("Business", back_populates="inventory_movements")
    created_by = relationship("User")
    reverting_movement = relationship("InventoryMovement", remote_side=[id], foreign_keys=[reverted_by_movement_id])

    def __repr__(self):
        return f"<InventoryMovement(id={self.id}, type={self.movement_type}, qty={self.quantity})>"
