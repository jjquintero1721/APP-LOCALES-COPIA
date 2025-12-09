from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
from app.services.employees.employees_service import EmployeesService
from app.schemas.employees.employee_schema import (
    EmployeeCreateRequest,
    EmployeeUpdateRequest,
    EmployeeResponse,
)
from app.models.users.user_model import User


class EmployeesController:
    """
    Controller de empleados.
    Maneja los requests HTTP y delega la lógica al servicio.
    """

    @staticmethod
    async def create_employee(
        data: EmployeeCreateRequest,
        current_user: User,
        db: AsyncSession,
    ) -> EmployeeResponse:
        """
        Endpoint: POST /employees
        Crea un nuevo empleado.
        """
        employees_service = EmployeesService(db)
        return await employees_service.create_employee(data, current_user)

    @staticmethod
    async def get_employee(
        employee_id: int,
        current_user: User,
        db: AsyncSession,
    ) -> EmployeeResponse:
        """
        Endpoint: GET /employees/{employee_id}
        Obtiene un empleado por ID.
        """
        employees_service = EmployeesService(db)
        return await employees_service.get_employee_by_id(employee_id, current_user)

    @staticmethod
    async def get_employees(
        skip: int,
        limit: int,
        current_user: User,
        db: AsyncSession,
    ) -> List[EmployeeResponse]:
        """
        Endpoint: GET /employees
        Obtiene todos los empleados del negocio.
        """
        employees_service = EmployeesService(db)
        return await employees_service.get_all_employees(current_user, skip, limit)

    @staticmethod
    async def update_employee(
        employee_id: int,
        data: EmployeeUpdateRequest,
        current_user: User,
        db: AsyncSession,
    ) -> EmployeeResponse:
        """
        Endpoint: PUT /employees/{employee_id}
        Actualiza un empleado existente.
        """
        employees_service = EmployeesService(db)
        return await employees_service.update_employee(employee_id, data, current_user)

    @staticmethod
    async def deactivate_employee(
        employee_id: int,
        current_user: User,
        db: AsyncSession,
    ) -> EmployeeResponse:
        """
        Endpoint: DELETE /employees/{employee_id}
        Inactiva un empleado.
        """
        employees_service = EmployeesService(db)
        return await employees_service.deactivate_employee(employee_id, current_user)

    @staticmethod
    async def delete_employee_permanently(
        employee_id: int,
        current_user: User,
        db: AsyncSession,
    ) -> Dict[str, str]:
        """
        Endpoint: DELETE /employees/{employee_id}/permanent
        Elimina permanentemente un empleado (solo OWNER).
        """
        employees_service = EmployeesService(db)
        return await employees_service.delete_employee_permanently(employee_id, current_user)
