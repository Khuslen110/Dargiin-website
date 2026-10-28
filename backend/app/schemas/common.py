from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import GroupType

T = TypeVar("T")


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Page(BaseModel, Generic[T]):
    items: list[T]
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    total: int = Field(ge=0)
    total_pages: int = Field(ge=0)


class UserRef(ORMModel):
    id: int
    username: str
    full_name: str


class PersonRef(ORMModel):
    id: int
    reg_number: str
    last_name: str
    first_name: str
    status: str


class LeaderRef(ORMModel):
    id: int
    reg_number: str
    last_name: str
    first_name: str
    group_type: GroupType
    status: str
