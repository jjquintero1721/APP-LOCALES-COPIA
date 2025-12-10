"""
Modelo Supplier (Proveedor).
Proveedores de ítems de inventario para un negocio.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.config.database import Base


class Supplier(Base):
    """
    Modelo Supplier (Proveedor).
    Representa un proveedor de productos/ingredientes para el inventario de un negocio.
    """
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("business.id", ondelete="CASCADE"), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    supplier_type = Column(String(100), nullable=True)  # Texto libre: alimentos, bebidas, etc.
    tax_id = Column(String(50), nullable=True)  # NIT/RFC/Identificación tributaria
    legal_representative = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    address = Column(Text, nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    business = relationship("Business", back_populates="suppliers")
    inventory_items = relationship("InventoryItem", back_populates="supplier")

    def __repr__(self):
        return f"<Supplier(id={self.id}, name='{self.name}', business_id={self.business_id})>"
