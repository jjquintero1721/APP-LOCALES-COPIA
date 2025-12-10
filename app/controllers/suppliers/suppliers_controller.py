"""
Controller para Proveedores.
Capa delgada que delega al servicio de proveedores.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.services.suppliers.suppliers_service import SuppliersService
from app.schemas.suppliers.supplier_schema import (
    SupplierCreate,
    SupplierUpdate,
    SupplierResponse,
)
from app.models.users.user_model import User


class SuppliersController:
    """
    Controller para gestionar endpoints de proveedores.
    """

    @staticmethod
    async def create_supplier(
        data: SupplierCreate,
        current_user: User,
        db: AsyncSession,
    ) -> SupplierResponse:
        """Crear un nuevo proveedor"""
        suppliers_service = SuppliersService(db)
        return await suppliers_service.create_supplier(data, current_user)

    @staticmethod
    async def get_supplier_by_id(
        supplier_id: int,
        current_user: User,
        db: AsyncSession,
    ) -> SupplierResponse:
        """Obtener un proveedor por ID"""
        suppliers_service = SuppliersService(db)
        return await suppliers_service.get_supplier_by_id(supplier_id, current_user)

    @staticmethod
    async def get_all_suppliers(
        skip: int,
        limit: int,
        active_only: bool,
        current_user: User,
        db: AsyncSession,
    ) -> List[SupplierResponse]:
        """Obtener todos los proveedores con paginación"""
        suppliers_service = SuppliersService(db)
        return await suppliers_service.get_all_suppliers(
            current_user,
            skip=skip,
            limit=limit,
            active_only=active_only,
        )

    @staticmethod
    async def update_supplier(
        supplier_id: int,
        data: SupplierUpdate,
        current_user: User,
        db: AsyncSession,
    ) -> SupplierResponse:
        """Actualizar un proveedor"""
        suppliers_service = SuppliersService(db)
        return await suppliers_service.update_supplier(supplier_id, data, current_user)

    @staticmethod
    async def deactivate_supplier(
        supplier_id: int,
        current_user: User,
        db: AsyncSession,
    ) -> SupplierResponse:
        """Inactivar un proveedor (soft delete)"""
        suppliers_service = SuppliersService(db)
        return await suppliers_service.deactivate_supplier(supplier_id, current_user)

    @staticmethod
    async def delete_supplier_permanently(
        supplier_id: int,
        current_user: User,
        db: AsyncSession,
    ) -> None:
        """Eliminar permanentemente un proveedor"""
        suppliers_service = SuppliersService(db)
        return await suppliers_service.delete_supplier_permanently(supplier_id, current_user)
