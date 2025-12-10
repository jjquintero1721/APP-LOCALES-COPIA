"""
Servicio de Productos/Recetas.
Maneja operaciones CRUD de productos con cálculos de costos y auditoría.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from typing import List, Optional
from decimal import Decimal
from app.repositories.products.products_repository import ProductsRepository
from app.repositories.inventory.inventory_items_repository import InventoryItemsRepository
from app.repositories.inventory.inventory_movements_repository import InventoryMovementsRepository
from app.repositories.audit.audit_repository import AuditRepository
from app.schemas.products.product_schema import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductListResponse,
    ProductIngredientResponse,
    IngredientUpdate,
)
from app.models.users.user_model import User, UserRole
from app.models.inventory.inventory_enums import MovementType


class ProductsService:
    """
    Servicio de productos.
    Maneja operaciones CRUD de productos con validaciones y auditoría completa.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.products_repo = ProductsRepository(db)
        self.items_repo = InventoryItemsRepository(db)
        self.movements_repo = InventoryMovementsRepository(db)
        self.audit_repo = AuditRepository(db)

    async def create_product(
        self,
        data: ProductCreate,
        current_user: User,
    ) -> ProductResponse:
        """
        Crea un nuevo producto con sus ingredientes.

        Validaciones:
        - Solo OWNER, ADMIN y COOK pueden crear productos
        - Todos los ingredientes deben existir y estar activos
        - No puede haber ingredientes duplicados
        - sale_price >= total_cost

        Args:
            data: Datos del producto
            current_user: Usuario que crea el producto

        Returns:
            ProductResponse con los datos del producto creado
        """
        # Validar que el usuario sea OWNER, ADMIN o COOK
        if current_user.role not in [UserRole.OWNER, UserRole.ADMIN, UserRole.COOK]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo los roles OWNER, ADMIN y COOK pueden crear productos.",
            )

        # Validar y calcular costos de ingredientes
        total_cost = Decimal(0)
        ingredients_data = []

        for ing_data in data.ingredients:
            # Validar que el ingrediente exista y pertenezca al negocio
            item = await self.items_repo.get_by_id(ing_data.inventory_item_id, current_user.business_id)
            if not item:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"El ítem con ID {ing_data.inventory_item_id} no existe o no pertenece a tu negocio.",
                )

            # Validar que el ítem esté activo
            if not item.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"El ingrediente '{item.name}' está inactivo. No se puede usar en el producto.",
                )

            # Calcular costo del ingrediente
            unit_cost = item.unit_price
            ingredient_total_cost = unit_cost * ing_data.quantity
            total_cost += ingredient_total_cost

            ingredients_data.append({
                "inventory_item_id": ing_data.inventory_item_id,
                "quantity": ing_data.quantity,
                "unit_cost": unit_cost,
                "total_cost": ingredient_total_cost,
            })

        # Validar que sale_price >= total_cost
        if data.sale_price < total_cost:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El precio de venta ({data.sale_price}) debe ser mayor o igual al costo total ({total_cost}).",
            )

        # Calcular márgenes
        profit_amount = data.sale_price - total_cost

        # Si el usuario especificó un margen, validar que sea correcto
        if data.profit_margin_percentage is not None:
            expected_sale_price = total_cost * (Decimal(1) + data.profit_margin_percentage / Decimal(100))
            if abs(data.sale_price - expected_sale_price) > Decimal('0.01'):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"El margen de ganancia especificado ({data.profit_margin_percentage}%) no coincide con el precio de venta.",
                )
            profit_margin = data.profit_margin_percentage
        else:
            # Calcular el margen basado en el precio de venta
            profit_margin = (profit_amount / data.sale_price * Decimal(100)) if data.sale_price > 0 else Decimal(0)

        # Crear el producto
        product = await self.products_repo.create_product(
            business_id=current_user.business_id,
            name=data.name,
            description=data.description,
            category=data.category,
            sale_price=data.sale_price,
            total_cost=total_cost,
            profit_margin_percentage=profit_margin,
            profit_amount=profit_amount,
            image_url=data.image_url,
        )

        # Crear los ingredientes
        for ing_data in ingredients_data:
            await self.products_repo.add_ingredient(
                product_id=product.id,
                inventory_item_id=ing_data["inventory_item_id"],
                quantity=ing_data["quantity"],
                unit_cost=ing_data["unit_cost"],
                total_cost=ing_data["total_cost"],
            )

        await self.products_repo.commit()

        # Registrar auditoría
        await self.audit_repo.create_log(
            business_id=current_user.business_id,
            user_id=current_user.id,
            action=f"Producto creado: {product.name} (ID: {product.id}) con {len(ingredients_data)} ingredientes por {current_user.full_name}",
        )

        # Cargar el producto con todas las relaciones
        product_with_relations = await self.products_repo.get_by_id(product.id, current_user.business_id)

        return self._build_response(product_with_relations)

    async def get_product_by_id(
        self,
        product_id: int,
        current_user: User,
    ) -> ProductResponse:
        """Obtiene un producto por ID"""
        product = await self.products_repo.get_by_id(product_id, current_user.business_id)

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Producto no encontrado.",
            )

        return self._build_response(product)

    async def get_all_products(
        self,
        current_user: User,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = False,
        category: Optional[str] = None,
    ) -> List[ProductListResponse]:
        """Obtiene todos los productos del negocio"""
        products = await self.products_repo.get_all_by_business(
            business_id=current_user.business_id,
            skip=skip,
            limit=limit,
            active_only=active_only,
            category=category,
        )

        return [self._build_list_response(product) for product in products]

    async def update_product(
        self,
        product_id: int,
        data: ProductUpdate,
        current_user: User,
    ) -> ProductResponse:
        """
        Actualiza un producto (sin modificar ingredientes).

        Validaciones:
        - Solo OWNER, ADMIN y COOK pueden actualizar
        - Si se actualiza sale_price, debe ser >= total_cost

        Args:
            product_id: ID del producto
            data: Datos a actualizar
            current_user: Usuario que actualiza

        Returns:
            ProductResponse con los datos actualizados
        """
        # Validar que el usuario sea OWNER, ADMIN o COOK
        if current_user.role not in [UserRole.OWNER, UserRole.ADMIN, UserRole.COOK]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo los roles OWNER, ADMIN y COOK pueden actualizar productos.",
            )

        # Obtener el producto
        product = await self.products_repo.get_by_id(product_id, current_user.business_id)

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Producto no encontrado.",
            )

        # Validar sale_price >= total_cost
        new_sale_price = data.sale_price if data.sale_price is not None else product.sale_price
        if new_sale_price < product.total_cost:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El precio de venta ({new_sale_price}) debe ser mayor o igual al costo total ({product.total_cost}).",
            )

        # Registrar cambios para auditoría
        changes = []
        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            old_value = getattr(product, field)
            if value != old_value:
                setattr(product, field, value)
                changes.append(f"{field}: '{old_value}' → '{value}'")

        # Recalcular profit_amount y profit_margin si cambió el precio
        if data.sale_price is not None:
            product.profit_amount = product.sale_price - product.total_cost
            product.profit_margin_percentage = (
                (product.profit_amount / product.sale_price * Decimal(100))
                if product.sale_price > 0 else Decimal(0)
            )

        # Solo actualizar si hay cambios
        if changes:
            updated_product = await self.products_repo.update(product)

            # Registrar auditoría
            await self.audit_repo.create_log(
                business_id=current_user.business_id,
                user_id=current_user.id,
                action=f"Producto actualizado: {updated_product.name} (ID: {updated_product.id}). Cambios: {', '.join(changes)}. Actualizado por {current_user.full_name}",
            )

            return self._build_response(updated_product)

        return self._build_response(product)

    async def update_ingredients(
        self,
        product_id: int,
        data: IngredientUpdate,
        current_user: User,
    ) -> ProductResponse:
        """
        Actualiza los ingredientes de un producto.
        Elimina todos los ingredientes anteriores y crea los nuevos.

        Args:
            product_id: ID del producto
            data: Nuevos ingredientes
            current_user: Usuario que actualiza

        Returns:
            ProductResponse con los datos actualizados
        """
        # Validar que el usuario sea OWNER, ADMIN o COOK
        if current_user.role not in [UserRole.OWNER, UserRole.ADMIN, UserRole.COOK]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo los roles OWNER, ADMIN y COOK pueden actualizar ingredientes.",
            )

        # Obtener el producto
        product = await self.products_repo.get_by_id(product_id, current_user.business_id)

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Producto no encontrado.",
            )

        # Validar y calcular costos de ingredientes
        total_cost = Decimal(0)
        ingredients_data = []

        for ing_data in data.ingredients:
            # Validar que el ingrediente exista y pertenezca al negocio
            item = await self.items_repo.get_by_id(ing_data.inventory_item_id, current_user.business_id)
            if not item:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"El ítem con ID {ing_data.inventory_item_id} no existe o no pertenece a tu negocio.",
                )

            # Validar que el ítem esté activo
            if not item.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"El ingrediente '{item.name}' está inactivo. No se puede usar en el producto.",
                )

            # Calcular costo del ingrediente
            unit_cost = item.unit_price
            ingredient_total_cost = unit_cost * ing_data.quantity
            total_cost += ingredient_total_cost

            ingredients_data.append({
                "inventory_item_id": ing_data.inventory_item_id,
                "quantity": ing_data.quantity,
                "unit_cost": unit_cost,
                "total_cost": ingredient_total_cost,
            })

        # Validar que sale_price >= nuevo total_cost
        if product.sale_price < total_cost:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El precio de venta actual ({product.sale_price}) es menor al nuevo costo total ({total_cost}). Actualiza el precio de venta primero.",
            )

        # Eliminar ingredientes anteriores
        await self.products_repo.delete_ingredients(product)

        # Crear los nuevos ingredientes
        for ing_data in ingredients_data:
            await self.products_repo.add_ingredient(
                product_id=product.id,
                inventory_item_id=ing_data["inventory_item_id"],
                quantity=ing_data["quantity"],
                unit_cost=ing_data["unit_cost"],
                total_cost=ing_data["total_cost"],
            )

        # Actualizar costos y márgenes del producto
        product.total_cost = total_cost
        product.profit_amount = product.sale_price - total_cost
        product.profit_margin_percentage = (
            (product.profit_amount / product.sale_price * Decimal(100))
            if product.sale_price > 0 else Decimal(0)
        )

        await self.products_repo.commit()

        # Registrar auditoría
        await self.audit_repo.create_log(
            business_id=current_user.business_id,
            user_id=current_user.id,
            action=f"Ingredientes actualizados para producto: {product.name} (ID: {product.id}). Nuevo costo total: {total_cost}. Actualizado por {current_user.full_name}",
        )

        # Cargar el producto con todas las relaciones
        updated_product = await self.products_repo.get_by_id(product.id, current_user.business_id)

        return self._build_response(updated_product)

    async def deactivate_product(
        self,
        product_id: int,
        current_user: User,
    ) -> ProductResponse:
        """Inactiva un producto (soft delete)"""
        # Validar que el usuario sea OWNER, ADMIN o COOK
        if current_user.role not in [UserRole.OWNER, UserRole.ADMIN, UserRole.COOK]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo los roles OWNER, ADMIN y COOK pueden inactivar productos.",
            )

        # Obtener el producto
        product = await self.products_repo.get_by_id(product_id, current_user.business_id)

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Producto no encontrado.",
            )

        if not product.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El producto ya está inactivo.",
            )

        # Inactivar
        product.is_active = False
        updated_product = await self.products_repo.update(product)

        # Registrar auditoría
        await self.audit_repo.create_log(
            business_id=current_user.business_id,
            user_id=current_user.id,
            action=f"Producto inactivado: {updated_product.name} (ID: {updated_product.id}) por {current_user.full_name}",
        )

        return self._build_response(updated_product)

    def _build_response(self, product) -> ProductResponse:
        """Construye la respuesta completa del producto con ingredientes"""
        ingredients_response = [
            ProductIngredientResponse(
                id=ing.id,
                product_id=ing.product_id,
                inventory_item_id=ing.inventory_item_id,
                inventory_item_name=ing.inventory_item.name,
                quantity=ing.quantity,
                unit_cost=ing.unit_cost,
                total_cost=ing.total_cost,
            )
            for ing in product.ingredients
        ]

        return ProductResponse(
            id=product.id,
            business_id=product.business_id,
            name=product.name,
            description=product.description,
            category=product.category,
            sale_price=product.sale_price,
            total_cost=product.total_cost,
            profit_margin_percentage=product.profit_margin_percentage,
            profit_amount=product.profit_amount,
            image_url=product.image_url,
            is_active=product.is_active,
            created_at=product.created_at,
            updated_at=product.updated_at,
            ingredients=ingredients_response,
        )

    def _build_list_response(self, product) -> ProductListResponse:
        """Construye la respuesta resumida del producto sin ingredientes"""
        return ProductListResponse(
            id=product.id,
            name=product.name,
            category=product.category,
            sale_price=product.sale_price,
            total_cost=product.total_cost,
            profit_margin_percentage=product.profit_margin_percentage,
            is_active=product.is_active,
            ingredients_count=len(product.ingredients),
        )
