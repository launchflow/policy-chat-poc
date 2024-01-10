import datetime
import uuid
from typing import List

from buildflow.dependencies import Scope, dependency
from buildflow.io.gcp import CloudSQLDatabase, CloudSQLUser

from components.audit_log.storage.dependencies import AuditLogStorageBuilder
from components.audit_log.storage.models import AuditLogEvent


def AuditLogComponentBuilder(
    cloud_sql_database: CloudSQLDatabase, cloud_sql_user: CloudSQLUser
):
    AuditLogStorage = AuditLogStorageBuilder(cloud_sql_database, cloud_sql_user)

    @dependency(scope=Scope.PROCESS)
    class AuditLogger:
        async def __init__(self, storage: AuditLogStorage):
            # Private attributes
            self._storage = storage

        async def create_event(
            self,
            *,
            resource_id: uuid.UUID,
            event_type: str,
            event_data: dict,
        ) -> AuditLogEvent:
            return await self._storage.create_event(
                resource_id=resource_id,
                event_type=event_type,
                event_data=event_data,
            )

        async def get_events(
            self,
            *,
            resource_id: uuid.UUID,
            event_type: str = None,
            start_time: datetime.datetime = None,
            end_time: datetime.datetime = None,
        ) -> List[AuditLogEvent]:
            return await self._storage.get_events(
                resource_id=resource_id,
                event_type=event_type,
                start_time=start_time,
                end_time=end_time,
            )

    @dependency(scope=Scope.NO_SCOPE)
    class AuditLogComponent:
        def __init__(self, logger: AuditLogger):
            self.logger = logger

    return AuditLogComponent
