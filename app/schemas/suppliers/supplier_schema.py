"""
Schemas Pydantic para Supplier (Proveedor).
Define la validación y serialización de datos de proveedores.
"""
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional


class SupplierBase(BaseModel):
    """Base schema para Supplier con campos comunes"""
    name: str = Field(..., min_length=1, max_length=255)
    supplier_type: Optional[str] = Field(None, max_length=100)
    tax_id: Optional[str] = Field(None, max_length=50)
    legal_representative: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    address: Optional[str] = None


class SupplierCreate(SupplierBase):
    """Schema para crear un nuevo Supplier"""
    pass


class SupplierUpdate(BaseModel):
    """Schema para actualizar un Supplier existente"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    supplier_type: Optional[str] = Field(None, max_length=100)
    tax_id: Optional[str] = Field(None, max_length=50)
    legal_representative: Optional[str] = Field(None, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    is_active: Optional[bool] = None


class SupplierResponse(SupplierBase):
    """Schema para respuesta de Supplier"""
    id: int
    business_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
