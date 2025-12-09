from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional
from app.models.users.user_model import UserRole


class UserBase(BaseModel):
    """
    Schema base para User.
    """
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    document: Optional[str] = Field(None, max_length=50)


class UserCreate(UserBase):
    """
    Schema para crear un User.
    Incluye password en texto plano (se hasheará en el servicio).
    """
    password: str = Field(..., min_length=8, max_length=100)
    role: UserRole = UserRole.CASHIER


class UserUpdate(BaseModel):
    """
    Schema para actualizar un User.
    """
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """
    Schema para respuesta de User.
    NO incluye hashed_password por seguridad.
    """
    id: int
    business_id: int
    business_name: Optional[str] = None
    role: UserRole
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserInDB(UserResponse):
    """
    Schema para User en base de datos.
    Incluye hashed_password para uso interno.
    """
    hashed_password: str
