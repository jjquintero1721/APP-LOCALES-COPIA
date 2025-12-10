"""
Schemas Pydantic para Product (Producto/Receta).
Define la validación y serialización de datos de productos.
"""
from pydantic import BaseModel, Field, field_validator, model_validator
from decimal import Decimal
from datetime import datetime
from typing import List, Optional, Annotated


class ProductIngredientCreate(BaseModel):
    """Schema para crear un ingrediente dentro de un producto"""
    inventory_item_id: int = Field(..., gt=0)
    quantity: Annotated[Decimal, Field(gt=0)]

    @field_validator('quantity')
    @classmethod
    def validate_quantity(cls, v):
        """Validar que la cantidad sea positiva"""
        if v <= 0:
            raise ValueError('La cantidad debe ser mayor a 0')
        return v


class ProductIngredientResponse(BaseModel):
    """Schema para respuesta de ingrediente"""
    id: int
    product_id: int
    inventory_item_id: int
    inventory_item_name: str  # Agregado en servicio
    quantity: Decimal
    unit_cost: Decimal
    total_cost: Decimal

    class Config:
        from_attributes = True


class ProductCreate(BaseModel):
    """Schema para crear un nuevo producto"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)
    category: Optional[str] = Field(None, max_length=100)
    sale_price: Annotated[Decimal, Field(ge=0)]
    profit_margin_percentage: Optional[Annotated[Decimal, Field(ge=0, le=100)]] = None
    image_url: Optional[str] = Field(None, max_length=500)
    ingredients: List[ProductIngredientCreate] = Field(..., min_length=1)

    @field_validator('ingredients')
    @classmethod
    def validate_no_duplicate_ingredients(cls, v):
        """Validar que no haya ingredientes duplicados"""
        item_ids = [ing.inventory_item_id for ing in v]
        if len(item_ids) != len(set(item_ids)):
            raise ValueError('No se pueden agregar ingredientes duplicados en el mismo producto')
        return v


class ProductUpdate(BaseModel):
    """Schema para actualizar un producto (sin ingredientes)"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)
    category: Optional[str] = Field(None, max_length=100)
    sale_price: Optional[Annotated[Decimal, Field(ge=0)]] = None
    profit_margin_percentage: Optional[Annotated[Decimal, Field(ge=0, le=100)]] = None
    image_url: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class IngredientUpdate(BaseModel):
    """Schema para actualizar ingredientes de un producto"""
    ingredients: List[ProductIngredientCreate] = Field(..., min_length=1)

    @field_validator('ingredients')
    @classmethod
    def validate_no_duplicate_ingredients(cls, v):
        """Validar que no haya ingredientes duplicados"""
        item_ids = [ing.inventory_item_id for ing in v]
        if len(item_ids) != len(set(item_ids)):
            raise ValueError('No se pueden agregar ingredientes duplicados en el mismo producto')
        return v


class ProductResponse(BaseModel):
    """Schema para respuesta de producto"""
    id: int
    business_id: int
    name: str
    description: Optional[str]
    category: Optional[str]
    sale_price: Decimal
    total_cost: Decimal
    profit_margin_percentage: Optional[Decimal]
    profit_amount: Optional[Decimal]
    image_url: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    ingredients: List[ProductIngredientResponse]

    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    """Schema para lista de productos (sin ingredientes para performance)"""
    id: int
    name: str
    category: Optional[str]
    sale_price: Decimal
    total_cost: Decimal
    profit_margin_percentage: Optional[Decimal]
    is_active: bool
    ingredients_count: int  # Agregado en servicio

    class Config:
        from_attributes = True
