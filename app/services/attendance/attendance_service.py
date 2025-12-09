from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from datetime import datetime, date, time
from typing import List
from app.repositories.attendance.attendance_repository import AttendanceRepository
from app.repositories.audit.audit_repository import AuditRepository
from app.schemas.attendance.attendance_schema import AttendanceResponse
from app.models.users.user_model import User, UserRole


class AttendanceService:
    """
    Servicio de asistencia.
    Maneja operaciones de check-in y check-out con validaciones de negocio y auditoría.

    Reglas:
    - Solo empleados (admin, cajero, mesero, cocinero) pueden registrar asistencia, NO owner
    - Un empleado solo puede registrar su propia asistencia
    - check-in y check-out solo una vez por día
    - check-out debe ser posterior al check-in
    - La comparación se basa en la zona horaria del servidor (UTC)
    """

    # Roles que pueden registrar asistencia
    ALLOWED_ROLES = {
        UserRole.ADMIN,
        UserRole.CASHIER,
        UserRole.WAITER,
        UserRole.COOK,
    }

    def __init__(self, db: AsyncSession):
        self.db = db
        self.attendance_repo = AttendanceRepository(db)
        self.audit_repo = AuditRepository(db)

    def _validate_employee_role(self, user: User) -> None:
        """
        Valida que el usuario tenga un rol permitido para registrar asistencia.

        Args:
            user: Usuario a validar

        Raises:
            HTTPException: Si el rol no está permitido
        """
        if user.role not in self.ALLOWED_ROLES:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"El rol {user.role.value} no puede registrar asistencia. Solo los empleados (admin, cajero, mesero, cocinero) pueden registrar entrada/salida.",
            )

    async def check_in(self, current_user: User) -> AttendanceResponse:
        """
        Registra la entrada (check-in) de un empleado.

        Validaciones:
        - Solo empleados permitidos pueden registrar entrada
        - No puede registrar check-in dos veces en un día
        - Si ya existe un registro del día, responde error

        Args:
            current_user: Usuario que registra la entrada

        Returns:
            AttendanceResponse con el registro creado
        """
        # Validar rol
        self._validate_employee_role(current_user)

        # Obtener fecha y hora actual (UTC)
        now = datetime.utcnow()
        today = now.date()

        # Verificar si ya existe un registro de asistencia hoy
        existing_attendance = await self.attendance_repo.get_today_attendance(
            employee_id=current_user.id,
            business_id=current_user.business_id,
            today_date=today,
        )

        if existing_attendance:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya has registrado tu entrada hoy a las {existing_attendance.check_in.strftime('%H:%M:%S')}. No puedes registrar entrada dos veces en un día.",
            )

        # Crear registro de check-in
        attendance = await self.attendance_repo.create_check_in(
            employee_id=current_user.id,
            business_id=current_user.business_id,
            check_in_time=now,
            today_date=today,
        )

        # Registrar auditoría
        await self.audit_repo.create_log(
            business_id=current_user.business_id,
            user_id=current_user.id,
            action=f"Empleado {current_user.full_name} ({current_user.email}) registró entrada a las {now.strftime('%Y-%m-%d %H:%M:%S')} UTC",
        )

        return AttendanceResponse.model_validate(attendance)

    async def check_out(self, current_user: User) -> AttendanceResponse:
        """
        Registra la salida (check-out) de un empleado.

        Validaciones:
        - Solo empleados permitidos pueden registrar salida
        - No puede registrar salida sin haber hecho entrada
        - No puede registrar salida dos veces
        - Debe ser el registro del día actual
        - check-out debe ser posterior al check-in

        Args:
            current_user: Usuario que registra la salida

        Returns:
            AttendanceResponse con el registro actualizado
        """
        # Validar rol
        self._validate_employee_role(current_user)

        # Obtener fecha y hora actual (UTC)
        now = datetime.utcnow()
        today = now.date()

        # Verificar si existe un registro de asistencia hoy
        attendance = await self.attendance_repo.get_today_attendance(
            employee_id=current_user.id,
            business_id=current_user.business_id,
            today_date=today,
        )

        if not attendance:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No has registrado entrada hoy. Debes registrar entrada antes de registrar salida.",
            )

        if not attendance.check_in:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No tienes una entrada registrada hoy. Debes registrar entrada antes de registrar salida.",
            )

        if attendance.check_out:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya has registrado tu salida hoy a las {attendance.check_out.strftime('%H:%M:%S')}. No puedes registrar salida dos veces en un día.",
            )

        # Validar que check-out sea posterior a check-in
        if now <= attendance.check_in:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La hora de salida debe ser posterior a la hora de entrada.",
            )

        # Actualizar check-out
        attendance = await self.attendance_repo.update_check_out(attendance, now)

        # Calcular duración
        duration = now - attendance.check_in
        hours = duration.total_seconds() / 3600

        # Registrar auditoría
        await self.audit_repo.create_log(
            business_id=current_user.business_id,
            user_id=current_user.id,
            action=f"Empleado {current_user.full_name} ({current_user.email}) registró salida a las {now.strftime('%Y-%m-%d %H:%M:%S')} UTC. Duración: {hours:.2f} horas",
        )

        return AttendanceResponse.model_validate(attendance)

    async def auto_close_attendances(self, business_id: int, target_date: date) -> List[AttendanceResponse]:
        """
        Cierra automáticamente todas las asistencias sin check-out al final del día.
        Esta función debe ser llamada por un job automático a medianoche.

        Args:
            business_id: ID del negocio
            target_date: Fecha de las asistencias a cerrar

        Returns:
            Lista de asistencias cerradas
        """
        # Obtener asistencias abiertas
        open_attendances = await self.attendance_repo.get_open_attendances(
            business_id=business_id,
            target_date=target_date,
        )

        closed_attendances = []

        # Cerrar cada asistencia a las 23:59:59 del día
        end_of_day = datetime.combine(target_date, time(23, 59, 59))

        for attendance in open_attendances:
            # Cerrar asistencia
            closed_attendance = await self.attendance_repo.close_attendance(
                attendance=attendance,
                check_out_time=end_of_day,
            )

            # Registrar auditoría
            await self.audit_repo.create_log(
                business_id=business_id,
                user_id=attendance.employee_id,
                action=f"Sistema cerró automáticamente la asistencia del empleado ID {attendance.employee_id} el {target_date.strftime('%Y-%m-%d')} a las 23:59:59 UTC (el empleado no registró salida)",
            )

            closed_attendances.append(AttendanceResponse.model_validate(closed_attendance))

        return closed_attendances
