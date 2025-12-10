"""
Controller para Business.
Capa delgada que delega al servicio de negocios.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.services.business.business_service import BusinessService
from app.schemas.business.business_schema import BusinessResponse


class BusinessController:
    """
    Controller para gestionar endpoints de negocios.
    """

    @staticmethod
    async def get_all_businesses(db: AsyncSession) -> List[BusinessResponse]:
        """Obtener todos los negocios"""
        service = BusinessService(db)
        return await service.get_all_businesses()
