from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.core.validation import clean_text, validate_username
from app.models.enums import Role
from app.schemas.common import LeaderRef, ORMModel


class UserListItem(ORMModel):
    id: int
    username: str
    full_name: str
    role: Role
    is_active: bool
    created_at: datetime
    leader_person: LeaderRef | None = None


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    full_name: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=10, max_length=128)
    role: Role = Role.LEADER
    leader_person_id: int | None = None

    @field_validator("username")
    @classmethod
    def normalize_username_field(cls, value: str) -> str:
        return validate_username(value)

    @field_validator("full_name")
    @classmethod
    def normalize_full_name(cls, value: str) -> str:
        cleaned = clean_text(value)
        if not cleaned:
            raise ValueError("Бүтэн нэр хоосон байж болохгүй.")
        return cleaned


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=120)
    role: Role | None = None
    is_active: bool | None = None
    leader_person_id: int | None = None

    @field_validator("full_name")
    @classmethod
    def normalize_full_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = clean_text(value)
        if not cleaned:
            raise ValueError("Бүтэн нэр хоосон байж болохгүй.")
        return cleaned


class PasswordResetRequest(BaseModel):
    new_password: str = Field(min_length=10, max_length=128)


class PersonAccountCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=10, max_length=128)

    @field_validator("username")
    @classmethod
    def normalize_username_field(cls, value: str) -> str:
        return validate_username(value)


class PersonAccountOut(ORMModel):
    id: int
    username: str
    role: Role
    is_active: bool
    created_at: datetime


class PersonAccountState(BaseModel):
    account: PersonAccountOut | None = None


class UserPage(BaseModel):
    items: list[UserListItem]
    page: int
    page_size: int
    total: int
    total_pages: int
