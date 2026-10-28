from dataclasses import dataclass

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.errors import AppError, forbidden, unauthorized
from app.core.security import csrf_matches
from app.models.user import User, UserSession
from app.permissions import policy
from app.services import auth as auth_service


@dataclass
class AuthContext:
    user: User
    session: UserSession


def client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def get_auth_context(
    request: Request, db: Session = Depends(get_db)
) -> AuthContext:
    token = request.cookies.get(settings.session_cookie_name)
    session = auth_service.get_active_session(db, token)
    if session is None:
        raise unauthorized("Нэвтрэлтийн хугацаа дууссан эсвэл нэвтрээгүй байна. Дахин нэвтэрнэ үү.")
    return AuthContext(user=session.user, session=session)


def require_csrf(
    request: Request, ctx: AuthContext = Depends(get_auth_context)
) -> AuthContext:
    provided = request.headers.get("X-CSRF-Token")
    if not csrf_matches(ctx.session.csrf_token, provided):
        raise AppError(
            403,
            "Хүсэлтийн аюулгүй байдлын токен буруу байна. Хуудсыг дахин ачаална уу.",
            code="CSRF_FAILED",
        )
    return ctx


def require_admin(ctx: AuthContext = Depends(get_auth_context)) -> AuthContext:
    if not policy.is_admin(ctx.user):
        raise forbidden("Энэ үйлдлийг зөвхөн администратор гүйцэтгэнэ.")
    return ctx


def require_admin_csrf(ctx: AuthContext = Depends(require_csrf)) -> AuthContext:
    if not policy.is_admin(ctx.user):
        raise forbidden("Энэ үйлдлийг зөвхөн администратор гүйцэтгэнэ.")
    return ctx
