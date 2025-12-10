"""
Modelo InventoryItem (Ítem de Inventario).
Representa un producto/ingrediente en el inventario de un negocio.
"""
from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, ForeignKey, Text, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.config.database import Base


class InventoryItem(Base):
    """
    Modelo InventoryItem (Ítem de Inventario).
    Representa un ítem en el inventario de un negocio (ingredientes, productos, insumos).
    """
    __tablename__ = "inventory_items"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("business.id", ondelete="CASCADE"), nullable=False, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id", ondelete="SET NULL"), nullable=True, index=True)

    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=True)  # Texto libre: bebidas, carnes, verduras, etc.
    unit_of_measure = Column(String(50), nullable=False)  # kg, g, litros, ml, unidad, caja, paquete
    sku = Column(String(100), nullable=True, index=True)  # Código para filtrado

    quantity_in_stock = Column(Numeric(10, 3), nullable=False, default=0)
    min_stock = Column(Numeric(10, 3), nullable=True)
    max_stock = Column(Numeric(10, 3), nullable=True)
    unit_price = Column(Numeric(10, 2), nullable=False)

    tax_percentage = Column(Numeric(5, 2), nullable=True)  # 16, 19, etc.
    include_tax = Column(Boolean, default=False, nullable=False)  # Si el precio incluye IVA

    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Constraints
    __table_args__ = (
        CheckConstraint('quantity_in_stock >= 0', name='check_quantity_non_negative'),
        CheckConstraint('unit_price >= 0', name='check_unit_price_non_negative'),
    )

    # Relationships
    business = relationship("Business", back_populates="inventory_items")
    supplier = relationship("Supplier", back_populates="inventory_items")
    movements = relationship("InventoryMovement", back_populates="inventory_item", cascade="all, delete-orphan")
    product_ingredients = relationship("ProductIngredient", back_populates="inventory_item")
    modifier_inventory_items = relationship("ModifierInventoryItem", back_populates="inventory_item")

    def __repr__(self):
        return f"<InventoryItem(id={self.id}, name='{self.name}', stock={self.quantity_in_stock})>"
