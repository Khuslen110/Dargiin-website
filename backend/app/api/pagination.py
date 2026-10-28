import math

from fastapi import Query

from app.core.config import settings
from app.schemas.common import Page


def page_params(
    page: int = Query(1, ge=1),
    page_size: int = Query(
        settings.page_size_default, ge=1, le=settings.page_size_max
    ),
) -> tuple[int, int]:
    return page, page_size


def total_pages(total: int, page_size: int) -> int:
    return math.ceil(total / page_size) if total else 0


def build_page(items: list, *, page: int, page_size: int, total: int, schema):
    return Page[schema](
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages(total, page_size),
    )
