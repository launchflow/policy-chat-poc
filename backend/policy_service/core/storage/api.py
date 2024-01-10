from datetime import datetime

from pydantic import BaseModel

from policy_service.core.storage.models import PolicyType, StorageAccount, StoragePolicy


class Policy(BaseModel):
    # Identifiers
    account_id: str
    policy_id: str
    # Metadata
    policy_type: PolicyType
    policy_holder: str
    effective_date: datetime
    expiration_date: datetime
    is_active: bool
    image_url: str = None

    @classmethod
    def from_storage_policy(cls, storage_policy: StoragePolicy) -> "Policy":
        return cls(
            account_id=str(storage_policy.account_id),
            policy_id=storage_policy.policy_id,
            policy_type=PolicyType(storage_policy.policy_type),
            policy_holder=storage_policy.policy_holder,
            effective_date=storage_policy.effective_date,
            expiration_date=storage_policy.expiration_date,
            is_active=storage_policy.is_active,
        )


class Account(BaseModel):
    account_id: str
    display_name: str

    @classmethod
    def from_storage_account(cls, storage_account: StorageAccount) -> "Account":
        return cls(
            account_id=str(storage_account.id),
            display_name=storage_account.user_name,
        )
