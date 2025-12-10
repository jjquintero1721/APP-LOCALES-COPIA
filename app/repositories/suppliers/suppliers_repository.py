"""
Repositorio para operaciones de Supplier en la base de datos.
TODOS los queries filtran por business_id (multi-tenant).
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
from app.models.suppliers.supplier_model import Supplier


class SuppliersRepository:
    """
    Repositorio para gestionar operaciones CRUD de Supplier.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        business_id: int,
        name: str,
        supplier_type: Optional[str],
        tax_id: Optional[str],
        legal_representative: Optional[str],
        phone: Optional[str],
        email: Optional[str],
        address: Optional[str],
    ) -> Supplier:
        """Crear un nuevo proveedor"""
        supplier = Supplier(
            business_id=business_id,
            name=name,
            supplier_type=supplier_type,
            tax_id=tax_id,
            legal_representative=legal_representative,
            phone=phone,
            email=email,
            address=address,
        )
        self.db.add(supplier)
        await self.db.commit()
        await self.db.refresh(supplier)
        return supplier

    async def get_by_id(self, supplier_id: int, business_id: int) -> Optional[Supplier]:
        """Obtener proveedor por ID (filtrado por business_id)"""
        result = await self.db.execute(
            select(Supplier)
            .options(selectinload(Supplier.business))
            .where(and_(Supplier.id == supplier_id, Supplier.business_id == business_id))
        )
        return result.scalar_one_or_none()

    async def get_all_by_business(
        self,
        business_id: int,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = False,
    ) -> List[Supplier]:
        """Obtener todos los proveedores de un negocio con paginación"""
        query = select(Supplier).where(Supplier.business_id == business_id)

        if active_only:
            query = query.where(Supplier.is_active == True)

        query = query.offset(skip).limit(limit).order_by(Supplier.name)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def email_exists(self, email: str, business_id: int, exclude_id: Optional[int] = None) -> bool:
        """Verificar si un email ya existe para el negocio (excluyendo opcionalmente un ID)"""
        query = select(Supplier).where(
            and_(
                Supplier.email == email,
                Supplier.business_id == business_id,
            )
        )

        if exclude_id:
            query = query.where(Supplier.id != exclude_id)

        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None

    async def tax_id_exists(self, tax_id: str, business_id: int, exclude_id: Optional[int] = None) -> bool:
        """Verificar si un tax_id ya existe para el negocio (excluyendo opcionalmente un ID)"""
        query = select(Supplier).where(
            and_(
                Supplier.tax_id == tax_id,
                Supplier.business_id == business_id,
            )
        )

        if exclude_id:
            query = query.where(Supplier.id != exclude_id)

        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None

    async def update(self, supplier: Supplier) -> Supplier:
        """Actualizar proveedor existente"""
        await self.db.commit()
        await self.db.refresh(supplier)
        return supplier

    async def delete_permanently(self, supplier: Supplier) -> None:
        """Eliminar proveedor permanentemente de la base de datos"""
        await self.db.delete(supplier)
        await self.db.commit()
