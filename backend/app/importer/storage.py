import os
import uuid
from pathlib import Path

from fastapi import UploadFile

from app.core.config import settings
from app.core.errors import bad_request

ALLOWED_SUFFIXES = {".csv", ".xlsx"}
CHUNK_SIZE = 1024 * 1024


def save_upload(file: UploadFile) -> tuple[Path, str]:
    display_name = os.path.basename(file.filename or "").strip()[:255]
    suffix = Path(display_name).suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise bad_request("Зөвхөн .csv эсвэл .xlsx файл оруулна уу.")
    if not display_name:
        display_name = f"import{suffix}"

    settings.imports_path.mkdir(parents=True, exist_ok=True)
    path = settings.imports_path / f"{uuid.uuid4().hex}{suffix}"
    total = 0
    try:
        with path.open("wb") as handle:
            while chunk := file.file.read(CHUNK_SIZE):
                total += len(chunk)
                if total > settings.import_max_bytes:
                    limit_mb = settings.import_max_bytes // (1024 * 1024)
                    raise bad_request(
                        f"Файлын хэмжээ {limit_mb} MB-аас хэтрэхгүй байх ёстой."
                    )
                handle.write(chunk)
    except Exception:
        path.unlink(missing_ok=True)
        raise
    if total == 0:
        path.unlink(missing_ok=True)
        raise bad_request("Файл хоосон байна.")
    return path, display_name


def delete_file(path: str) -> None:
    try:
        Path(path).unlink(missing_ok=True)
    except OSError:
        pass
