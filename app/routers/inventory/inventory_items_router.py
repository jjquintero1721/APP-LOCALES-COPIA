"""
Router para Ítems de Inventario.
Define los endpoints REST para gestión de ítems de inventario.
"""
from fastapi import APIRouter, Query, Depends, Path
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.config.database import get_db
from app.controllers.inventory.inventory_items_controller import InventoryItemsController
from app.schemas.inventory.inventory_item_schema import (
    InventoryItemCreate,
    InventoryItemUpdate,
    InventoryItemResponse,
    StockAdjustmentRequest,
)
from app.dependencies.auth_dependencies import (
    require_owner_or_admin,
    get_current_user,
)
from app.models.users.user_model import User

router = APIRouter(
    prefix="/inventory/items",
    tags=["Inventory Items"],
)


@router.post("/", response_model=InventoryItemResponse, status_code=201)
async def create_item(
    data: InventoryItemCreate,
    current_user: User = Depends(require_owner_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Crea un nuevo ítem de inventario.

    Requiere rol: OWNER o ADMIN

    Validaciones:
    - SKU único por negocio (si se proporciona)
    - Supplier debe existir y pertenecer al negocio (si se proporciona)
    - min_stock <= max_stock
    - Stock inicial >= 0
    """
    return await InventoryItemsController.create_item(data, current_user, db)


@router.get("/", response_model=List[InventoryItemResponse])
async def get_items(
    skip: int = Query(0, ge=0, description="Número de registros a omitir"),
    limit: int = Query(100, ge=1, le=100, description="Número máximo de registros"),
    active_only: bool = Query(False, description="Filtrar solo ítems activos"),
    category: Optional[str] = Query(None, description="Filtrar por categoría"),
    supplier_id: Optional[int] = Query(None, description="Filtrar por proveedor"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Obtiene todos los ítems de inventario del negocio con paginación y filtros.

    Requiere autenticación.

    Solo retorna ítems del mismo business_id (multi-tenant).
    """
    return await InventoryItemsController.get_all_items(
        skip, limit, active_only, category, supplier_id, current_user, db
    )


@router.get("/alerts/low-stock", response_model=List[InventoryItemResponse])
async def get_low_stock_alerts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Obtiene alertas de ítems con stock por debajo del mínimo.

    Requiere autenticación.

    Retorna ítems activos con quantity_in_stock < min_stock.
    """
    return await InventoryItemsController.get_low_stock_alerts(current_user, db)


@router.get("/{item_id}", response_model=InventoryItemResponse)
async def get_item(
    item_id: int = Path(..., description="ID del ítem"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Obtiene un ítem de inventario por ID.

    Requiere autenticación.

    Solo se pueden obtener ítems del mismo business_id (multi-tenant).
    """
    return await InventoryItemsController.get_item_by_id(item_id, current_user, db)


@router.put("/{item_id}", response_model=InventoryItemResponse)
async def update_item(
    item_id: int = Path(..., description="ID del ítem"),
    data: InventoryItemUpdate = ...,
    current_user: User = Depends(require_owner_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Actualiza un ítem de inventario existente (solo metadatos, no stock).

    Requiere rol: OWNER o ADMIN

    Para ajustar el stock, usar el endpoint /inventory/items/{item_id}/adjust

    Validaciones:
    - SKU único por negocio
    - Supplier debe existir y pertenecer al negocio
    - min_stock <= max_stock
    """
    return await InventoryItemsController.update_item(
        item_id, data, current_user, db
    )


@router.delete("/{item_id}", response_model=InventoryItemResponse)
async def deactivate_item(
    item_id: int = Path(..., description="ID del ítem"),
    current_user: User = Depends(require_owner_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Inactiva un ítem de inventario (soft delete).

    Requiere rol: OWNER o ADMIN

    El ítem no se elimina de la base de datos, solo se marca como inactivo.
    """
    return await InventoryItemsController.deactivate_item(item_id, current_user, db)


@router.post("/{item_id}/adjust", response_model=InventoryItemResponse)
async def adjust_stock_manually(
    item_id: int = Path(..., description="ID del ítem"),
    data: StockAdjustmentRequest = ...,
    current_user: User = Depends(require_owner_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Ajusta el stock de un ítem manualmente (entrada o salida).

    Requiere rol: OWNER o ADMIN

    Validaciones:
    - El stock resultante no puede ser negativo
    - El motivo es obligatorio
    - quantity_change puede ser positivo (entrada) o negativo (salida)
    - Crea un movimiento MANUAL_IN o MANUAL_OUT

    Ejemplos:
    - Entrada: quantity_change = 10, reason = "Compra a proveedor"
    - Salida: quantity_change = -5, reason = "Merma por vencimiento"
    """
    return await InventoryItemsController.adjust_stock_manually(
        item_id, data, current_user, db
    )
