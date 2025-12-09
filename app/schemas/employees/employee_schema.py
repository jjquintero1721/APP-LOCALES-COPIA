from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime
from typing import Optional
from app.models.users.user_model import UserRole


class EmployeeCreateRequest(BaseModel):
    """
    Schema para crear un empleado.
    El owner o admin puede crear empleados de roles permitidos.
    """
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    document: Optional[str] = Field(None, max_length=50)
    role: UserRole
    password: Optional[str] = Field(None, min_length=8, max_length=100, description="Si no se proporciona, se generará automáticamente")

    @field_validator('role')
    def validate_role(cls, v):
        """Valida que el rol no sea OWNER (los owners se crean al registrar el negocio)"""
        if v == UserRole.OWNER:
            raise ValueError("No se puede crear un empleado con rol OWNER")
        return v


class EmployeeUpdateRequest(BaseModel):
    """
    Schema para actualizar un empleado.
    Solo se pueden actualizar ciertos campos.
    """
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None

    @field_validator('role')
    def validate_role(cls, v):
        """Valida que el rol no sea OWNER"""
        if v == UserRole.OWNER:
            raise ValueError("No se puede cambiar el rol a OWNER")
        return v


class EmployeeResponse(BaseModel):
    """
    Schema para respuesta de empleado.
    """
    id: int
    business_id: int
    business_name: Optional[str] = None
    email: EmailStr
    full_name: str
    phone: Optional[str] = None
    document: Optional[str] = None
    role: UserRole
    is_active: bool
    created_at: datetime
    # Incluir contraseña temporal solo al crear (se manejará en el servicio)
    temporary_password: Optional[str] = None

    class Config:
        from_attributes = True
