from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.config.database import get_db
from app.controllers.attendance.attendance_controller import AttendanceController
from app.schemas.attendance.attendance_schema import AttendanceResponse
from app.dependencies.auth_dependencies import get_current_user
from app.models.users.user_model import User

router = APIRouter(
    prefix="/attendance",
    tags=["Attendance"],
)


@router.post("/check-in", response_model=AttendanceResponse, status_code=201)
async def check_in(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Registra la entrada (check-in) de un empleado.

    Requiere autenticación.

    Solo para empleados (admin, cajero, mesero, cocinero).
    El owner NO puede registrar asistencia.

    Reglas:
    - No puede registrar check-in dos veces en un día
    - Si ya existe un registro del día, responde error 400
    - La hora se registra en UTC

    Un empleado solo puede registrar su propia asistencia.
    """
    return await AttendanceController.check_in(current_user, db)


@router.post("/check-out", response_model=AttendanceResponse, status_code=200)
async def check_out(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Registra la salida (check-out) de un empleado.

    Requiere autenticación.

    Solo para empleados (admin, cajero, mesero, cocinero).
    El owner NO puede registrar asistencia.

    Reglas:
    - No puede registrar salida sin haber hecho entrada
    - No puede registrar salida dos veces
    - Debe ser el registro del día actual
    - check-out debe ser posterior al check-in
    - La hora se registra en UTC

    Un empleado solo puede registrar su propia asistencia.

    Si el empleado no registra salida, el sistema la cerrará automáticamente
    a las 23:59:59 del día.
    """
    return await AttendanceController.check_out(current_user, db)
