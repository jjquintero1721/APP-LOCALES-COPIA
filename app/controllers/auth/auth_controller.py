from sqlalchemy.ext.asyncio import AsyncSession
from app.services.auth.auth_service import AuthService
from app.schemas.auth.auth_schema import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
)


class AuthController:
    """
    Controller de autenticación.
    Maneja los requests HTTP y delega la lógica al servicio.
    """

    @staticmethod
    async def register(
        data: RegisterRequest,
        db: AsyncSession,
    ) -> TokenResponse:
        """
        Endpoint: POST /auth/register
        Registra un nuevo usuario y crea su negocio.
        """
        auth_service = AuthService(db)
        return await auth_service.register(data)

    @staticmethod
    async def login(
        data: LoginRequest,
        db: AsyncSession,
    ) -> TokenResponse:
        """
        Endpoint: POST /auth/login
        Login de usuario.
        """
        auth_service = AuthService(db)
        return await auth_service.login(data)

    @staticmethod
    async def refresh_token(
        data: RefreshTokenRequest,
        db: AsyncSession,
    ) -> TokenResponse:
        """
        Endpoint: POST /auth/refresh
        Renueva el access token.
        """
        auth_service = AuthService(db)
        return await auth_service.refresh_token(data.refresh_token)
