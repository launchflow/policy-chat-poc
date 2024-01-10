import json
from datetime import datetime

from pydantic import BaseModel


class AuthenticatedUser(BaseModel):
    user_id: str
    email: str
    name: str


class Credentials(BaseModel):
    access_token: str
    access_expires_at: datetime
    refresh_token: str
    refresh_expires_at: datetime

    def to_json_str(self):
        return json.dumps(
            {"access_token": self.access_token, "refresh_token": self.refresh_token}
        )

    @classmethod
    def from_json_str(cls, json_str):
        json_obj = json.loads(json_str)
        return cls(
            access_token=json_obj["access_token"],
            refresh_token=json_obj["refresh_token"],
        )
