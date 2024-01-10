from buildflow import Service
from buildflow.middleware import CORSMiddleware
from buildflow.requests import UploadFile
from pydantic import BaseModel

from policy_service.core.auth.dependencies import AuthenticatedRequest
from policy_service.core.chat.dependencies import PolicyChatModel
from policy_service.core.storage.dependencies import PolicyStorage
from policy_service.exceptions import AccountNotFound

policy_service = Service(service_id="policy-service")

policy_service.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@policy_service.endpoint("/upload", method="POST")
async def upload_policy(
    request: AuthenticatedRequest,
    policy_file: UploadFile,
    storage: PolicyStorage,
):
    await storage.maybe_create_account(
        user_id=request.user.user_id, user_name=request.user.name
    )
    await storage.upload_policy_for_user(
        user_id=request.user.user_id,
        policy_upload=policy_file.file,
    )
    return {"success": True}


@policy_service.endpoint("/list", method="GET")
async def list_policies(
    request: AuthenticatedRequest,
    storage: PolicyStorage,
):
    try:
        return await storage.lookup_policies_for_user(user_id=request.user.user_id)
    except AccountNotFound:
        return []


class ChatRequest(BaseModel):
    user_inquiry: str


@policy_service.endpoint("/chat", method="POST")
async def chat_with_policies(
    chat_request: ChatRequest,
    request: AuthenticatedRequest,
    storage: PolicyStorage,
    model: PolicyChatModel,
):
    policies = await storage.lookup_policies_for_user(user_id=request.user.user_id)
    return model.handle_user_inquiry(
        inquiry=chat_request.user_inquiry,
        policies=policies,
    )
