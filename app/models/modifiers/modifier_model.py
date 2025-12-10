"""
Modelos para Modificadores.
Representan grupos de modificadores, modificadores individuales, sus ítems de inventario
y la relación con productos.
"""
from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, ForeignKey, Text, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.config.database import Base


class ModifierGroup(Base):
    """
    Modelo ModifierGroup (Grupo de Modificadores).
    Representa un grupo de modificadores (ej: "Tamaño", "Extras", "Sin ingrediente").
    """
    __tablename__ = "modifier_groups"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("business.id", ondelete="CASCADE"), nullable=False, index=True)

    name = Column(String(255), nullable=False)  # Tamaño, Extras, etc.
    description = Column(Text, nullable=True)
    allow_multiple = Column(Boolean, default=False, nullable=False)  # Si se pueden seleccionar varios modificadores
    is_required = Column(Boolean, default=False, nullable=False)  # Si es obligatorio seleccionar
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    business = relationship("Business", back_populates="modifier_groups")
    modifiers = relationship("Modifier", back_populates="modifier_group", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ModifierGroup(id={self.id}, name='{self.name}', allow_multiple={self.allow_multiple})>"


class Modifier(Base):
    """
    Modelo Modifier (Modificador).
    Representa un modificador individual (ej: "Doble carne", "Sin cebolla", "Grande").
    """
    __tablename__ = "modifiers"

    id = Column(Integer, primary_key=True, index=True)
    modifier_group_id = Column(Integer, ForeignKey("modifier_groups.id", ondelete="CASCADE"), nullable=False, index=True)

    name = Column(String(255), nullable=False)  # Doble carne, Sin cebolla, etc.
    description = Column(Text, nullable=True)
    price_extra = Column(Numeric(10, 2), nullable=False, default=0)  # Precio adicional
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Constraints
    __table_args__ = (
        UniqueConstraint('modifier_group_id', 'name', name='uq_modifier_name_per_group'),
        CheckConstraint('price_extra >= 0', name='check_price_extra_non_negative'),
    )

    # Relationships
    modifier_group = relationship("ModifierGroup", back_populates="modifiers")
    inventory_items = relationship("ModifierInventoryItem", back_populates="modifier", cascade="all, delete-orphan")
    product_modifiers = relationship("ProductModifier", back_populates="modifier", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Modifier(id={self.id}, name='{self.name}', price_extra={self.price_extra})>"


class ModifierInventoryItem(Base):
    """
    Modelo ModifierInventoryItem (Ítem de Inventario del Modificador).
    Relaciona un modificador con ítems del inventario.
    quantity puede ser positivo (agregar) o negativo (quitar).
    """
    __tablename__ = "modifier_inventory_items"

    id = Column(Integer, primary_key=True, index=True)
    modifier_id = Column(Integer, ForeignKey("modifiers.id", ondelete="CASCADE"), nullable=False, index=True)
    inventory_item_id = Column(Integer, ForeignKey("inventory_items.id", ondelete="CASCADE"), nullable=False, index=True)

    quantity = Column(Numeric(10, 3), nullable=False)  # Positivo = agregar, Negativo = quitar

    # Constraints
    __table_args__ = (
        UniqueConstraint('modifier_id', 'inventory_item_id', name='uq_modifier_inventory_item'),
        CheckConstraint('quantity != 0', name='check_quantity_not_zero'),
    )

    # Relationships
    modifier = relationship("Modifier", back_populates="inventory_items")
    inventory_item = relationship("InventoryItem", back_populates="modifier_inventory_items")

    def __repr__(self):
        return f"<ModifierInventoryItem(id={self.id}, modifier_id={self.modifier_id}, item_id={self.inventory_item_id}, qty={self.quantity})>"


class ProductModifier(Base):
    """
    Modelo ProductModifier (Compatibilidad Producto-Modificador).
    Define qué modificadores son compatibles con qué productos.
    Un modificador solo puede aplicarse a un producto si todos sus inventory_items
    existen en los ingredientes del producto.
    """
    __tablename__ = "product_modifiers"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    modifier_id = Column(Integer, ForeignKey("modifiers.id", ondelete="CASCADE"), nullable=False, index=True)

    # Constraints
    __table_args__ = (
        UniqueConstraint('product_id', 'modifier_id', name='uq_product_modifier'),
    )

    # Relationships
    product = relationship("Product", back_populates="product_modifiers")
    modifier = relationship("Modifier", back_populates="product_modifiers")

    def __repr__(self):
        return f"<ProductModifier(id={self.id}, product_id={self.product_id}, modifier_id={self.modifier_id})>"
