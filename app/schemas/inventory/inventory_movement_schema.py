"""
Schemas Pydantic para InventoryMovement (Movimiento de Inventario).
Define la validación y serialización de datos de movimientos de inventario.
"""
from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import datetime
from typing import Optional
from app.models.inventory.inventory_enums import MovementType


class MovementResponse(BaseModel):
    """Schema para respuesta de Movimiento"""
    id: int
    inventory_item_id: int
    inventory_item_name: str  # Agregado en servicio
    business_id: int
    created_by_user_id: Optional[int]
    created_by_user_name: Optional[str]  # Agregado en servicio
    movement_type: MovementType
    quantity: Decimal
    reason: Optional[str]
    reference_id: Optional[int]
    reverted: bool
    reverted_by_movement_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class RevertMovementRequest(BaseModel):
    """Schema para revertir movimiento"""
    reason: str = Field(..., min_length=1, max_length=500)
