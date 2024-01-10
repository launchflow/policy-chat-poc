import random
import uuid
from datetime import datetime, timedelta
from typing import BinaryIO, List

from buildflow.dependencies import Scope, dependency
from buildflow.dependencies.bucket import GCSBucketClientBuilder
from buildflow.dependencies.sqlalchemy import AsyncSessionDepBuilder, engine
from sqlalchemy.future import select

from policy_service.core.primitives import (
    cloud_sql_database,
    cloud_sql_user,
    gcs_bucket,
)
from policy_service.core.storage.api import Account, Policy
from policy_service.core.storage.models import (
    Base,
    PolicyType,
    StorageAccount,
    StoragePolicy,
)
from policy_service.exceptions import AccountNotFound, PolicyNotFound

_AsyncPostgres = AsyncSessionDepBuilder(
    db_primitive=cloud_sql_database,
    db_user=cloud_sql_user.user_name,
    db_password=cloud_sql_user.password,
    pool_size=5,
    max_overflow=10,
    pool_recycle=600,
)

StorageBucket = GCSBucketClientBuilder(bucket_primitive=gcs_bucket)


def PolicyStorageBuilder():
    try:
        Base.metadata.create_all(
            bind=engine(
                cloud_sql_database, cloud_sql_user.user_name, cloud_sql_user.password
            )
        )
    except Exception as e:
        print("Failed to drop / create tables: ", e)
        pass

    @dependency(scope=Scope.PROCESS)
    class PolicyStorageCRUD:
        async def __init__(self, postgres: _AsyncPostgres):
            self.db = postgres.session

        async def create_storage_account(
            self,
            *,
            user_id: str,
            user_name: str,
            storage_bucket_dir: str,
        ) -> StorageAccount:
            storage_account = StorageAccount(
                user_id=uuid.UUID(user_id),
                user_name=user_name,
                storage_bucket_dir=storage_bucket_dir,
            )
            self.db.add(storage_account)
            await self.db.commit()
            return storage_account

        async def lookup_storage_account(self, *, user_id: str) -> StorageAccount:
            stmt = select(StorageAccount).where(
                StorageAccount.user_id == uuid.UUID(user_id)
            )
            result = await self.db.execute(stmt)
            storage_account = result.scalar_one_or_none()
            if storage_account is None:
                raise AccountNotFound()
            return storage_account

        async def get_storage_account(self, *, user_id: str) -> StorageAccount:
            stmt = select(StorageAccount).where(
                StorageAccount.user_id == uuid.UUID(user_id)
            )
            result = await self.db.execute(stmt)
            storage_account = result.scalar_one_or_none()
            if storage_account is None:
                raise AccountNotFound()
            return storage_account

        async def delete_storage_account(self, *, user_id: str) -> StorageAccount:
            stmt = select(StorageAccount).where(
                StorageAccount.user_id == uuid.UUID(user_id)
            )
            result = await self.db.execute(stmt)
            storage_account = result.scalar_one_or_none()
            if storage_account is None:
                raise AccountNotFound()
            self.db.delete(storage_account)
            await self.db.commit()
            return True

        async def create_storage_policy(
            self,
            *,
            account_id: int,
            policy_id: str,
            policy_type: PolicyType,
            policy_holder: str,
            effective_date: datetime,
            expiration_date: datetime,
            is_active: bool,
        ) -> StoragePolicy:
            storage_policy = StoragePolicy(
                account_id=account_id,
                policy_id=policy_id,
                policy_type=policy_type,
                policy_holder=policy_holder,
                effective_date=effective_date,
                expiration_date=expiration_date,
                is_active=is_active,
            )
            self.db.add(storage_policy)
            await self.db.commit()
            return StoragePolicy

        async def lookup_storage_policies(
            self, *, account_id: int
        ) -> List[StoragePolicy]:
            stmt = select(StoragePolicy).where(StoragePolicy.account_id == account_id)
            result = await self.db.execute(stmt)
            storage_policies = result.scalars().all()
            return storage_policies

        async def get_storage_policy(self, *, policy_id: int) -> StoragePolicy:
            stmt = select(StoragePolicy).where(StoragePolicy.policy_id == policy_id)
            result = await self.db.execute(stmt)
            storage_policy = result.scalar_one_or_none()
            if storage_policy is None:
                raise PolicyNotFound()
            return storage_policy

        async def delete_storage_policy(self, *, policy_id: int) -> StoragePolicy:
            stmt = select(StoragePolicy).where(StoragePolicy.policy_id == policy_id)
            result = await self.db.execute(stmt)
            storage_policy = result.scalar_one_or_none()
            if storage_policy is None:
                raise PolicyNotFound()
            self.db.delete(storage_policy)
            await self.db.commit()
            return True

        async def close_connection(self):
            await self.db.close()

    @dependency(scope=Scope.PROCESS)
    class PolicyStorage:
        async def __init__(
            self, storage_crud: PolicyStorageCRUD, storage_bucket: StorageBucket
        ):
            self.crud = storage_crud
            self.bucket = storage_bucket.bucket

        async def create_account(self, *, user_id: str, user_name: str) -> Account:
            storage_bucket_dir = f"users/{user_id}/policies"
            try:
                storage_account = await self.crud.create_storage_account(
                    user_id=user_id,
                    user_name=user_name,
                    storage_bucket_dir=storage_bucket_dir,
                )
            except Exception as e:
                await self.crud.close_connection()
                raise e
            await self.crud.close_connection()
            self.bucket.blob(f"{storage_bucket_dir}/").upload_from_string("")
            return Account.from_storage_account(storage_account)

        async def maybe_create_account(
            self, *, user_id: str, user_name: str
        ) -> Account:
            try:
                storage_account = await self.crud.lookup_storage_account(
                    user_id=user_id
                )
            except AccountNotFound:
                return await self.create_account(
                    user_id=user_id,
                    user_name=user_name,
                )
            await self.crud.close_connection()
            return Account.from_storage_account(storage_account)

        async def lookup_account_for_user(self, *, user_id: str) -> Account:
            try:
                storage_account = await self.crud.lookup_storage_account(
                    user_id=user_id
                )
            except Exception as e:
                await self.crud.close_connection()
                raise e
            await self.crud.close_connection()
            return Account.from_storage_account(storage_account)

        async def upload_policy_for_user(
            self,
            *,
            user_id: str,
            policy_upload: BinaryIO,
        ) -> bool:
            try:
                storage_account = await self.crud.lookup_storage_account(
                    user_id=user_id
                )
            except Exception as e:
                await self.crud.close_connection()
                raise e

            # TODO: Parse the policy file
            expiration_date = datetime.now() + timedelta(days=random.randint(-50, 50))
            policy = Policy(
                account_id=str(storage_account.id),
                policy_id=str(uuid.uuid4()),
                policy_type=random.choice(list(PolicyType)),
                policy_holder="policy-holder",
                effective_date=datetime.now() - timedelta(days=365),
                expiration_date=expiration_date,
                is_active=expiration_date > datetime.now(),
            )

            # Upload the file to Google Cloud Storage bucket
            policy_blob = self.bucket.blob(
                f"{storage_account.storage_bucket_dir}/{policy.policy_id}.png"
            )
            policy_blob.upload_from_file(policy_upload)

            # Store the Policy metadata in the database
            try:
                storage_policy = await self.crud.create_storage_policy(
                    account_id=policy.account_id,
                    policy_id=policy.policy_id,
                    policy_type=policy.policy_type,
                    policy_holder=policy.policy_holder,
                    effective_date=policy.effective_date,
                    expiration_date=policy.expiration_date,
                    is_active=policy.is_active,
                )
            except Exception as e:
                await self.crud.close_connection()
                raise e
            await self.crud.close_connection()
            return True

        async def lookup_policies_for_user(self, *, user_id: str) -> List[Policy]:
            try:
                storage_account = await self.crud.lookup_storage_account(
                    user_id=user_id
                )
                storage_policies = await self.crud.lookup_storage_policies(
                    account_id=storage_account.id
                )
            except Exception as e:
                await self.crud.close_connection()
                raise e
            await self.crud.close_connection()
            policies = [Policy.from_storage_policy(sp) for sp in storage_policies]
            # attach image urls
            for policy in policies:
                blob = self.bucket.blob(
                    f"{storage_account.storage_bucket_dir}/{policy.policy_id}.png"
                )
                blob.make_public()
                policy.image_url = blob.public_url
            return policies

    return PolicyStorage


PolicyStorage = PolicyStorageBuilder()
