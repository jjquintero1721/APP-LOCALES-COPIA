"""
Modelos Product y ProductIngredient.
Representan productos/recetas y sus ingredientes del inventario.
"""
from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, ForeignKey, Text, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.config.database import Base


class Product(Base):
    """
    Modelo Product (Producto/Receta).
    Representa un producto final que se vende, compuesto por ingredientes del inventario.
    """
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("business.id", ondelete="CASCADE"), nullable=False, index=True)

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)  # Comidas rápidas, bebidas, postres, etc.

    sale_price = Column(Numeric(10, 2), nullable=False)  # Precio de venta
    total_cost = Column(Numeric(10, 2), nullable=False, default=0)  # Costo total (calculado)
    profit_margin_percentage = Column(Numeric(5, 2), nullable=True)  # Margen de ganancia en %
    profit_amount = Column(Numeric(10, 2), nullable=True)  # Ganancia en dinero

    image_url = Column(String(500), nullable=True)  # URL de la imagen o path
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Constraints
    __table_args__ = (
        CheckConstraint('sale_price >= 0', name='check_sale_price_non_negative'),
        CheckConstraint('total_cost >= 0', name='check_total_cost_non_negative'),
        CheckConstraint('sale_price >= total_cost', name='check_sale_price_gte_total_cost'),
    )

    # Relationships
    business = relationship("Business", back_populates="products")
    ingredients = relationship("ProductIngredient", back_populates="product", cascade="all, delete-orphan")
    product_modifiers = relationship("ProductModifier", back_populates="product", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', sale_price={self.sale_price})>"


class ProductIngredient(Base):
    """
    Modelo ProductIngredient (Ingrediente de Producto).
    Relaciona un producto con los ítems del inventario que lo componen.
    """
    __tablename__ = "product_ingredients"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    inventory_item_id = Column(Integer, ForeignKey("inventory_items.id", ondelete="CASCADE"), nullable=False, index=True)

    quantity = Column(Numeric(10, 3), nullable=False)  # Cantidad del ingrediente
    unit_cost = Column(Numeric(10, 2), nullable=False)  # Costo unitario del ingrediente (copiado de inventory_item)
    total_cost = Column(Numeric(10, 2), nullable=False)  # quantity * unit_cost

    # Constraints
    __table_args__ = (
        UniqueConstraint('product_id', 'inventory_item_id', name='uq_product_ingredient'),
        CheckConstraint('quantity > 0', name='check_ingredient_quantity_positive'),
        CheckConstraint('unit_cost >= 0', name='check_ingredient_unit_cost_non_negative'),
        CheckConstraint('total_cost >= 0', name='check_ingredient_total_cost_non_negative'),
    )

    # Relationships
    product = relationship("Product", back_populates="ingredients")
    inventory_item = relationship("InventoryItem", back_populates="product_ingredients")

    def __repr__(self):
        return f"<ProductIngredient(id={self.id}, product_id={self.product_id}, item_id={self.inventory_item_id}, qty={self.quantity})>"
