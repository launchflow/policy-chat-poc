"""This file contains all of the primitives needed by our backend."""


from buildflow.io.gcp import CloudSQLDatabase, CloudSQLInstance, CloudSQLUser, GCSBucket
from buildflow.types.gcp import CloudSQLDatabaseVersion, CloudSQLInstanceSettings

from policy_service.settings import env

# Deine our Cloud SQL instance in our GCP project.
cloud_sql_instance = CloudSQLInstance(
    instance_name="postgres-cloud-sql",
    project_id=env.gcp_project_id,
    database_version=CloudSQLDatabaseVersion.POSTGRES_15,
    region="us-central1",
    settings=CloudSQLInstanceSettings(
        tier="db-custom-1-3840",
    ),
)

# Define our Cloud SQL database contained in our Cloud SQL instance.
cloud_sql_database = CloudSQLDatabase(
    instance=cloud_sql_instance,
    database_name="postgres-db",
)

# Define our Cloud SQL user for our Cloud SQL instance.
cloud_sql_user = CloudSQLUser(
    instance=cloud_sql_instance,
    user_name=env.db_user,
    password=env.db_password,
)

# Define our GCS bucket for our blob storage.
gcs_bucket = GCSBucket(bucket_name="user-policy-storage", project_id=env.gcp_project_id)

# Define a separate Cloud SQL database for our auth extension.
cloud_sql_auth_database = CloudSQLDatabase(
    instance=cloud_sql_instance,
    database_name="auth-postgres-db",
)

# Define a separate Cloud SQL user for our auth extension.
cloud_sql_auth_user = CloudSQLUser(
    instance=cloud_sql_instance,
    user_name="auth-postgres-user",
    password="auth-postgres-password",
)
