from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
from app.models.business.business_model import Business


class BusinessRepository:
    """
    Repositorio para operaciones de Business en la base de datos.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, name: str) -> Business:
        """
        Crea un nuevo negocio.
        """
        business = Business(name=name)
        self.db.add(business)
        await self.db.commit()
        await self.db.refresh(business)
        return business

    async def get_by_id(self, business_id: int) -> Optional[Business]:
        """
        Obtiene un negocio por ID.
        """
        result = await self.db.execute(
            select(Business).where(Business.id == business_id)
        )
        return result.scalar_one_or_none()

    async def get_all(self) -> List[Business]:
        """
        Obtiene todos los negocios.
        """
        result = await self.db.execute(select(Business))
        return list(result.scalars().all())
