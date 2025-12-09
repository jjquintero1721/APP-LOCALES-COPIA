from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.models.audit.audit_log_model import AuditLog


class AuditRepository:
    """
    Repositorio para operaciones de AuditLog.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_log(
        self,
        business_id: int,
        action: str,
        user_id: Optional[int] = None,
    ) -> AuditLog:
        """
        Crea un registro de auditoría.
        """
        audit_log = AuditLog(
            business_id=business_id,
            user_id=user_id,
            action=action,
        )
        self.db.add(audit_log)
        await self.db.commit()
        await self.db.refresh(audit_log)
        return audit_log
