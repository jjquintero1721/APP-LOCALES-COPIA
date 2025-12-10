"""
Modelos InventoryTransfer y TransferItem.
Representan los traslados de inventario entre negocios relacionados.
"""
from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Text, Enum, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.config.database import Base
from app.models.inventory.inventory_enums import TransferStatus


class InventoryTransfer(Base):
    """
    Modelo InventoryTransfer (Traslado de Inventario).
    Representa un traslado de ítems de inventario entre dos negocios relacionados.
    """
    __tablename__ = "inventory_transfers"

    id = Column(Integer, primary_key=True, index=True)
    from_business_id = Column(Integer, ForeignKey("business.id", ondelete="CASCADE"), nullable=False, index=True)
    to_business_id = Column(Integer, ForeignKey("business.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    status = Column(Enum(TransferStatus), nullable=False, default=TransferStatus.PENDING.value, index=True)
    notes = Column(Text, nullable=True)  # Notas del traslado

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)  # Fecha de aceptación/completado

    # Relationships
    from_business = relationship("Business", foreign_keys=[from_business_id], back_populates="outgoing_transfers")
    to_business = relationship("Business", foreign_keys=[to_business_id], back_populates="incoming_transfers")
    created_by = relationship("User", foreign_keys=[created_by_user_id])
    items = relationship("TransferItem", back_populates="transfer", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<InventoryTransfer(id={self.id}, from={self.from_business_id}, to={self.to_business_id}, status={self.status})>"


class TransferItem(Base):
    """
    Modelo TransferItem (Ítem de Traslado).
    Representa un ítem individual dentro de un traslado de inventario.
    """
    __tablename__ = "transfer_items"

    id = Column(Integer, primary_key=True, index=True)
    transfer_id = Column(Integer, ForeignKey("inventory_transfers.id", ondelete="CASCADE"), nullable=False, index=True)
    inventory_item_id = Column(Integer, ForeignKey("inventory_items.id", ondelete="CASCADE"), nullable=False, index=True)

    quantity = Column(Numeric(10, 3), nullable=False)  # Cantidad a trasladar
    notes = Column(Text, nullable=True)  # Notas específicas del ítem

    # Constraints
    __table_args__ = (
        UniqueConstraint('transfer_id', 'inventory_item_id', name='uq_transfer_item'),
    )

    # Relationships
    transfer = relationship("InventoryTransfer", back_populates="items")
    inventory_item = relationship("InventoryItem")

    def __repr__(self):
        return f"<TransferItem(id={self.id}, transfer_id={self.transfer_id}, item_id={self.inventory_item_id}, qty={self.quantity})>"
