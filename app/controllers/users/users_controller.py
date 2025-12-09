from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.services.users.users_service import UsersService
from app.schemas.users.user_schema import UserResponse
from app.models.users.user_model import User


class UsersController:
    """
    Controller de usuarios.
    Maneja los requests HTTP y delega la lógica al servicio.
    """

    @staticmethod
    async def get_me(
        current_user: User,
    ) -> UserResponse:
        """
        Endpoint: GET /users/me
        Obtiene el perfil del usuario actual.
        """
        # Crear el response con los datos del usuario
        user_response = UserResponse.model_validate(current_user)
        
        # Agregar el nombre del negocio si existe
        if current_user.business:
            user_response.business_name = current_user.business.name
        
        return user_response

    @staticmethod
    async def get_users(
        skip: int,
        limit: int,
        current_user: User,
        db: AsyncSession,
    ) -> List[UserResponse]:
        """
        Endpoint: GET /users/
        Obtiene todos los usuarios del negocio.
        """
        users_service = UsersService(db)
        return await users_service.get_all_users(current_user.business_id, skip, limit)
