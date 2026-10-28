from dataclasses import dataclass
from datetime import timedelta
from functools import lru_cache

from fastapi import Response
from sqlalchemy.orm import Session

from app.core.audit_actions import AuditAction
from app.core.config import settings
from app.core.errors import forbidden, unauthorized
from app.core.security import (
    generate_csrf_token,
    generate_token,
    hash_password,
    hash_token,
    needs_rehash,
    password_policy_errors,
    verify_password,
)
from app.core.time import now_utc
from app.models.user import User, UserSession
from app.repositories import users as users_repo
from app.services import audit as audit_service

IDLE_REFRESH_SECONDS = 600


@dataclass
class IssuedSession:
    token: str
    csrf_token: str
    session: UserSession


@lru_cache(maxsize=1)
def _dummy_hash() -> str:
    return hash_password("timing-equalizer-not-a-real-password-123")


def authenticate(
    db: Session,
    *,
    username: str,
    password: str,
    ip: str | None,
    user_agent: str | None,
) -> IssuedSession:
    user = users_repo.get_by_username(db, username)
    if user is None:
        verify_password(_dummy_hash(), password)
        audit_service.log(
            db,
            actor=None,
            action=AuditAction.LOGIN_FAILED,
            metadata={"username": username, "reason": "invalid_credentials"},
            ip=ip,
        )
        db.commit()
        raise unauthorized("Хэрэглэгчийн нэр эсвэл нууц үг буруу.")

    if not verify_password(user.password_hash, password) or not user.is_active:
        audit_service.log(
            db,
            actor=user,
            action=AuditAction.LOGIN_FAILED,
            metadata={"reason": "invalid_credentials"},
            ip=ip,
        )
        db.commit()
        raise unauthorized("Хэрэглэгчийн нэр эсвэл нууц үг буруу.")

    if needs_rehash(user.password_hash):
        user.password_hash = hash_password(password)

    token = generate_token()
    csrf_token = generate_csrf_token()
    session = UserSession(
        user_id=user.id,
        token_hash=hash_token(token),
        csrf_token=csrf_token,
        ip=ip,
        user_agent=(user_agent[:255] if user_agent else None),
        expires_at=now_utc() + timedelta(hours=settings.session_ttl_hours),
        last_seen_at=now_utc(),
    )
    users_repo.add_session(db, session)
    audit_service.log(
        db, actor=user, action=AuditAction.LOGIN_SUCCESS, entity_type="user", entity_id=user.id, ip=ip
    )
    db.commit()
    db.refresh(session)
    return IssuedSession(token=token, csrf_token=csrf_token, session=session)


def get_active_session(db: Session, raw_token: str | None) -> UserSession | None:
    if not raw_token:
        return None
    session = users_repo.get_session_by_hash(db, hash_token(raw_token))
    now = now_utc()
    if session is None or session.revoked_at is not None:
        return None
    if session.expires_at <= now or not session.user.is_active:
        return None
    if (now - session.last_seen_at).total_seconds() > IDLE_REFRESH_SECONDS:
        session.last_seen_at = now
        db.commit()
    return session


def logout(db: Session, session: UserSession, *, ip: str | None = None) -> None:
    session.revoked_at = now_utc()
    audit_service.log(
        db,
        actor=session.user,
        action=AuditAction.LOGOUT,
        entity_type="user",
        entity_id=session.user_id,
        ip=ip,
    )
    db.commit()


def change_password(
    db: Session,
    current_session: UserSession,
    *,
    current_password: str,
    new_password: str,
    ip: str | None = None,
) -> None:
    user = current_session.user
    if not verify_password(user.password_hash, current_password):
        raise forbidden("Одоогийн нууц үг буруу байна.")
    errors = password_policy_errors(new_password)
    if errors:
        raise forbidden(" ".join(errors))
    if verify_password(user.password_hash, new_password):
        raise forbidden("Шинэ нууц үг одоогийн нууц үгээс ялгаатай байх ёстой.")

    user.password_hash = hash_password(new_password)
    users_repo.revoke_user_sessions(db, user.id, except_session_id=current_session.id)
    audit_service.log(
        db,
        actor=user,
        action=AuditAction.PASSWORD_CHANGED,
        entity_type="user",
        entity_id=user.id,
        ip=ip,
    )
    db.commit()


def set_session_cookies(response: Response, *, token: str, csrf_token: str) -> None:
    max_age = settings.session_ttl_hours * 3600
    common = {
        "max_age": max_age,
        "path": "/",
        "secure": settings.cookie_secure,
        "samesite": "lax",
        "domain": settings.cookie_domain or None,
    }
    response.set_cookie(settings.session_cookie_name, token, httponly=True, **common)
    response.set_cookie(settings.csrf_cookie_name, csrf_token, httponly=False, **common)


def clear_session_cookies(response: Response) -> None:
    response.delete_cookie(
        settings.session_cookie_name,
        path="/",
        domain=settings.cookie_domain or None,
        secure=settings.cookie_secure,
        samesite="lax",
    )
    response.delete_cookie(
        settings.csrf_cookie_name,
        path="/",
        domain=settings.cookie_domain or None,
        secure=settings.cookie_secure,
        samesite="lax",
    )


def user_public(user: User) -> dict:
    from app.core.group_rules import next_group_type
    from app.permissions.policy import permission_set
    from app.schemas.common import LeaderRef

    leader = user.leader_person
    next_type = next_group_type(leader.group_type) if leader else None
    return {
        "id": user.id,
        "username": user.username,
        "full_name": user.full_name,
        "role": user.role.value,
        "is_admin": user.is_admin,
        "permissions": permission_set(user),
        "leader_person": LeaderRef.model_validate(leader) if leader else None,
        "leader_group_type": leader.group_type.value if leader else None,
        "next_group_type": next_type.value if next_type else None,
    }
