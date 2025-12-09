from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional


class AttendanceCheckInRequest(BaseModel):
    """
    Schema para registrar entrada (check-in).
    No requiere datos adicionales ya que se usa el usuario autenticado.
    """
    pass


class AttendanceCheckOutRequest(BaseModel):
    """
    Schema para registrar salida (check-out).
    No requiere datos adicionales ya que se usa el usuario autenticado.
    """
    pass


class AttendanceResponse(BaseModel):
    """
    Schema para respuesta de asistencia.
    """
    id: int
    employee_id: int
    business_id: int
    date: date
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TodayAttendanceResponse(BaseModel):
    """
    Schema para la asistencia del día actual (usado en el endpoint de empleados).
    """
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None

    class Config:
        from_attributes = True
