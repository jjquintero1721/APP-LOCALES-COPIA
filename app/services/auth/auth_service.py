from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.repositories.users.users_repository import UsersRepository
from app.repositories.business.business_repository import BusinessRepository
from app.repositories.audit.audit_repository import AuditRepository
from app.schemas.auth.auth_schema import RegisterRequest, LoginRequest, TokenResponse
from app.schemas.users.user_schema import UserResponse
from app.models.users.user_model import UserRole
from app.utils.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)


class AuthService:
    """
    Servicio de autenticación.
    Maneja registro, login, refresh tokens.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.users_repo = UsersRepository(db)
        self.business_repo = BusinessRepository(db)
        self.audit_repo = AuditRepository(db)

    async def register(self, data: RegisterRequest) -> TokenResponse:
        """
        Registra un nuevo usuario y crea su negocio.
        El primer usuario siempre es OWNER.
        """
        # Crear el negocio
        business = await self.business_repo.create(name=data.business_name)

        # Verificar que el email no exista en este negocio
        existing_user = await self.users_repo.get_by_email(data.email, business.id)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered in this business",
            )

        # Hashear contraseña
        hashed_password = get_password_hash(data.password)

        # Crear usuario owner
        user = await self.users_repo.create(
            business_id=business.id,
            email=data.email,
            full_name=data.full_name,
            hashed_password=hashed_password,
            role=UserRole.OWNER,
        )

        # Registrar auditoría
        await self.audit_repo.create_log(
            business_id=business.id,
            user_id=user.id,
            action=f"Usuario owner '{user.full_name}' registrado. Negocio '{business.name}' creado.",
        )

        # Generar tokens
        access_token = create_access_token(user.id, business.id, user.role)
        refresh_token = create_refresh_token(user.id, business.id, user.role)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    async def login(self, data: LoginRequest) -> TokenResponse:
        """
        Login de usuario.
        NOTA: No requiere business_id porque el email puede identificar al usuario.
        """
        # Buscar usuario por email en TODOS los negocios
        # (En producción, se podría agregar dominio/subdomain para identificar el negocio)
        from sqlalchemy import select
        from app.models.users.user_model import User

        result = await self.db.execute(select(User).where(User.email == data.email))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )

        # Verificar contraseña
        if not verify_password(data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )

        # Verificar que el usuario esté activo
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is not active",
            )

        # Registrar auditoría
        await self.audit_repo.create_log(
            business_id=user.business_id,
            user_id=user.id,
            action=f"Usuario '{user.full_name}' inició sesión",
        )

        # Generar tokens
        access_token = create_access_token(user.id, user.business_id, user.role)
        refresh_token = create_refresh_token(user.id, user.business_id, user.role)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        """
        Renueva el access token usando un refresh token válido.
        """
        # Decodificar y validar refresh token
        token_data = decode_token(refresh_token)

        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )

        # Verificar que el usuario existe y está activo
        user = await self.users_repo.get_by_id(token_data.user_id, token_data.business_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )

        # Generar nuevos tokens
        access_token = create_access_token(user.id, user.business_id, user.role)
        new_refresh_token = create_refresh_token(user.id, user.business_id, user.role)

        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
        )
