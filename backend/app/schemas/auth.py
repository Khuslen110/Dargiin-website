from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.core.validation import normalize_username
from app.models.enums import GroupType
from app.schemas.common import LeaderRef


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("username")
    @classmethod
    def normalize(cls, value: str) -> str:
        return normalize_username(value)


class PermissionSet(BaseModel):
    can_edit: bool
    can_import: bool
    can_export: bool
    can_view_sensitive: bool
    can_delete: bool
    can_manage_users: bool
    can_add_child: bool


class CurrentUser(BaseModel):
    id: int
    username: str
    full_name: str
    role: str
    is_admin: bool
    permissions: PermissionSet
    leader_person: LeaderRef | None = None
    leader_group_type: GroupType | None = None
    next_group_type: GroupType | None = None


class SessionResponse(BaseModel):
    user: CurrentUser
    csrf_token: str


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=10, max_length=128)


class SessionInfo(BaseModel):
    id: int
    created_at: datetime
    last_seen_at: datetime
    expires_at: datetime
    ip: str | None = None
    user_agent: str | None = None
    current: bool = False
