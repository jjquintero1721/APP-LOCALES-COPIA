"""
Servicio de Proveedores.
Maneja operaciones CRUD de proveedores con validaciones y auditoría.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from typing import List
from app.repositories.suppliers.suppliers_repository import SuppliersRepository
from app.repositories.audit.audit_repository import AuditRepository
from app.schemas.suppliers.supplier_schema import (
    SupplierCreate,
    SupplierUpdate,
    SupplierResponse,
)
from app.models.users.user_model import User, UserRole


class SuppliersService:
    """
    Servicio de proveedores.
    Maneja operaciones CRUD de proveedores con validaciones y auditoría completa.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.suppliers_repo = SuppliersRepository(db)
        self.audit_repo = AuditRepository(db)

    async def create_supplier(
        self,
        data: SupplierCreate,
        current_user: User,
    ) -> SupplierResponse:
        """
        Crea un nuevo proveedor.

        Validaciones:
        - El email no debe existir en el negocio (si se proporciona)
        - El tax_id no debe existir en el negocio (si se proporciona)
        - Solo OWNER y ADMIN pueden crear proveedores

        Args:
            data: Datos del proveedor a crear
            current_user: Usuario que crea el proveedor

        Returns:
            SupplierResponse con los datos del proveedor creado
        """
        # Validar que el usuario sea OWNER o ADMIN
        if current_user.role not in [UserRole.OWNER, UserRole.ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo los roles OWNER y ADMIN pueden crear proveedores.",
            )

        # Validar email único (si se proporciona)
        if data.email:
            if await self.suppliers_repo.email_exists(data.email, current_user.business_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"El email {data.email} ya está registrado para otro proveedor en este negocio.",
                )

        # Validar tax_id único (si se proporciona)
        if data.tax_id:
            if await self.suppliers_repo.tax_id_exists(data.tax_id, current_user.business_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"El NIT/Tax ID {data.tax_id} ya está registrado para otro proveedor en este negocio.",
                )

        # Crear el proveedor
        supplier = await self.suppliers_repo.create(
            business_id=current_user.business_id,
            name=data.name,
            supplier_type=data.supplier_type,
            tax_id=data.tax_id,
            legal_representative=data.legal_representative,
            phone=data.phone,
            email=data.email,
            address=data.address,
        )

        # Registrar auditoría
        await self.audit_repo.create_log(
            business_id=current_user.business_id,
            user_id=current_user.id,
            action=f"Proveedor creado: {supplier.name} (ID: {supplier.id}) por {current_user.full_name}",
        )

        return SupplierResponse.model_validate(supplier)

    async def get_supplier_by_id(
        self,
        supplier_id: int,
        current_user: User,
    ) -> SupplierResponse:
        """
        Obtiene un proveedor por ID.

        Args:
            supplier_id: ID del proveedor
            current_user: Usuario actual

        Returns:
            SupplierResponse con los datos del proveedor
        """
        supplier = await self.suppliers_repo.get_by_id(supplier_id, current_user.business_id)

        if not supplier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Proveedor no encontrado.",
            )

        return SupplierResponse.model_validate(supplier)

    async def get_all_suppliers(
        self,
        current_user: User,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = False,
    ) -> List[SupplierResponse]:
        """
        Obtiene todos los proveedores del negocio con paginación.

        Args:
            current_user: Usuario actual
            skip: Número de registros a saltar
            limit: Número máximo de registros a retornar
            active_only: Si es True, solo retorna proveedores activos

        Returns:
            Lista de SupplierResponse
        """
        suppliers = await self.suppliers_repo.get_all_by_business(
            business_id=current_user.business_id,
            skip=skip,
            limit=limit,
            active_only=active_only,
        )

        return [SupplierResponse.model_validate(supplier) for supplier in suppliers]

    async def update_supplier(
        self,
        supplier_id: int,
        data: SupplierUpdate,
        current_user: User,
    ) -> SupplierResponse:
        """
        Actualiza un proveedor existente.

        Validaciones:
        - Solo OWNER y ADMIN pueden actualizar proveedores
        - El email no debe existir en otro proveedor del negocio
        - El tax_id no debe existir en otro proveedor del negocio

        Args:
            supplier_id: ID del proveedor a actualizar
            data: Datos a actualizar
            current_user: Usuario que realiza la actualización

        Returns:
            SupplierResponse con los datos actualizados
        """
        # Validar que el usuario sea OWNER o ADMIN
        if current_user.role not in [UserRole.OWNER, UserRole.ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo los roles OWNER y ADMIN pueden actualizar proveedores.",
            )

        # Obtener el proveedor
        supplier = await self.suppliers_repo.get_by_id(supplier_id, current_user.business_id)

        if not supplier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Proveedor no encontrado.",
            )

        # Validar email único (si se proporciona y cambió)
        if data.email and data.email != supplier.email:
            if await self.suppliers_repo.email_exists(data.email, current_user.business_id, exclude_id=supplier_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"El email {data.email} ya está registrado para otro proveedor en este negocio.",
                )

        # Validar tax_id único (si se proporciona y cambió)
        if data.tax_id and data.tax_id != supplier.tax_id:
            if await self.suppliers_repo.tax_id_exists(data.tax_id, current_user.business_id, exclude_id=supplier_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"El NIT/Tax ID {data.tax_id} ya está registrado para otro proveedor en este negocio.",
                )

        # Registrar cambios para auditoría
        changes = []
        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            old_value = getattr(supplier, field)
            if value != old_value:
                setattr(supplier, field, value)
                changes.append(f"{field}: '{old_value}' → '{value}'")

        # Solo actualizar si hay cambios
        if changes:
            updated_supplier = await self.suppliers_repo.update(supplier)

            # Registrar auditoría
            await self.audit_repo.create_log(
                business_id=current_user.business_id,
                user_id=current_user.id,
                action=f"Proveedor actualizado: {updated_supplier.name} (ID: {updated_supplier.id}). Cambios: {', '.join(changes)}. Actualizado por {current_user.full_name}",
            )

            return SupplierResponse.model_validate(updated_supplier)

        return SupplierResponse.model_validate(supplier)

    async def deactivate_supplier(
        self,
        supplier_id: int,
        current_user: User,
    ) -> SupplierResponse:
        """
        Inactiva un proveedor (soft delete).

        Args:
            supplier_id: ID del proveedor a inactivar
            current_user: Usuario que realiza la inactivación

        Returns:
            SupplierResponse con el proveedor inactivado
        """
        # Validar que el usuario sea OWNER o ADMIN
        if current_user.role not in [UserRole.OWNER, UserRole.ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo los roles OWNER y ADMIN pueden inactivar proveedores.",
            )

        # Obtener el proveedor
        supplier = await self.suppliers_repo.get_by_id(supplier_id, current_user.business_id)

        if not supplier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Proveedor no encontrado.",
            )

        if not supplier.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El proveedor ya está inactivo.",
            )

        # Inactivar
        supplier.is_active = False
        updated_supplier = await self.suppliers_repo.update(supplier)

        # Registrar auditoría
        await self.audit_repo.create_log(
            business_id=current_user.business_id,
            user_id=current_user.id,
            action=f"Proveedor inactivado: {updated_supplier.name} (ID: {updated_supplier.id}) por {current_user.full_name}",
        )

        return SupplierResponse.model_validate(updated_supplier)

    async def delete_supplier_permanently(
        self,
        supplier_id: int,
        current_user: User,
    ) -> None:
        """
        Elimina permanentemente un proveedor de la base de datos.
        Solo OWNER puede realizar esta operación.

        Args:
            supplier_id: ID del proveedor a eliminar
            current_user: Usuario que realiza la eliminación
        """
        # Solo OWNER puede eliminar permanentemente
        if current_user.role != UserRole.OWNER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo el OWNER puede eliminar proveedores permanentemente.",
            )

        # Obtener el proveedor
        supplier = await self.suppliers_repo.get_by_id(supplier_id, current_user.business_id)

        if not supplier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Proveedor no encontrado.",
            )

        # Registrar auditoría antes de eliminar
        await self.audit_repo.create_log(
            business_id=current_user.business_id,
            user_id=current_user.id,
            action=f"Proveedor eliminado permanentemente: {supplier.name} (ID: {supplier.id}, Tax ID: {supplier.tax_id}) por {current_user.full_name}",
        )

        # Eliminar
        await self.suppliers_repo.delete_permanently(supplier)
