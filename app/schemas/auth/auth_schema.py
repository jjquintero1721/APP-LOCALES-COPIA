from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from app.models.users.user_model import UserRole


class RegisterRequest(BaseModel):
    """
    Schema para registro de usuario + negocio.
    """
    # Business info
    business_name: str = Field(..., min_length=1, max_length=255, description="Nombre del negocio")

    # User info
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    full_name: str = Field(..., min_length=1, max_length=255)


class LoginRequest(BaseModel):
    """
    Schema para login.
    """
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """
    Schema para respuesta de tokens JWT.
    """
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    """
    Schema para renovar token.
    """
    refresh_token: str


class TokenPayload(BaseModel):
    """
    Schema para payload del JWT.
    """
    user_id: int
    business_id: int
    role: UserRole
    exp: Optional[int] = None
