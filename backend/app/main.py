import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.api.routes import (
    audit,
    auth,
    dashboard,
    exports,
    hierarchy,
    imports,
    notifications,
    people,
    users,
)
from app.core.config import settings
from app.core.database import SessionLocal
from app.core.errors import AppError, error_payload
from app.core.time import now_utc

logger = logging.getLogger("people_registry")

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.imports_path.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    docs_url="/api/docs" if not settings.is_production else None,
    redoc_url=None,
    openapi_url="/api/openapi.json" if not settings.is_production else None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_middleware(request: Request, call_next):
    if request.method not in SAFE_METHODS and request.url.path.startswith(settings.api_prefix):
        origin = request.headers.get("origin")
        if origin and origin not in settings.allowed_origins_list:
            return JSONResponse(
                status_code=403,
                content=error_payload("Хүсэлтийн эх сурвалж зөвшөөрөгдөөгүй байна.", code="BAD_ORIGIN"),
            )

    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    if request.url.path.startswith(settings.api_prefix):
        response.headers["Cache-Control"] = "no-store"
    return response


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=error_payload(exc.detail, code=exc.code, fields=exc.fields),
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    fields: dict[str, str] = {}
    for error in exc.errors():
        location = [str(part) for part in error.get("loc", []) if part not in ("body", "query", "path")]
        field = location[-1] if location else "form"
        message = str(error.get("msg", "Буруу утга.")).removeprefix("Value error, ")
        fields.setdefault(field, message)
    return JSONResponse(
        status_code=422,
        content=error_payload(
            "Оруулсан мэдээлэл буруу байна.", code="VALIDATION_ERROR", fields=fields
        ),
    )


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    logger.warning("Unhandled integrity error on %s", request.url.path)
    return JSONResponse(
        status_code=409,
        content=error_payload(
            "Өгөгдлийн зөрчил гарлаа. Мэдээллээ шалгаад дахин оролдоно уу.",
            code="CONFLICT",
        ),
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error on %s", request.url.path)
    return JSONResponse(
        status_code=500,
        content=error_payload("Системийн алдаа гарлаа. Дахин оролдоно уу.", code="INTERNAL_ERROR"),
    )


@app.get(f"{settings.api_prefix}/health")
def health() -> dict[str, str]:
    with SessionLocal() as db:
        db.execute(text("SELECT 1"))
    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
        "database": "ok",
        "time": now_utc().isoformat(),
    }


api = settings.api_prefix
app.include_router(auth.router, prefix=api)
app.include_router(dashboard.router, prefix=api)
app.include_router(people.router, prefix=api)
app.include_router(hierarchy.router, prefix=api)
app.include_router(users.router, prefix=api)
app.include_router(audit.router, prefix=api)
app.include_router(notifications.router, prefix=api)
app.include_router(imports.router, prefix=api)
app.include_router(exports.router, prefix=api)


@app.get("/")
def root() -> dict[str, str]:
    return {"name": settings.app_name, "docs": "/api/docs", "health": f"{settings.api_prefix}/health"}
