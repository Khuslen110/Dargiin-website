import uuid

from fastapi import APIRouter, Depends, File, Form, Query, Request, Response, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, client_ip, require_admin, require_admin_csrf
from app.core.database import get_db
from app.core.errors import not_found
from app.importer.storage import delete_file, save_upload
from app.repositories import imports as imports_repo
from app.schemas.common import Page
from app.schemas.import_job import ImportJobOut, ImportPreview
from app.services import imports as imports_service

router = APIRouter(prefix="/imports", tags=["imports"])


@router.post("/preview", response_model=ImportPreview)
def preview_import(
    request: Request,
    file: UploadFile = File(...),
    parent_id: int | None = Form(None),
    ctx: AuthContext = Depends(require_admin_csrf),
    db: Session = Depends(get_db),
) -> ImportPreview:
    path, filename = save_upload(file)
    job_id = uuid.uuid4()
    try:
        job = imports_service.create_uploaded_job(
            db, ctx.user, job_id=job_id, path=path, filename=filename, parent_id=parent_id
        )
        return imports_service.preview_job(
            db, ctx.user, job, ip=client_ip(request)
        )
    except Exception:
        delete_file(str(path))
        db.rollback()
        raise


@router.get("/template")
def download_template(
    ctx: AuthContext = Depends(require_admin),
) -> Response:
    return Response(
        content=imports_service.template_csv(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="import-template.csv"'},
    )


@router.get("", response_model=Page[ImportJobOut])
def list_imports(
    ctx: AuthContext = Depends(require_admin),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
) -> Page[ImportJobOut]:
    jobs, total = imports_repo.list_jobs(
        db, ctx.user, page=page, page_size=page_size
    )
    return Page[ImportJobOut](
        items=[imports_service.job_out(job) for job in jobs],
        page=page,
        page_size=page_size,
        total=total,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/{job_id}", response_model=ImportJobOut)
def get_import(
    job_id: uuid.UUID,
    ctx: AuthContext = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ImportJobOut:
    job = imports_repo.get_job(db, job_id)
    if job is None:
        raise not_found("Импортын ажил олдсонгүй.")
    return imports_service.job_out(job)


@router.post("/{job_id}/confirm", response_model=ImportJobOut)
def confirm_import(
    job_id: uuid.UUID,
    request: Request,
    ctx: AuthContext = Depends(require_admin_csrf),
    db: Session = Depends(get_db),
) -> ImportJobOut:
    return imports_service.confirm_job(
        db, ctx.user, job_id, ip=client_ip(request)
    )


@router.get("/{job_id}/errors.csv")
def download_errors(
    job_id: uuid.UUID,
    ctx: AuthContext = Depends(require_admin),
    db: Session = Depends(get_db),
) -> Response:
    job = imports_repo.get_job(db, job_id)
    if job is None:
        raise not_found("Импортын ажил олдсонгүй.")
    return Response(
        content=imports_service.error_report_csv(job),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="import-errors-{job_id}.csv"'
        },
    )
