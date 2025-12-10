"""
Router para Productos/Recetas.
Define los endpoints REST para gestión de productos.
"""
from fastapi import APIRouter, Depends, Path, Query
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.config.database import get_db
from app.controllers.products.products_controller import ProductsController
from app.schemas.products.product_schema import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductListResponse,
    IngredientUpdate,
)
from app.dependencies.auth_dependencies import get_current_user
from app.models.users.user_model import User

router = APIRouter(
    prefix="/products",
    tags=["Products"],
)


@router.post("/", response_model=ProductResponse, status_code=201)
async def create_product(
    data: ProductCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Crea un nuevo producto/receta con sus ingredientes.

    Requiere rol: OWNER, ADMIN o COOK

    Validaciones:
    - Todos los ingredientes deben existir y estar activos
    - No puede haber ingredientes duplicados
    - El precio de venta debe ser >= costo total
    """
    return await ProductsController.create_product(data, current_user, db)


@router.get("/", response_model=List[ProductListResponse])
async def get_products(
    skip: int = Query(0, ge=0, description="Número de registros a omitir"),
    limit: int = Query(100, ge=1, le=100, description="Número máximo de registros"),
    active_only: bool = Query(False, description="Filtrar solo productos activos"),
    category: Optional[str] = Query(None, description="Filtrar por categoría"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Obtiene todos los productos del negocio con paginación y filtros.

    Requiere autenticación.
    """
    return await ProductsController.get_all_products(
        skip, limit, active_only, category, current_user, db
    )


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int = Path(..., description="ID del producto"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Obtiene un producto por ID con todos sus ingredientes.

    Requiere autenticación.
    """
    return await ProductsController.get_product_by_id(product_id, current_user, db)


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int = Path(..., description="ID del producto"),
    data: ProductUpdate = ...,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Actualiza un producto (sin modificar ingredientes).

    Requiere rol: OWNER, ADMIN o COOK

    Validaciones:
    - El precio de venta debe ser >= costo total
    """
    return await ProductsController.update_product(product_id, data, current_user, db)


@router.put("/{product_id}/ingredients", response_model=ProductResponse)
async def update_product_ingredients(
    product_id: int = Path(..., description="ID del producto"),
    data: IngredientUpdate = ...,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Actualiza los ingredientes de un producto.

    Requiere rol: OWNER, ADMIN o COOK

    IMPORTANTE: Esta operación elimina todos los ingredientes anteriores
    y crea los nuevos. El costo total se recalcula automáticamente.

    Validaciones:
    - Todos los ingredientes deben existir y estar activos
    - El precio de venta actual debe ser >= nuevo costo total
    """
    return await ProductsController.update_ingredients(product_id, data, current_user, db)


@router.delete("/{product_id}", response_model=ProductResponse)
async def deactivate_product(
    product_id: int = Path(..., description="ID del producto"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Inactiva un producto (soft delete).

    Requiere rol: OWNER, ADMIN o COOK
    """
    return await ProductsController.deactivate_product(product_id, current_user, db)
