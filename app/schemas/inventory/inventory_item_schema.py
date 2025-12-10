"""
Schemas Pydantic para InventoryItem (Ítem de Inventario).
Define la validación y serialización de datos de ítems de inventario.
"""
from pydantic import BaseModel, Field, field_validator, model_validator, condecimal
from decimal import Decimal
from datetime import datetime
from typing import Optional, Annotated


class InventoryItemBase(BaseModel):
    """Base schema para InventoryItem con campos comunes"""
    name: str = Field(..., min_length=1, max_length=255)
    category: Optional[str] = Field(None, max_length=100)
    unit_of_measure: str = Field(..., min_length=1, max_length=50)
    sku: Optional[str] = Field(None, max_length=100)
    unit_price: Annotated[Decimal, Field(ge=0)]
    min_stock: Optional[Annotated[Decimal, Field(ge=0)]] = None
    max_stock: Optional[Annotated[Decimal, Field(ge=0)]] = None
    tax_percentage: Optional[Annotated[Decimal, Field(ge=0, le=100)]] = None
    include_tax: bool = False
    supplier_id: Optional[int] = None


class InventoryItemCreate(InventoryItemBase):
    """Schema para crear un nuevo InventoryItem"""
    quantity_in_stock: Annotated[Decimal, Field(ge=0)] = Decimal(0)

    @model_validator(mode='after')
    def validate_stock_limits(self):
        """Validar que max_stock >= min_stock"""
        if self.max_stock is not None and self.min_stock is not None:
            if self.max_stock < self.min_stock:
                raise ValueError('max_stock debe ser mayor o igual que min_stock')
        return self


class InventoryItemUpdate(BaseModel):
    """Schema para actualizar InventoryItem (sin tocar stock directamente)"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    category: Optional[str] = Field(None, max_length=100)
    unit_of_measure: Optional[str] = Field(None, min_length=1, max_length=50)
    sku: Optional[str] = Field(None, max_length=100)
    unit_price: Optional[Annotated[Decimal, Field(ge=0)]] = None
    min_stock: Optional[Annotated[Decimal, Field(ge=0)]] = None
    max_stock: Optional[Annotated[Decimal, Field(ge=0)]] = None
    tax_percentage: Optional[Annotated[Decimal, Field(ge=0, le=100)]] = None
    include_tax: Optional[bool] = None
    supplier_id: Optional[int] = None
    is_active: Optional[bool] = None


class StockAdjustmentRequest(BaseModel):
    """Schema para ajuste manual de stock"""
    quantity_change: Annotated[Decimal, Field()]  # Positivo = entrada, Negativo = salida
    reason: str = Field(..., min_length=1, max_length=500)

    @field_validator('quantity_change')
    @classmethod
    def validate_quantity_change(cls, v):
        if v == 0:
            raise ValueError('quantity_change no puede ser cero')
        return v


class InventoryItemResponse(InventoryItemBase):
    """Schema para respuesta de InventoryItem"""
    id: int
    business_id: int
    quantity_in_stock: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime
    supplier_name: Optional[str] = None  # Agregado en el servicio
    is_below_min_stock: bool = False  # Agregado en el servicio

    class Config:
        from_attributes = True
