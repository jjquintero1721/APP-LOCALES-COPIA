"""
Repositorio para operaciones de Product en la base de datos.
"""
from typing import List, Optional
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from app.models.products.product_model import Product, ProductIngredient


class ProductsRepository:
    """
    Repositorio para gestionar operaciones CRUD de Product y ProductIngredient.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_product(
        self,
        business_id: int,
        name: str,
        description: Optional[str],
        category: Optional[str],
        sale_price: Decimal,
        total_cost: Decimal,
        profit_margin_percentage: Optional[Decimal],
        profit_amount: Optional[Decimal],
        image_url: Optional[str],
    ) -> Product:
        """Crear un nuevo producto"""
        product = Product(
            business_id=business_id,
            name=name,
            description=description,
            category=category,
            sale_price=sale_price,
            total_cost=total_cost,
            profit_margin_percentage=profit_margin_percentage,
            profit_amount=profit_amount,
            image_url=image_url,
        )
        self.db.add(product)
        await self.db.flush()
        return product

    async def add_ingredient(
        self,
        product_id: int,
        inventory_item_id: int,
        quantity: Decimal,
        unit_cost: Decimal,
        total_cost: Decimal,
    ) -> ProductIngredient:
        """Agregar un ingrediente a un producto"""
        ingredient = ProductIngredient(
            product_id=product_id,
            inventory_item_id=inventory_item_id,
            quantity=quantity,
            unit_cost=unit_cost,
            total_cost=total_cost,
        )
        self.db.add(ingredient)
        await self.db.flush()
        return ingredient

    async def get_by_id(self, product_id: int, business_id: int) -> Optional[Product]:
        """Obtener producto por ID con ingredientes"""
        result = await self.db.execute(
            select(Product)
            .options(
                selectinload(Product.ingredients).selectinload(ProductIngredient.inventory_item),
            )
            .where(and_(Product.id == product_id, Product.business_id == business_id))
        )
        return result.scalar_one_or_none()

    async def get_all_by_business(
        self,
        business_id: int,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = False,
        category: Optional[str] = None,
    ) -> List[Product]:
        """Obtener todos los productos de un negocio"""
        query = select(Product).options(
            selectinload(Product.ingredients)
        ).where(Product.business_id == business_id)

        if active_only:
            query = query.where(Product.is_active == True)

        if category:
            query = query.where(Product.category == category)

        query = query.order_by(Product.name).offset(skip).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update(self, product: Product) -> Product:
        """Actualizar un producto"""
        await self.db.commit()
        await self.db.refresh(product)
        return product

    async def delete_ingredients(self, product: Product):
        """Eliminar todos los ingredientes de un producto"""
        for ingredient in product.ingredients:
            await self.db.delete(ingredient)
        await self.db.flush()

    async def commit(self):
        """Hacer commit de los cambios"""
        await self.db.commit()
