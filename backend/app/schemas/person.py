from datetime import date, datetime

from pydantic import BaseModel, Field, computed_field, field_validator, model_validator

from app.core.time import age_from_birth_date
from app.core.validation import clean_text, validate_phone, validate_reg_number
from app.models.enums import Gender, GroupType, PersonStatus
from app.schemas.common import ORMModel, PersonRef, UserRef


class PersonSummary(ORMModel):
    id: int
    reg_number: str
    last_name: str
    first_name: str
    gender: Gender
    birth_date: date | None
    phone: str | None
    district: str | None
    khoroo: str | None
    group_type: GroupType
    parent_id: int | None
    status: PersonStatus
    full_profile: bool = True
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def age(self) -> int | None:
        return age_from_birth_date(self.birth_date)


class PersonPermissions(BaseModel):
    can_edit: bool
    can_add_child: bool
    can_delete: bool
    can_restore: bool
    can_purge: bool
    can_view_sensitive: bool
    can_view_full: bool
    can_manage_account: bool = False


class HierarchyNode(PersonSummary):
    direct_member_count: int = 0


class PersonDetail(PersonSummary):
    address: str | None
    job: str | None
    created_by: UserRef | None = None
    parent: PersonRef | None = None
    path: list[PersonRef] = []
    direct_member_count: int = 0
    deleted_at: datetime | None = None
    permissions: PersonPermissions


class PersonCreate(BaseModel):
    reg_number: str
    last_name: str = Field(min_length=1, max_length=80)
    first_name: str = Field(min_length=1, max_length=80)
    gender: Gender
    birth_date: date | None = None
    phone: str | None = None
    district: str | None = Field(default=None, max_length=80)
    khoroo: str | None = Field(default=None, max_length=80)
    address: str | None = Field(default=None, max_length=255)
    job: str | None = Field(default=None, max_length=120)
    group_type: GroupType
    parent_id: int | None = None

    @field_validator("reg_number")
    @classmethod
    def reg_number(cls, value: str) -> str:
        return validate_reg_number(value)

    @field_validator("last_name", "first_name")
    @classmethod
    def name(cls, value: str) -> str:
        cleaned = clean_text(value)
        if not cleaned:
            raise ValueError("Овог, нэр хоосон байж болохгүй.")
        return cleaned

    @field_validator("phone")
    @classmethod
    def normalize_phone_field(cls, value: str | None) -> str | None:
        return validate_phone(value)

    @field_validator("district", "khoroo", "address", "job")
    @classmethod
    def optional_text(cls, value: str | None) -> str | None:
        return clean_text(value)

    @field_validator("birth_date")
    @classmethod
    def birth_date_not_future(cls, value: date | None) -> date | None:
        if value is None:
            return None
        if value > date.today():
            raise ValueError("Төрсөн огноо ирээдүйн огноо байж болохгүй.")
        if value.year < 1900:
            raise ValueError("Төрсөн огноо 1900 оноос хойш байх ёстой.")
        return value


class PersonUpdate(BaseModel):
    last_name: str | None = Field(default=None, min_length=1, max_length=80)
    first_name: str | None = Field(default=None, min_length=1, max_length=80)
    gender: Gender | None = None
    birth_date: date | None = None
    phone: str | None = None
    district: str | None = Field(default=None, max_length=80)
    khoroo: str | None = Field(default=None, max_length=80)
    address: str | None = Field(default=None, max_length=255)
    job: str | None = Field(default=None, max_length=120)
    group_type: GroupType | None = None
    parent_id: int | None = None

    @field_validator("last_name", "first_name")
    @classmethod
    def name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = clean_text(value)
        if not cleaned:
            raise ValueError("Овог, нэр хоосон байж болохгүй.")
        return cleaned

    @field_validator("phone")
    @classmethod
    def normalize_phone_field(cls, value: str | None) -> str | None:
        return validate_phone(value)

    @field_validator("district", "khoroo", "address", "job")
    @classmethod
    def optional_text(cls, value: str | None) -> str | None:
        return clean_text(value)

    @field_validator("birth_date")
    @classmethod
    def birth_date_not_future(cls, value: date | None) -> date | None:
        if value is None:
            return None
        if value > date.today():
            raise ValueError("Төрсөн огноо ирээдүйн огноо байж болохгүй.")
        if value.year < 1900:
            raise ValueError("Төрсөн огноо 1900 оноос хойш байх ёстой.")
        return value

    @model_validator(mode="after")
    def at_least_one_field(self) -> "PersonUpdate":
        if not self.model_fields_set:
            raise ValueError("Өөрчлөх талбар сонгоогүй байна.")
        return self


class PersonSearchParams(BaseModel):
    reg_number: str | None = None
    last_name: str | None = None
    first_name: str | None = None
    phone: str | None = None
    district: str | None = None
    khoroo: str | None = None
    address: str | None = None
    job: str | None = None
    gender: Gender | None = None
    age_min: int | None = Field(default=None, ge=0, le=120)
    age_max: int | None = Field(default=None, ge=0, le=120)
    group_type: GroupType | None = None
    under_person_id: int | None = None
    direct_only: bool = False
    status: PersonStatus = PersonStatus.ACTIVE


class ParentCandidate(ORMModel):
    id: int
    reg_number: str
    last_name: str
    first_name: str
    group_type: GroupType


class PurgeRequest(BaseModel):
    confirm_reg_number: str


__all__ = [
    "HierarchyNode",
    "ParentCandidate",
    "PersonCreate",
    "PersonDetail",
    "PersonPermissions",
    "PersonSearchParams",
    "PersonSummary",
    "PersonUpdate",
    "PersonRef",
    "PurgeRequest",
]
