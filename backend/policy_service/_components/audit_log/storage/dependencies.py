import datetime
import uuid
from typing import List

from buildflow.dependencies import Scope, dependency
from buildflow.dependencies.sqlalchemy import AsyncSessionDepBuilder
from buildflow.io.gcp import CloudSQLDatabase, CloudSQLUser
from sqlalchemy.future import select

from components.audit_log.storage.models import AuditLogEvent


def AuditLogStorageBuilder(db_primitive: CloudSQLDatabase, db_user: CloudSQLUser):
    AsyncPostgres = AsyncSessionDepBuilder(
        db_primitive=db_primitive,
        db_user=db_user.user_name,
        db_password=db_user.password,
        pool_size=5,
        max_overflow=10,
        pool_recycle=600,
    )

    @dependency(scope=Scope.PROCESS)
    class AuditLogStorage:
        async def __init__(self, postgres: AsyncPostgres):
            self.db = postgres.session

        async def create_event(
            self,
            *,
            resource_id: uuid.UUID,
            event_type: str,
            event_data: dict,
        ) -> AuditLogEvent:
            event = AuditLogEvent(
                resource_id=resource_id,
                event_type=event_type,
                event_data=event_data,
            )
            self.db.add(event)
            await self.db.commit()
            return event

        async def get_events(
            self,
            *,
            resource_id: uuid.UUID,
            event_type: str = None,
            start_time: datetime.datetime = None,
            end_time: datetime.datetime = None,
        ) -> List[AuditLogEvent]:
            stmt = select(AuditLogEvent).where(AuditLogEvent.resource_id == resource_id)

            if event_type is not None:
                stmt = stmt.where(AuditLogEvent.event_type == event_type)

            if start_time is not None:
                stmt = stmt.where(AuditLogEvent.created_at >= start_time)

            if end_time is not None:
                stmt = stmt.where(AuditLogEvent.created_at <= end_time)

            result = await self.db.execute(stmt)
            events = result.scalars().all()
            return events

    return AuditLogStorage
