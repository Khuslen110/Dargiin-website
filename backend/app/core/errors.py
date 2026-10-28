from typing import Any


class AppError(Exception):
    """Хэрэглэгчид харуулах аюулгүй алдаа. Дотоод дэлгэрэнгүй мэдээлэл агуулахгүй."""

    def __init__(
        self,
        status_code: int,
        detail: str,
        *,
        code: str | None = None,
        fields: dict[str, str] | None = None,
    ) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail
        self.code = code
        self.fields = fields


def bad_request(detail: str, *, code: str | None = None, fields: dict[str, str] | None = None) -> AppError:
    return AppError(400, detail, code=code, fields=fields)


def unauthorized(detail: str = "Нэвтрэх шаардлагатай.") -> AppError:
    return AppError(401, detail, code="UNAUTHORIZED")


def forbidden(detail: str = "Танд энэ үйлдэл хийх эрх байхгүй.") -> AppError:
    return AppError(403, detail, code="FORBIDDEN")


def not_found(detail: str = "Бичлэг олдсонгүй.") -> AppError:
    return AppError(404, detail, code="NOT_FOUND")


def conflict(detail: str, *, code: str | None = None, fields: dict[str, str] | None = None) -> AppError:
    return AppError(409, detail, code=code, fields=fields)


def error_payload(
    detail: str, *, code: str | None = None, fields: dict[str, Any] | None = None
) -> dict[str, Any]:
    payload: dict[str, Any] = {"detail": detail}
    if code:
        payload["code"] = code
    if fields:
        payload["fields"] = fields
    return payload
