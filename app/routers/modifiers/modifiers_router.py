"""
Router para Modificadores.
Define los endpoints REST para gestión de modificadores.
"""
from fastapi import APIRouter, Depends, Path, Query
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.config.database import get_db
from app.controllers.modifiers.modifiers_controller import ModifiersController
from app.schemas.modifiers.modifier_schema import (
    ModifierGroupCreate,
    ModifierGroupUpdate,
    ModifierGroupResponse,
    ModifierCreate,
    ModifierUpdate,
    ModifierResponse,
    ModifierListResponse,
    ProductModifierAssign,
    ProductModifierResponse,
)
from app.dependencies.auth_dependencies import get_current_user
from app.models.users.user_model import User

router = APIRouter(
    prefix="/modifiers",
    tags=["Modifiers"],
)


# ============= MODIFIER GROUP ENDPOINTS =============

@router.post("/groups", response_model=ModifierGroupResponse, status_code=201)
async def create_modifier_group(
    data: ModifierGroupCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Crea un nuevo grupo de modificadores.

    Requiere rol: OWNER, ADMIN o COOK

    Un grupo puede contener múltiples modificadores (ej: "Tamaño", "Extras").
    """
    return await ModifiersController.create_modifier_group(data, current_user, db)


@router.get("/groups", response_model=List[ModifierGroupResponse])
async def get_modifier_groups(
    skip: int = Query(0, ge=0, description="Número de registros a omitir"),
    limit: int = Query(100, ge=1, le=100, description="Número máximo de registros"),
    active_only: bool = Query(False, description="Filtrar solo grupos activos"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Obtiene todos los grupos de modificadores del negocio.

    Requiere autenticación.
    """
    return await ModifiersController.get_all_modifier_groups(
        skip, limit, active_only, current_user, db
    )


@router.get("/groups/{group_id}", response_model=ModifierGroupResponse)
async def get_modifier_group(
    group_id: int = Path(..., description="ID del grupo"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Obtiene un grupo de modificadores por ID.

    Requiere autenticación.
    """
    return await ModifiersController.get_modifier_group_by_id(group_id, current_user, db)


@router.put("/groups/{group_id}", response_model=ModifierGroupResponse)
async def update_modifier_group(
    group_id: int = Path(..., description="ID del grupo"),
    data: ModifierGroupUpdate = ...,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Actualiza un grupo de modificadores.

    Requiere rol: OWNER, ADMIN o COOK
    """
    return await ModifiersController.update_modifier_group(
        group_id, data, current_user, db
    )


# ============= MODIFIER ENDPOINTS =============

@router.post("/", response_model=ModifierResponse, status_code=201)
async def create_modifier(
    data: ModifierCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Crea un nuevo modificador con sus ítems de inventario.

    Requiere rol: OWNER, ADMIN o COOK

    Validaciones:
    - El nombre no debe repetirse dentro del mismo grupo
    - Todos los ítems de inventario deben existir y estar activos
    - La cantidad no puede ser 0 (positivo = agregar, negativo = quitar)
    """
    return await ModifiersController.create_modifier(data, current_user, db)


@router.get("/groups/{group_id}/modifiers", response_model=List[ModifierListResponse])
async def get_modifiers_by_group(
    group_id: int = Path(..., description="ID del grupo"),
    active_only: bool = Query(False, description="Filtrar solo modificadores activos"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Obtiene todos los modificadores de un grupo.

    Requiere autenticación.
    """
    return await ModifiersController.get_modifiers_by_group(
        group_id, active_only, current_user, db
    )


@router.get("/{modifier_id}", response_model=ModifierResponse)
async def get_modifier(
    modifier_id: int = Path(..., description="ID del modificador"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Obtiene un modificador por ID con todos sus ítems de inventario.

    Requiere autenticación.
    """
    return await ModifiersController.get_modifier_by_id(modifier_id, current_user, db)


@router.put("/{modifier_id}", response_model=ModifierResponse)
async def update_modifier(
    modifier_id: int = Path(..., description="ID del modificador"),
    data: ModifierUpdate = ...,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Actualiza un modificador (sin modificar ítems de inventario).

    Requiere rol: OWNER, ADMIN o COOK

    Validaciones:
    - El nombre no debe repetirse dentro del mismo grupo
    """
    return await ModifiersController.update_modifier(modifier_id, data, current_user, db)


# ============= PRODUCT MODIFIER ENDPOINTS =============

@router.post("/products/{product_id}/modifiers", response_model=ProductModifierResponse, status_code=201)
async def assign_modifier_to_product(
    product_id: int = Path(..., description="ID del producto"),
    data: ProductModifierAssign = ...,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Asigna un modificador a un producto.

    Requiere rol: OWNER, ADMIN o COOK

    VALIDACIÓN CRÍTICA DE COMPATIBILIDAD:
    Todos los ítems de inventario del modificador deben existir
    en los ingredientes del producto. Por ejemplo, un modificador
    de "Doble carne" solo puede asignarse a productos que tengan
    carne en sus ingredientes.
    """
    return await ModifiersController.assign_modifier_to_product(
        product_id, data, current_user, db
    )


@router.get("/products/{product_id}/modifiers", response_model=List[ProductModifierResponse])
async def get_product_modifiers(
    product_id: int = Path(..., description="ID del producto"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Obtiene todos los modificadores asignados a un producto.

    Requiere autenticación.
    """
    return await ModifiersController.get_modifiers_for_product(
        product_id, current_user, db
    )


@router.delete("/products/{product_id}/modifiers/{modifier_id}", status_code=204)
async def remove_modifier_from_product(
    product_id: int = Path(..., description="ID del producto"),
    modifier_id: int = Path(..., description="ID del modificador"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Desasigna un modificador de un producto.

    Requiere rol: OWNER, ADMIN o COOK
    """
    await ModifiersController.remove_modifier_from_product(
        product_id, modifier_id, current_user, db
    )
