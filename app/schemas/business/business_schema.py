from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class BusinessBase(BaseModel):
    """
    Schema base para Business.
    """
    name: str = Field(..., min_length=1, max_length=255, description="Nombre del negocio")


class BusinessCreate(BusinessBase):
    """
    Schema para crear un Business.
    """
    pass


class BusinessResponse(BusinessBase):
    """
    Schema para respuesta de Business.
    """
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
