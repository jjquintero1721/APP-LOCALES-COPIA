from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.config.database import Base


class Attendance(Base):
    """
    Modelo Attendance (Asistencia).
    Registra la entrada y salida de empleados por día.

    Reglas:
    - Un empleado solo puede tener un registro por día
    - check_out solo puede registrarse si ya hay check_in
    - Solo para empleados (admin, cajero, mesero, cocinero), NO para owner
    """

    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    business_id = Column(Integer, ForeignKey("business.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)  # Solo la fecha, sin hora
    check_in = Column(DateTime(timezone=True), nullable=True)  # Hora de entrada
    check_out = Column(DateTime(timezone=True), nullable=True)  # Hora de salida
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Constraints
    # Un empleado solo puede tener un registro por día
    __table_args__ = (
        UniqueConstraint('employee_id', 'date', name='uq_employee_date'),
    )

    # Relationships
    employee = relationship("User", back_populates="attendance_records")
    business = relationship("Business", back_populates="attendance_records")

    def __repr__(self):
        return f"<Attendance(id={self.id}, employee_id={self.employee_id}, date={self.date})>"
