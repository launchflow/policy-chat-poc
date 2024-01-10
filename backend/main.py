"""Main file the setups the flow and is our entry point."""

from buildflow import Flow

from policy_service.core.auth.dependencies import auth_service
from policy_service.core.primitives import (
    cloud_sql_auth_database,
    cloud_sql_auth_user,
    cloud_sql_database,
    cloud_sql_instance,
    cloud_sql_user,
    gcs_bucket,
)
from policy_service.service import policy_service

app = Flow()

# Setup infrastructure to be managed self-managed.
app.manage(
    cloud_sql_instance,
    cloud_sql_database,
    cloud_sql_user,
    cloud_sql_auth_database,
    cloud_sql_auth_user,
    gcs_bucket,
)

# Attach services to expose the endpoints.
app.add_service(auth_service)
app.add_service(policy_service)
