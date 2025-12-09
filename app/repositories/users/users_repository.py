from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from typing import Optional, List
from app.models.users.user_model import User, UserRole


class UsersRepository:
    """
    Repositorio para operaciones de User en la base de datos.
    TODOS los queries filtran por business_id (multi-tenant).
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        business_id: int,
        email: str,
        full_name: str,
        hashed_password: str,
        role: UserRole = UserRole.CASHIER,
        phone: Optional[str] = None,
        document: Optional[str] = None,
    ) -> User:
        """
        Crea un nuevo usuario.
        """
        user = User(
            business_id=business_id,
            email=email,
            full_name=full_name,
            hashed_password=hashed_password,
            role=role,
            phone=phone,
            document=document,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def get_by_id(self, user_id: int, business_id: int) -> Optional[User]:
        """
        Obtiene un usuario por ID, filtrado por business_id.
        """
        result = await self.db.execute(
            select(User)
                .options(selectinload(User.business))            
                .where(
                    and_(User.id == user_id, User.business_id == business_id)
                )
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str, business_id: int) -> Optional[User]:
        """
        Obtiene un usuario por email, filtrado por business_id.
        """
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.business))
            .where(
                and_(User.email == email, User.business_id == business_id)
            )
        )
        return result.scalar_one_or_none()

    async def get_all_by_business(
        self, business_id: int, skip: int = 0, limit: int = 100
    ) -> List[User]:
        """
        Obtiene todos los usuarios de un negocio.
        """
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.business))
            .where(User.business_id == business_id)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update(self, user: User) -> User:
        """
        Actualiza un usuario.
        """
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def email_exists(self, email: str, business_id: int, exclude_user_id: Optional[int] = None) -> bool:
        """
        Verifica si un email ya existe en un negocio.

        Args:
            email: Email a verificar
            business_id: ID del negocio
            exclude_user_id: ID del usuario a excluir de la búsqueda (útil para actualizaciones)
        """
        query = select(User.id).where(
            and_(User.email == email, User.business_id == business_id)
        )

        if exclude_user_id is not None:
            query = query.where(User.id != exclude_user_id)

        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None

    async def delete_permanently(self, user: User) -> None:
        """
        Elimina permanentemente un usuario de la base de datos.
        """
        await self.db.delete(user)
        await self.db.commit()

    async def get_by_document(self, document: str, business_id: int) -> Optional[User]:
        """
        Obtiene un usuario por documento, filtrado por business_id.
        """
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.business))
            .where(
                and_(User.document == document, User.business_id == business_id)
            )
        )
        return result.scalar_one_or_none()

    async def count_owners(self, business_id: int) -> int:
        """
        Cuenta cuántos owners tiene un negocio.
        """
        from sqlalchemy import func as sql_func
        result = await self.db.execute(
            select(sql_func.count(User.id)).where(
                and_(User.business_id == business_id, User.role == UserRole.OWNER)
            )
        )
        return result.scalar_one()
