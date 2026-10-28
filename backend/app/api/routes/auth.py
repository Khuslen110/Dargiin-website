from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.api.deps import AuthContext, client_ip, get_auth_context, require_csrf
from app.core.config import settings
from app.core.database import get_db
from app.core.errors import AppError
from app.core.rate_limit import login_limiter
from app.schemas.auth import ChangePasswordRequest, CurrentUser, LoginRequest, SessionResponse
from app.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=SessionResponse)
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> SessionResponse:
    ip = client_ip(request)
    rate_key = f"{ip or 'unknown'}:{payload.username}"
    allowed, retry_after = login_limiter.hit(rate_key)
    if not allowed:
        raise AppError(
            429,
            f"Хэт олон удаа нэвтрэх оролдлого хийсэн байна. {retry_after} секундын дараа дахин оролдоно уу.",
            code="RATE_LIMITED",
        )
    issued = auth_service.authenticate(
        db,
        username=payload.username,
        password=payload.password,
        ip=ip,
        user_agent=request.headers.get("user-agent"),
    )
    login_limiter.reset(rate_key)
    auth_service.set_session_cookies(
        response, token=issued.token, csrf_token=issued.csrf_token
    )
    user_data = auth_service.user_public(issued.session.user)
    return SessionResponse(
        user=CurrentUser(**user_data), csrf_token=issued.csrf_token
    )


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    ctx: AuthContext = Depends(require_csrf),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    auth_service.logout(db, ctx.session, ip=client_ip(request))
    auth_service.clear_session_cookies(response)
    return {"message": "Амжилттай гарлаа."}


@router.get("/me", response_model=SessionResponse)
def me(ctx: AuthContext = Depends(get_auth_context)) -> SessionResponse:
    return SessionResponse(
        user=CurrentUser(**auth_service.user_public(ctx.user)),
        csrf_token=ctx.session.csrf_token,
    )


@router.post("/change-password")
def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    response: Response,
    ctx: AuthContext = Depends(require_csrf),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    auth_service.change_password(
        db,
        ctx.session,
        current_password=payload.current_password,
        new_password=payload.new_password,
        ip=client_ip(request),
    )
    auth_service.set_session_cookies(
        response,
        token=request.cookies.get(settings.session_cookie_name) or "",
        csrf_token=ctx.session.csrf_token,
    )
    return {"message": "Нууц үг амжилттай солигдлоо."}
