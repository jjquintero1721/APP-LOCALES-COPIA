from sqlalchemy.ext.asyncio import AsyncSession
from app.services.attendance.attendance_service import AttendanceService
from app.schemas.attendance.attendance_schema import AttendanceResponse
from app.models.users.user_model import User


class AttendanceController:
    """
    Controller de asistencia.
    Maneja los requests HTTP y delega la lógica al servicio.
    """

    @staticmethod
    async def check_in(
        current_user: User,
        db: AsyncSession,
    ) -> AttendanceResponse:
        """
        Endpoint: POST /attendance/check-in
        Registra la entrada de un empleado.
        """
        attendance_service = AttendanceService(db)
        return await attendance_service.check_in(current_user)

    @staticmethod
    async def check_out(
        current_user: User,
        db: AsyncSession,
    ) -> AttendanceResponse:
        """
        Endpoint: POST /attendance/check-out
        Registra la salida de un empleado.
        """
        attendance_service = AttendanceService(db)
        return await attendance_service.check_out(current_user)
