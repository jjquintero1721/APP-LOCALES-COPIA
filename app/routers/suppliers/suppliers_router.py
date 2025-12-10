"""
Router para Proveedores.
Define los endpoints REST para gestión de proveedores.
"""
from fastapi import APIRouter, Query, Depends, Path
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.config.database import get_db
from app.controllers.suppliers.suppliers_controller import SuppliersController
from app.schemas.suppliers.supplier_schema import (
    SupplierCreate,
    SupplierUpdate,
    SupplierResponse,
)
from app.dependencies.auth_dependencies import (
    require_owner,
    require_owner_or_admin,
    get_current_user,
)
from app.models.users.user_model import User

router = APIRouter(
    prefix="/suppliers",
    tags=["Suppliers"],
)


@router.post("/", response_model=SupplierResponse, status_code=201)
async def create_supplier(
    data: SupplierCreate,
    current_user: User = Depends(require_owner_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Crea un nuevo proveedor.

    Requiere rol: OWNER o ADMIN

    Validaciones:
    - El email no debe existir en el negocio (si se proporciona)
    - El tax_id no debe existir en el negocio (si se proporciona)
    """
    return await SuppliersController.create_supplier(data, current_user, db)


@router.get("/", response_model=List[SupplierResponse])
async def get_suppliers(
    skip: int = Query(0, ge=0, description="Número de registros a omitir"),
    limit: int = Query(100, ge=1, le=100, description="Número máximo de registros"),
    active_only: bool = Query(False, description="Filtrar solo proveedores activos"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Obtiene todos los proveedores del negocio con paginación.

    Requiere autenticación.

    Solo retorna proveedores del mismo business_id (multi-tenant).
    """
    return await SuppliersController.get_all_suppliers(
        skip, limit, active_only, current_user, db
    )


@router.get("/{supplier_id}", response_model=SupplierResponse)
async def get_supplier(
    supplier_id: int = Path(..., description="ID del proveedor"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Obtiene un proveedor por ID.

    Requiere autenticación.

    Solo se pueden obtener proveedores del mismo business_id (multi-tenant).
    """
    return await SuppliersController.get_supplier_by_id(supplier_id, current_user, db)


@router.put("/{supplier_id}", response_model=SupplierResponse)
async def update_supplier(
    supplier_id: int = Path(..., description="ID del proveedor"),
    data: SupplierUpdate = ...,
    current_user: User = Depends(require_owner_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Actualiza un proveedor existente.

    Requiere rol: OWNER o ADMIN

    Validaciones:
    - El email no debe existir en otro proveedor del negocio
    - El tax_id no debe existir en otro proveedor del negocio
    """
    return await SuppliersController.update_supplier(
        supplier_id, data, current_user, db
    )


@router.delete("/{supplier_id}", response_model=SupplierResponse)
async def deactivate_supplier(
    supplier_id: int = Path(..., description="ID del proveedor"),
    current_user: User = Depends(require_owner_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Inactiva un proveedor (soft delete).

    Requiere rol: OWNER o ADMIN

    El proveedor no se elimina de la base de datos, solo se marca como inactivo.
    """
    return await SuppliersController.deactivate_supplier(supplier_id, current_user, db)


@router.delete("/{supplier_id}/permanent", status_code=204)
async def delete_supplier_permanently(
    supplier_id: int = Path(..., description="ID del proveedor"),
    current_user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    """
    Elimina permanentemente un proveedor de la base de datos.

    Requiere rol: OWNER únicamente

    ADVERTENCIA: Esta operación es irreversible.
    """
    await SuppliersController.delete_supplier_permanently(supplier_id, current_user, db)
