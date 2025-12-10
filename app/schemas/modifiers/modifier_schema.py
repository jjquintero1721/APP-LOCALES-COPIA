"""
Schemas Pydantic para Modificadores.
Define la validación y serialización de datos de modificadores.
"""
from pydantic import BaseModel, Field, field_validator
from decimal import Decimal
from datetime import datetime
from typing import List, Optional, Annotated


# ============= MODIFIER GROUP SCHEMAS =============

class ModifierGroupCreate(BaseModel):
    """Schema para crear un grupo de modificadores"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)
    allow_multiple: bool = False
    is_required: bool = False


class ModifierGroupUpdate(BaseModel):
    """Schema para actualizar un grupo de modificadores"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)
    allow_multiple: Optional[bool] = None
    is_required: Optional[bool] = None
    is_active: Optional[bool] = None


class ModifierGroupResponse(BaseModel):
    """Schema para respuesta de grupo de modificadores"""
    id: int
    business_id: int
    name: str
    description: Optional[str]
    allow_multiple: bool
    is_required: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    modifiers_count: int  # Agregado en servicio

    class Config:
        from_attributes = True


# ============= MODIFIER SCHEMAS =============

class ModifierInventoryItemCreate(BaseModel):
    """Schema para crear un ítem de inventario dentro de un modificador"""
    inventory_item_id: int = Field(..., gt=0)
    quantity: Annotated[Decimal, Field()]

    @field_validator('quantity')
    @classmethod
    def validate_quantity_not_zero(cls, v):
        """Validar que la cantidad no sea cero"""
        if v == 0:
            raise ValueError('La cantidad no puede ser 0. Use valores positivos para agregar y negativos para quitar.')
        return v


class ModifierInventoryItemResponse(BaseModel):
    """Schema para respuesta de ítem de inventario del modificador"""
    id: int
    modifier_id: int
    inventory_item_id: int
    inventory_item_name: str  # Agregado en servicio
    quantity: Decimal

    class Config:
        from_attributes = True


class ModifierCreate(BaseModel):
    """Schema para crear un modificador"""
    modifier_group_id: int = Field(..., gt=0)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)
    price_extra: Annotated[Decimal, Field(ge=0)] = Decimal(0)
    inventory_items: List[ModifierInventoryItemCreate] = Field(..., min_length=1)

    @field_validator('inventory_items')
    @classmethod
    def validate_no_duplicate_items(cls, v):
        """Validar que no haya ítems duplicados"""
        item_ids = [item.inventory_item_id for item in v]
        if len(item_ids) != len(set(item_ids)):
            raise ValueError('No se pueden agregar ítems duplicados en el mismo modificador')
        return v


class ModifierUpdate(BaseModel):
    """Schema para actualizar un modificador"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)
    price_extra: Optional[Annotated[Decimal, Field(ge=0)]] = None
    is_active: Optional[bool] = None


class ModifierResponse(BaseModel):
    """Schema para respuesta de modificador"""
    id: int
    modifier_group_id: int
    modifier_group_name: str  # Agregado en servicio
    name: str
    description: Optional[str]
    price_extra: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime
    inventory_items: List[ModifierInventoryItemResponse]

    class Config:
        from_attributes = True


class ModifierListResponse(BaseModel):
    """Schema para lista de modificadores (sin ítems)"""
    id: int
    modifier_group_id: int
    modifier_group_name: str
    name: str
    price_extra: Decimal
    is_active: bool
    items_count: int  # Agregado en servicio

    class Config:
        from_attributes = True


# ============= PRODUCT MODIFIER SCHEMAS =============

class ProductModifierAssign(BaseModel):
    """Schema para asignar un modificador a un producto"""
    modifier_id: int = Field(..., gt=0)


class ProductModifierResponse(BaseModel):
    """Schema para respuesta de modificador asignado a producto"""
    id: int
    product_id: int
    modifier_id: int
    modifier_name: str  # Agregado en servicio
    modifier_group_name: str  # Agregado en servicio
    price_extra: Decimal  # Agregado en servicio

    class Config:
        from_attributes = True
