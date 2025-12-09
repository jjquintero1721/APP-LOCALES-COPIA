from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from typing import Optional, List
from datetime import datetime, date
from app.models.attendance.attendance_model import Attendance


class AttendanceRepository:
    """
    Repositorio para operaciones de Attendance en la base de datos.
    TODOS los queries filtran por business_id (multi-tenant).
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_today_attendance(
        self, employee_id: int, business_id: int, today_date: date
    ) -> Optional[Attendance]:
        """
        Obtiene el registro de asistencia del día actual de un empleado.

        Args:
            employee_id: ID del empleado
            business_id: ID del negocio
            today_date: Fecha de hoy

        Returns:
            Attendance si existe, None en caso contrario
        """
        result = await self.db.execute(
            select(Attendance).where(
                and_(
                    Attendance.employee_id == employee_id,
                    Attendance.business_id == business_id,
                    Attendance.date == today_date,
                )
            )
        )
        return result.scalar_one_or_none()

    async def create_check_in(
        self, employee_id: int, business_id: int, check_in_time: datetime, today_date: date
    ) -> Attendance:
        """
        Crea un nuevo registro de asistencia con check-in.

        Args:
            employee_id: ID del empleado
            business_id: ID del negocio
            check_in_time: Hora de entrada
            today_date: Fecha de hoy

        Returns:
            Attendance creado
        """
        attendance = Attendance(
            employee_id=employee_id,
            business_id=business_id,
            date=today_date,
            check_in=check_in_time,
        )
        self.db.add(attendance)
        await self.db.commit()
        await self.db.refresh(attendance)
        return attendance

    async def update_check_out(
        self, attendance: Attendance, check_out_time: datetime
    ) -> Attendance:
        """
        Actualiza el check-out de un registro de asistencia.

        Args:
            attendance: Registro de asistencia a actualizar
            check_out_time: Hora de salida

        Returns:
            Attendance actualizado
        """
        attendance.check_out = check_out_time
        await self.db.commit()
        await self.db.refresh(attendance)
        return attendance

    async def get_open_attendances(self, business_id: int, target_date: date) -> List[Attendance]:
        """
        Obtiene todos los registros de asistencia sin check-out para una fecha específica.
        Útil para cerrar asistencias automáticamente a medianoche.

        Args:
            business_id: ID del negocio
            target_date: Fecha objetivo

        Returns:
            Lista de registros de asistencia sin check-out
        """
        result = await self.db.execute(
            select(Attendance).where(
                and_(
                    Attendance.business_id == business_id,
                    Attendance.date == target_date,
                    Attendance.check_in.isnot(None),
                    Attendance.check_out.is_(None),
                )
            )
        )
        return list(result.scalars().all())

    async def close_attendance(self, attendance: Attendance, check_out_time: datetime) -> Attendance:
        """
        Cierra un registro de asistencia (usado para cierre automático).

        Args:
            attendance: Registro de asistencia a cerrar
            check_out_time: Hora de cierre

        Returns:
            Attendance cerrado
        """
        attendance.check_out = check_out_time
        await self.db.commit()
        await self.db.refresh(attendance)
        return attendance
