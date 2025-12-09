from fastapi import APIRouter, Query, Depends, Path
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.config.database import get_db
from app.controllers.employees.employees_controller import EmployeesController
from app.schemas.employees.employee_schema import (
    EmployeeCreateRequest,
    EmployeeUpdateRequest,
    EmployeeResponse,
)
from app.dependencies.auth_dependencies import (
    require_owner,
    require_owner_or_admin,
    get_current_user,
)
from app.models.users.user_model import User

router = APIRouter(
    prefix="/employees",
    tags=["Employees"],
)


@router.post("/", response_model=EmployeeResponse, status_code=201)
async def create_employee(
    data: EmployeeCreateRequest,
    current_user: User = Depends(require_owner_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Crea un nuevo empleado.

    Requiere rol: OWNER o ADMIN

    Validaciones:
    - No se puede usar un email ya existente en el negocio
    - No se puede crear un empleado con rol mayor o igual al del creador
    - OWNER puede crear: ADMIN, CASHIER, WAITER, COOK
    - ADMIN puede crear: CASHIER, WAITER, COOK

    Si no se proporciona contraseña, se genera automáticamente y se retorna en `temporary_password`.
    """
    return await EmployeesController.create_employee(data, current_user, db)


@router.get("/", response_model=List[EmployeeResponse])
async def get_employees(
    skip: int = Query(0, ge=0, description="Número de registros a omitir"),
    limit: int = Query(100, ge=1, le=100, description="Número máximo de registros"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Obtiene todos los empleados del negocio.

    Requiere autenticación.

    Solo retorna empleados del mismo business_id (multi-tenant).
    """
    return await EmployeesController.get_employees(skip, limit, current_user, db)


@router.get("/{employee_id}", response_model=EmployeeResponse)
async def get_employee(
    employee_id: int = Path(..., description="ID del empleado"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Obtiene un empleado por ID.

    Requiere autenticación.

    Solo se pueden obtener empleados del mismo business_id (multi-tenant).
    """
    return await EmployeesController.get_employee(employee_id, current_user, db)


@router.put("/{employee_id}", response_model=EmployeeResponse)
async def update_employee(
    employee_id: int = Path(..., description="ID del empleado"),
    data: EmployeeUpdateRequest = ...,
    current_user: User = Depends(require_owner_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Actualiza un empleado existente.

    Requiere rol: OWNER o ADMIN

    Campos editables:
    - full_name
    - email
    - phone
    - role
    - is_active

    Validaciones:
    - No se puede actualizar un empleado de mayor jerarquía
    - No se puede cambiar el propio rol
    - No se puede cambiar el email a uno ya existente
    - Los empleados no pueden cambiarse su propio rol

    Todos los cambios quedan registrados en la auditoría.
    """
    return await EmployeesController.update_employee(employee_id, data, current_user, db)


@router.delete("/{employee_id}", response_model=EmployeeResponse)
async def deactivate_employee(
    employee_id: int = Path(..., description="ID del empleado"),
    current_user: User = Depends(require_owner_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Inactiva un empleado (primera fase de eliminación).

    Requiere rol: OWNER o ADMIN

    Validaciones:
    - El owner no puede eliminarse a sí mismo
    - El admin no puede eliminar al owner
    - No se puede eliminar un empleado de mayor jerarquía

    La acción queda registrada en la auditoría.

    Para eliminar permanentemente, usar DELETE /employees/{employee_id}/permanent (solo OWNER).
    """
    return await EmployeesController.deactivate_employee(employee_id, current_user, db)


@router.delete("/{employee_id}/permanent", response_model=Dict[str, str])
async def delete_employee_permanently(
    employee_id: int = Path(..., description="ID del empleado"),
    current_user: User = Depends(require_owner),
    db: AsyncSession = Depends(get_db),
):
    """
    Elimina permanentemente un empleado de la base de datos.

    Requiere rol: OWNER (solo el owner puede realizar esta acción)

    Validaciones:
    - Solo el OWNER puede eliminar permanentemente
    - El owner no puede eliminarse a sí mismo
    - El empleado debe estar inactivo primero (usar DELETE /employees/{employee_id})

    Esta acción es irreversible y queda registrada en la auditoría.
    """
    return await EmployeesController.delete_employee_permanently(employee_id, current_user, db)
