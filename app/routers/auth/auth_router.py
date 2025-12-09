from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.config.database import get_db
from app.controllers.auth.auth_controller import AuthController
from app.schemas.auth.auth_schema import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """
    Registra un nuevo usuario y crea su negocio.
    El primer usuario siempre es OWNER.
    """
    return await AuthController.register(data, db)


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Login de usuario.
    Retorna access_token y refresh_token.
    """
    return await AuthController.login(data, db)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(data: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    """
    Renueva el access token usando un refresh token válido.
    """
    return await AuthController.refresh_token(data, db)
