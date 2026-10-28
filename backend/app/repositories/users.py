from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, selectinload

from app.models.enums import Role
from app.models.user import User, UserSession


def _user_options():
    return selectinload(User.leader_person)


def get_by_id(db: Session, user_id: int) -> User | None:
    stmt = select(User).options(_user_options()).where(User.id == user_id)
    return db.scalars(stmt).first()


def get_by_username(db: Session, username: str) -> User | None:
    stmt = (
        select(User)
        .options(_user_options())
        .where(func.lower(User.username) == username.lower())
    )
    return db.scalars(stmt).first()


def username_exists(db: Session, username: str, exclude_id: int | None = None) -> bool:
    stmt = select(User.id).where(func.lower(User.username) == username.lower())
    if exclude_id is not None:
        stmt = stmt.where(User.id != exclude_id)
    return db.scalars(stmt).first() is not None


def list_users(db: Session, *, page: int, page_size: int, search: str | None) -> tuple[list[User], int]:
    conditions = []
    if search:
        term = f"%{search.strip()}%"
        conditions.append(User.full_name.ilike(term) | User.username.ilike(term))
    base: Select = select(User).options(_user_options())
    count_stmt = select(func.count()).select_from(User)
    for condition in conditions:
        base = base.where(condition)
        count_stmt = count_stmt.where(condition)
    total = db.scalar(count_stmt) or 0
    items = list(
        db.scalars(
            base.order_by(User.created_at.desc(), User.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    )
    return items, total


def get_by_leader_person_id(db: Session, person_id: int) -> User | None:
    stmt = (
        select(User)
        .options(_user_options())
        .where(User.leader_person_id == person_id)
    )
    return db.scalars(stmt).first()


def leader_person_taken(
    db: Session, person_id: int, exclude_user_id: int | None = None
) -> bool:
    stmt = select(User.id).where(User.leader_person_id == person_id)
    if exclude_user_id is not None:
        stmt = stmt.where(User.id != exclude_user_id)
    return db.scalars(stmt).first() is not None


def count_active_admins(db: Session) -> int:
    return (
        db.scalar(
            select(func.count())
            .select_from(User)
            .where(User.role == Role.ADMIN, User.is_active.is_(True))
        )
        or 0
    )


def add_session(db: Session, session: UserSession) -> None:
    db.add(session)


def get_session_by_hash(db: Session, token_hash: str) -> UserSession | None:
    stmt = (
        select(UserSession)
        .options(selectinload(UserSession.user).selectinload(User.leader_person))
        .where(UserSession.token_hash == token_hash)
    )
    return db.scalars(stmt).first()


def revoke_user_sessions(db: Session, user_id: int, *, except_session_id: int | None = None) -> int:
    from datetime import UTC, datetime

    stmt = select(UserSession).where(
        UserSession.user_id == user_id, UserSession.revoked_at.is_(None)
    )
    if except_session_id is not None:
        stmt = stmt.where(UserSession.id != except_session_id)
    sessions = list(db.scalars(stmt))
    now = datetime.now(UTC)
    for session in sessions:
        session.revoked_at = now
    return len(sessions)


def active_sessions(db: Session, user_id: int) -> list[UserSession]:
    from datetime import UTC, datetime

    stmt = (
        select(UserSession)
        .where(
            UserSession.user_id == user_id,
            UserSession.revoked_at.is_(None),
            UserSession.expires_at > datetime.now(UTC),
        )
        .order_by(UserSession.created_at.desc())
    )
    return list(db.scalars(stmt))
