"""
Servicio de Business.
Maneja operaciones CRUD de negocios.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.repositories.business.business_repository import BusinessRepository
from app.schemas.business.business_schema import BusinessResponse


class BusinessService:
    """
    Servicio de negocios.
    Maneja operaciones de negocios.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.business_repo = BusinessRepository(db)

    async def get_all_businesses(self) -> List[BusinessResponse]:
        """
        Obtiene todos los negocios registrados.

        Returns:
            List[BusinessResponse]: Lista de todos los negocios
        """
        businesses = await self.business_repo.get_all()
        return [BusinessResponse.model_validate(business) for business in businesses]
