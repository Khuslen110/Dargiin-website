from typing import Literal

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, client_ip, get_auth_context
from app.core.database import get_db
from app.models.enums import Gender, GroupType
from app.services import exports as exports_service

router = APIRouter(prefix="/exports", tags=["exports"])


@router.get("/people")
def export_people(
    request: Request,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
    fmt: Literal["csv", "xlsx"] = "csv",
    reg_number: str | None = None,
    last_name: str | None = None,
    first_name: str | None = None,
    phone: str | None = None,
    district: str | None = None,
    khoroo: str | None = None,
    address: str | None = None,
    job: str | None = None,
    gender: Gender | None = None,
    age_min: int | None = None,
    age_max: int | None = None,
    group_type: GroupType | None = None,
    under_person_id: int | None = None,
    direct_only: bool = False,
) -> Response:
    filters = {
        "reg_number": reg_number,
        "last_name": last_name,
        "first_name": first_name,
        "phone": phone,
        "district": district,
        "khoroo": khoroo,
        "address": address,
        "job": job,
        "gender": gender,
        "age_min": age_min,
        "age_max": age_max,
        "group_type": group_type,
        "under_person_id": under_person_id,
        "direct_only": direct_only,
    }
    filters = {key: value for key, value in filters.items() if value not in (None, "")}
    content, filename, content_type, truncated, count = exports_service.export_people(
        db,
        ctx.user,
        fmt=fmt,
        filters=filters,
        ip=client_ip(request),
    )
    return Response(
        content=content,
        media_type=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Export-Count": str(count),
            "X-Export-Truncated": "true" if truncated else "false",
        },
    )
