import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.import_job import ImportJob
from app.models.user import User
from app.permissions.policy import is_admin


def create_job(
    db: Session,
    *,
    job_id: uuid.UUID,
    user_id: int,
    filename: str,
    file_path: str,
    parent_id: int | None = None,
) -> ImportJob:
    job = ImportJob(
        id=job_id,
        user_id=user_id,
        filename=filename,
        file_path=file_path,
        parent_id=parent_id,
    )
    db.add(job)
    db.flush()
    return job


def get_job(db: Session, job_id: uuid.UUID) -> ImportJob | None:
    return db.get(ImportJob, job_id)


def get_job_for_update(db: Session, job_id: uuid.UUID) -> ImportJob | None:
    return db.scalars(
        select(ImportJob).where(ImportJob.id == job_id).with_for_update()
    ).first()


def list_jobs(
    db: Session, user: User, *, page: int, page_size: int
) -> tuple[list[ImportJob], int]:
    conditions = []
    if not is_admin(user):
        conditions.append(ImportJob.user_id == user.id)
    count_stmt = select(func.count()).select_from(ImportJob)
    stmt = select(ImportJob)
    for condition in conditions:
        count_stmt = count_stmt.where(condition)
        stmt = stmt.where(condition)
    total = db.scalar(count_stmt) or 0
    stmt = (
        stmt.order_by(ImportJob.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return list(db.scalars(stmt)), total
