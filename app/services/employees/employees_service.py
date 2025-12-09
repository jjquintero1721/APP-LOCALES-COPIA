from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.repositories.users.users_repository import UsersRepository
from app.repositories.audit.audit_repository import AuditRepository
from app.repositories.attendance.attendance_repository import AttendanceRepository
from app.schemas.employees.employee_schema import (
    EmployeeCreateRequest,
    EmployeeUpdateRequest,
    EmployeeResponse,
)
from app.schemas.attendance.attendance_schema import TodayAttendanceResponse
from app.models.users.user_model import User, UserRole
from app.utils.security import get_password_hash, generate_random_password


class EmployeesService:
    """
    Servicio de empleados.
    Maneja operaciones CRUD de empleados con validaciones jerárquicas y auditoría.
    """

    # Jerarquía de roles (de mayor a menor)
    ROLE_HIERARCHY = {
        UserRole.OWNER: 5,
        UserRole.ADMIN: 4,
        UserRole.CASHIER: 3,
        UserRole.WAITER: 2,
        UserRole.COOK: 1,
    }

    def __init__(self, db: AsyncSession):
        self.db = db
        self.users_repo = UsersRepository(db)
        self.audit_repo = AuditRepository(db)
        self.attendance_repo = AttendanceRepository(db)

    def _can_manage_role(self, manager_role: UserRole, target_role: UserRole) -> bool:
        """
        Verifica si un rol puede gestionar otro rol.

        Args:
            manager_role: Rol del usuario que gestiona
            target_role: Rol del empleado a gestionar

        Returns:
            True si puede gestionar, False en caso contrario
        """
        manager_level = self.ROLE_HIERARCHY.get(manager_role, 0)
        target_level = self.ROLE_HIERARCHY.get(target_role, 0)
        return manager_level > target_level

    async def _get_today_attendance(self, employee_id: int, business_id: int) -> Optional[TodayAttendanceResponse]:
        """
        Obtiene la asistencia del día actual de un empleado.

        Args:
            employee_id: ID del empleado
            business_id: ID del negocio

        Returns:
            TodayAttendanceResponse con check_in y check_out, o None si no hay registro
        """
        today = datetime.utcnow().date()
        attendance = await self.attendance_repo.get_today_attendance(
            employee_id=employee_id,
            business_id=business_id,
            today_date=today,
        )

        if not attendance:
            return None

        return TodayAttendanceResponse(
            check_in=attendance.check_in,
            check_out=attendance.check_out,
        )

    async def create_employee(
        self,
        data: EmployeeCreateRequest,
        current_user: User,
    ) -> EmployeeResponse:
        """
        Crea un nuevo empleado con validaciones de jerarquía.

        Validaciones:
        - No se puede usar un email ya existente en el negocio
        - No se puede crear un empleado con rol mayor o igual al del creador
        - OWNER puede crear cualquier rol excepto OWNER
        - ADMIN puede crear CASHIER, WAITER, COOK

        Args:
            data: Datos del empleado a crear
            current_user: Usuario que crea el empleado

        Returns:
            EmployeeResponse con los datos del empleado creado
        """
        # Validar que el rol del empleado sea menor que el del creador
        if not self._can_manage_role(current_user.role, data.role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"No puedes crear empleados con rol {data.role.value}. Tu rol ({current_user.role.value}) no tiene suficientes permisos.",
            )

        # Validar que el email no exista en el negocio
        if await self.users_repo.email_exists(data.email, current_user.business_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El email {data.email} ya está registrado en este negocio.",
            )

        # Generar o usar contraseña proporcionada
        if data.password:
            plain_password = data.password
        else:
            plain_password = generate_random_password()

        hashed_password = get_password_hash(plain_password)

        # Crear el empleado
        employee = await self.users_repo.create(
            business_id=current_user.business_id,
            email=data.email,
            full_name=data.full_name,
            phone=data.phone,
            document=data.document,
            hashed_password=hashed_password,
            role=data.role,
        )

        # Registrar auditoría
        await self.audit_repo.create_log(
            business_id=current_user.business_id,
            user_id=current_user.id,
            action=f"Empleado creado: {employee.full_name} ({employee.email}) con rol {employee.role.value} por {current_user.full_name}",
        )

        # Crear respuesta con contraseña temporal solo si se generó automáticamente
        response = EmployeeResponse.model_validate(employee)
        if not data.password:
            response.temporary_password = plain_password

        return response

    async def get_employee_by_id(
        self,
        employee_id: int,
        current_user: User,
    ) -> EmployeeResponse:
        """
        Obtiene un empleado por ID.

        Args:
            employee_id: ID del empleado
            current_user: Usuario actual

        Returns:
            EmployeeResponse con los datos del empleado
        """
        employee = await self.users_repo.get_by_id(employee_id, current_user.business_id)

        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Empleado no encontrado.",
            )

        # Obtener asistencia del día
        today_attendance = await self._get_today_attendance(employee.id, current_user.business_id)

        # Crear respuesta
        response = EmployeeResponse.model_validate(employee)
        response.today_attendance = today_attendance

        return response

    async def get_all_employees(
        self,
        current_user: User,
        skip: int = 0,
        limit: int = 100,
    ) -> List[EmployeeResponse]:
        """
        Obtiene todos los empleados del negocio.

        Args:
            current_user: Usuario actual
            skip: Número de registros a omitir
            limit: Número máximo de registros

        Returns:
            Lista de EmployeeResponse con asistencia del día actual
        """
        employees = await self.users_repo.get_all_by_business(
            current_user.business_id, skip, limit
        )

        # Agregar asistencia del día a cada empleado
        result = []
        for emp in employees:
            today_attendance = await self._get_today_attendance(emp.id, current_user.business_id)
            response = EmployeeResponse.model_validate(emp)
            response.today_attendance = today_attendance
            result.append(response)

        return result

    async def update_employee(
        self,
        employee_id: int,
        data: EmployeeUpdateRequest,
        current_user: User,
    ) -> EmployeeResponse:
        """
        Actualiza un empleado existente.

        Validaciones:
        - No se puede cambiar el business_id
        - No se puede actualizar un empleado de mayor jerarquía
        - No se puede cambiar el propio rol
        - No se puede cambiar el email a uno ya existente
        - Los empleados no pueden cambiarse su propio rol

        Args:
            employee_id: ID del empleado a actualizar
            data: Datos a actualizar
            current_user: Usuario que realiza la actualización

        Returns:
            EmployeeResponse con los datos actualizados
        """
        # Obtener el empleado
        employee = await self.users_repo.get_by_id(employee_id, current_user.business_id)

        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Empleado no encontrado.",
            )

        # Validar que el usuario actual pueda gestionar este empleado
        if not self._can_manage_role(current_user.role, employee.role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"No tienes permisos para editar este empleado (rol: {employee.role.value}).",
            )

        # Rastrear cambios para auditoría
        changes: List[str] = []

        # Validar y aplicar cambio de rol
        if data.role is not None:
            # Validar que un empleado no pueda cambiar su propio rol
            if current_user.id == employee.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No puedes cambiar tu propio rol.",
                )

            # Validar que el nuevo rol pueda ser gestionado
            if not self._can_manage_role(current_user.role, data.role):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"No puedes asignar el rol {data.role.value}.",
                )

            if employee.role != data.role:
                changes.append(f"Rol cambiado de {employee.role.value} a {data.role.value}")
                employee.role = data.role

        # Validar y aplicar cambio de email
        if data.email is not None and data.email != employee.email:
            if await self.users_repo.email_exists(
                data.email, current_user.business_id, exclude_user_id=employee.id
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"El email {data.email} ya está registrado en este negocio.",
                )
            changes.append(f"Email cambiado de {employee.email} a {data.email}")
            employee.email = data.email

        # Aplicar cambio de nombre
        if data.full_name is not None and data.full_name != employee.full_name:
            changes.append(f"Nombre cambiado de '{employee.full_name}' a '{data.full_name}'")
            employee.full_name = data.full_name

        # Aplicar cambio de teléfono
        if data.phone is not None and data.phone != employee.phone:
            changes.append(f"Teléfono cambiado de '{employee.phone or 'N/A'}' a '{data.phone}'")
            employee.phone = data.phone

        # Aplicar cambio de estado
        if data.is_active is not None and data.is_active != employee.is_active:
            new_status = "activo" if data.is_active else "inactivo"
            old_status = "activo" if employee.is_active else "inactivo"
            changes.append(f"Estado cambiado de {old_status} a {new_status}")
            employee.is_active = data.is_active

        # Guardar cambios
        if changes:
            employee = await self.users_repo.update(employee)

            # Registrar auditoría
            await self.audit_repo.create_log(
                business_id=current_user.business_id,
                user_id=current_user.id,
                action=f"Empleado actualizado: {employee.full_name} ({employee.email}). Cambios: {', '.join(changes)}. Actualizado por {current_user.full_name}",
            )

        return EmployeeResponse.model_validate(employee)

    async def deactivate_employee(
        self,
        employee_id: int,
        current_user: User,
    ) -> EmployeeResponse:
        """
        Inactiva un empleado (primera fase de eliminación).

        Validaciones:
        - El owner no puede eliminarse a sí mismo
        - El admin no puede eliminar al owner
        - No se puede eliminar un empleado de mayor jerarquía

        Args:
            employee_id: ID del empleado a inactivar
            current_user: Usuario que realiza la inactivación

        Returns:
            EmployeeResponse con el empleado inactivado
        """
        # Obtener el empleado
        employee = await self.users_repo.get_by_id(employee_id, current_user.business_id)

        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Empleado no encontrado.",
            )

        # Validar que el owner no se elimine a sí mismo
        if employee.id == current_user.id and current_user.role == UserRole.OWNER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="El owner no puede eliminarse a sí mismo.",
            )

        # Validar que el admin no pueda eliminar al owner
        if employee.role == UserRole.OWNER and current_user.role != UserRole.OWNER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No puedes eliminar al owner.",
            )

        # Validar jerarquía
        if not self._can_manage_role(current_user.role, employee.role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"No tienes permisos para eliminar este empleado (rol: {employee.role.value}).",
            )

        # Inactivar el empleado
        employee.is_active = False
        employee = await self.users_repo.update(employee)

        # Registrar auditoría
        await self.audit_repo.create_log(
            business_id=current_user.business_id,
            user_id=current_user.id,
            action=f"Empleado inactivado: {employee.full_name} ({employee.email}, rol: {employee.role.value}) por {current_user.full_name}",
        )

        return EmployeeResponse.model_validate(employee)

    async def delete_employee_permanently(
        self,
        employee_id: int,
        current_user: User,
    ) -> Dict[str, str]:
        """
        Elimina permanentemente un empleado (solo OWNER).

        Validaciones:
        - Solo el OWNER puede eliminar permanentemente
        - El owner no puede eliminarse a sí mismo
        - El empleado debe estar inactivo primero

        Args:
            employee_id: ID del empleado a eliminar
            current_user: Usuario que realiza la eliminación (debe ser OWNER)

        Returns:
            Mensaje de confirmación
        """
        # Validar que solo el OWNER pueda eliminar permanentemente
        if current_user.role != UserRole.OWNER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo el owner puede eliminar permanentemente empleados.",
            )

        # Obtener el empleado
        employee = await self.users_repo.get_by_id(employee_id, current_user.business_id)

        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Empleado no encontrado.",
            )

        # Validar que el owner no se elimine a sí mismo
        if employee.id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="El owner no puede eliminarse a sí mismo.",
            )

        # Validar que el empleado esté inactivo
        if employee.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El empleado debe estar inactivo antes de eliminarlo permanentemente. Primero inactívalo.",
            )

        # Guardar datos para auditoría antes de eliminar
        employee_name = employee.full_name
        employee_email = employee.email
        employee_role = employee.role.value

        # Eliminar permanentemente
        await self.users_repo.delete_permanently(employee)

        # Registrar auditoría
        await self.audit_repo.create_log(
            business_id=current_user.business_id,
            user_id=current_user.id,
            action=f"Empleado eliminado permanentemente: {employee_name} ({employee_email}, rol: {employee_role}) por {current_user.full_name}",
        )

        return {
            "message": f"Empleado {employee_name} eliminado permanentemente.",
        }
