from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from typing import List
from app.repositories.users.users_repository import UsersRepository
from app.schemas.users.user_schema import UserResponse


class UsersService:
    """
    Servicio de usuarios.
    Maneja operaciones relacionadas con usuarios.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.users_repo = UsersRepository(db)

    async def get_user_by_id(self, user_id: int, business_id: int) -> UserResponse:
        """
        Obtiene un usuario por ID.
        Filtra por business_id para seguridad multi-tenant.
        """
        user = await self.users_repo.get_by_id(user_id, business_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return UserResponse.model_validate(user)

    async def get_all_users(
        self, business_id: int, skip: int = 0, limit: int = 100
    ) -> List[UserResponse]:
        """
        Obtiene todos los usuarios del negocio.
        """
        users = await self.users_repo.get_all_by_business(business_id, skip, limit)
        return [UserResponse.model_validate(user) for user in users]
