from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.models.enums import ImportStatus


class ImportErrorItem(BaseModel):
    row: int
    message: str
    field: str | None = None


class ImportPreview(BaseModel):
    job_id: str
    filename: str
    total_rows: int
    valid_rows: int
    invalid_rows: int
    errors: list[ImportErrorItem]
    can_confirm: bool
    accounts_planned: int = 0


class ImportJobOut(BaseModel):
    id: str
    filename: str
    status: ImportStatus
    total_rows: int
    valid_rows: int
    invalid_rows: int
    imported_rows: int
    accounts_created: int
    errors: list[dict[str, Any]]
    created_at: datetime
    completed_at: datetime | None


class ImportConfirmResult(BaseModel):
    job: ImportJobOut
    imported_rows: int
    invalid_rows: int
