"""
Controller para Productos/Recetas.
Capa delgada que delega al servicio de productos.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.services.products.products_service import ProductsService
from app.schemas.products.product_schema import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductListResponse,
    IngredientUpdate,
)
from app.models.users.user_model import User


class ProductsController:
    """
    Controller para gestionar endpoints de productos.
    """

    @staticmethod
    async def create_product(
        data: ProductCreate,
        current_user: User,
        db: AsyncSession,
    ) -> ProductResponse:
        """Crear un nuevo producto"""
        service = ProductsService(db)
        return await service.create_product(data, current_user)

    @staticmethod
    async def get_product_by_id(
        product_id: int,
        current_user: User,
        db: AsyncSession,
    ) -> ProductResponse:
        """Obtener un producto por ID"""
        service = ProductsService(db)
        return await service.get_product_by_id(product_id, current_user)

    @staticmethod
    async def get_all_products(
        skip: int,
        limit: int,
        active_only: bool,
        category: Optional[str],
        current_user: User,
        db: AsyncSession,
    ) -> List[ProductListResponse]:
        """Obtener todos los productos"""
        service = ProductsService(db)
        return await service.get_all_products(
            current_user,
            skip=skip,
            limit=limit,
            active_only=active_only,
            category=category,
        )

    @staticmethod
    async def update_product(
        product_id: int,
        data: ProductUpdate,
        current_user: User,
        db: AsyncSession,
    ) -> ProductResponse:
        """Actualizar un producto"""
        service = ProductsService(db)
        return await service.update_product(product_id, data, current_user)

    @staticmethod
    async def update_ingredients(
        product_id: int,
        data: IngredientUpdate,
        current_user: User,
        db: AsyncSession,
    ) -> ProductResponse:
        """Actualizar ingredientes de un producto"""
        service = ProductsService(db)
        return await service.update_ingredients(product_id, data, current_user)

    @staticmethod
    async def deactivate_product(
        product_id: int,
        current_user: User,
        db: AsyncSession,
    ) -> ProductResponse:
        """Inactivar un producto"""
        service = ProductsService(db)
        return await service.deactivate_product(product_id, current_user)
