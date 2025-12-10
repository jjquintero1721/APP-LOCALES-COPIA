"""
Schemas Pydantic para InventoryTransfer (Traslado de Inventario).
Define la validación y serialización de datos de traslados de inventario.
"""
from pydantic import BaseModel, Field, field_validator
from decimal import Decimal
from datetime import datetime
from typing import List, Optional, Annotated
from app.models.inventory.inventory_enums import TransferStatus


class TransferItemCreate(BaseModel):
    """Schema para crear un ítem dentro de un traslado"""
    inventory_item_id: int = Field(..., gt=0)
    quantity: Annotated[Decimal, Field(gt=0)]
    notes: Optional[str] = Field(None, max_length=500)

    @field_validator('quantity')
    @classmethod
    def validate_quantity(cls, v):
        """Validar que la cantidad sea positiva"""
        if v <= 0:
            raise ValueError('La cantidad debe ser mayor a 0')
        return v


class TransferItemResponse(BaseModel):
    """Schema para respuesta de ítem de traslado"""
    id: int
    transfer_id: int
    inventory_item_id: int
    inventory_item_name: str  # Agregado en servicio
    quantity: Decimal
    notes: Optional[str]

    class Config:
        from_attributes = True


class TransferCreate(BaseModel):
    """Schema para crear un nuevo traslado"""
    to_business_id: int = Field(..., gt=0)
    notes: Optional[str] = Field(None, max_length=1000)
    items: List[TransferItemCreate] = Field(..., min_length=1)

    @field_validator('items')
    @classmethod
    def validate_no_duplicate_items(cls, v):
        """Validar que no haya ítems duplicados en el traslado"""
        item_ids = [item.inventory_item_id for item in v]
        if len(item_ids) != len(set(item_ids)):
            raise ValueError('No se pueden agregar ítems duplicados en el mismo traslado')
        return v


class TransferResponse(BaseModel):
    """Schema para respuesta de traslado"""
    id: int
    from_business_id: int
    from_business_name: str  # Agregado en servicio
    to_business_id: int
    to_business_name: str  # Agregado en servicio
    created_by_user_id: Optional[int]
    created_by_user_name: Optional[str]  # Agregado en servicio
    status: TransferStatus
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]
    items: List[TransferItemResponse]

    class Config:
        from_attributes = True


class TransferListResponse(BaseModel):
    """Schema para lista de traslados (sin ítems para performance)"""
    id: int
    from_business_id: int
    from_business_name: str
    to_business_id: int
    to_business_name: str
    status: TransferStatus
    items_count: int  # Agregado en servicio
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True
