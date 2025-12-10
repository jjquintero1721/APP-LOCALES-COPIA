"""
Schemas Pydantic para BusinessRelationship (Relación entre Negocios).
Define la validación y serialización de datos de relaciones entre negocios.
"""
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional
from app.models.inventory.inventory_enums import RelationshipStatus


class RelationshipCreateRequest(BaseModel):
    """Schema para crear relación"""
    target_business_id: int = Field(..., gt=0)


class RelationshipResponse(BaseModel):
    """Schema para respuesta de Relación"""
    id: int
    requester_business_id: int
    requester_business_name: str  # Agregado en servicio
    target_business_id: int
    target_business_name: str  # Agregado en servicio
    status: RelationshipStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
