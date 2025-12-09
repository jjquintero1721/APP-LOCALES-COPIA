"""
Script para cerrar automáticamente las asistencias abiertas al final del día.

Este script debe ejecutarse diariamente a medianoche (00:00) usando un cron job
o un programador de tareas como APScheduler.

Ejemplo de cron job (ejecutar a las 00:00 todos los días):
0 0 * * * cd /path/to/project && python -m app.jobs.auto_close_attendance

O usando APScheduler en el main.py:
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.jobs.auto_close_attendance import auto_close_all_attendances

scheduler = AsyncIOScheduler()
scheduler.add_job(auto_close_all_attendances, 'cron', hour=0, minute=0)
scheduler.start()
"""
import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy import select
from app.config.database import AsyncSessionLocal
from app.models.business.business_model import Business
from app.services.attendance.attendance_service import AttendanceService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def auto_close_all_attendances():
    """
    Cierra automáticamente todas las asistencias abiertas del día anterior
    para todos los negocios.

    Esta función debe ejecutarse a medianoche (00:00) para cerrar las asistencias
    del día que acaba de terminar.
    """
    logger.info("Iniciando cierre automático de asistencias...")

    # Obtener la fecha de ayer (el día que acaba de terminar)
    yesterday = (datetime.utcnow() - timedelta(days=1)).date()

    try:
        async with AsyncSessionLocal() as db:
            # Obtener todos los negocios
            result = await db.execute(select(Business))
            businesses = result.scalars().all()

            total_closed = 0

            # Cerrar asistencias para cada negocio
            for business in businesses:
                attendance_service = AttendanceService(db)

                try:
                    closed_attendances = await attendance_service.auto_close_attendances(
                        business_id=business.id,
                        target_date=yesterday,
                    )

                    if closed_attendances:
                        logger.info(
                            f"Negocio '{business.name}' (ID: {business.id}): "
                            f"Se cerraron {len(closed_attendances)} asistencia(s) del {yesterday}"
                        )
                        total_closed += len(closed_attendances)
                    else:
                        logger.info(
                            f"Negocio '{business.name}' (ID: {business.id}): "
                            f"No hay asistencias abiertas para cerrar del {yesterday}"
                        )

                except Exception as e:
                    logger.error(
                        f"Error al cerrar asistencias del negocio '{business.name}' (ID: {business.id}): {e}"
                    )
                    continue

            logger.info(
                f"Cierre automático completado. Total de asistencias cerradas: {total_closed}"
            )

    except Exception as e:
        logger.error(f"Error crítico al cerrar asistencias automáticamente: {e}")
        raise


async def main():
    """
    Función principal para ejecutar el script directamente.
    """
    await auto_close_all_attendances()


if __name__ == "__main__":
    asyncio.run(main())
