from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Бүх тохиргоог нэг газраас удирдана. Нууц утгууд env-ээс ирнэ."""

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "Хүмүүсийн бүртгэлийн систем"
    app_env: str = "development"
    api_prefix: str = "/api"
    app_version: str = "1.0.0"

    database_url: str = (
        "postgresql+psycopg://postgres:postgres@localhost:5432/people_registry"
    )
    test_database_url: str = (
        "postgresql+psycopg://postgres:postgres@localhost:5432/people_registry_test"
    )

    secret_key: str = "dev-only-insecure-key"
    session_cookie_name: str = "pr_session"
    csrf_cookie_name: str = "pr_csrf"
    session_ttl_hours: int = 8
    cookie_secure: bool = False
    cookie_domain: str | None = None
    allowed_origins: str = "http://localhost:5173"

    timezone: str = "Asia/Ulaanbaatar"

    page_size_default: int = 20
    page_size_max: int = 100
    export_max_rows: int = 50_000

    import_dir: Path = Path("var/imports")
    import_max_bytes: int = 10 * 1024 * 1024
    import_max_rows: int = 50_000

    login_rate_limit: int = 10
    login_rate_window_seconds: int = 300

    admin_initial_password: str | None = Field(default=None)

    @property
    def allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def imports_path(self) -> Path:
        path = self.import_dir
        if not path.is_absolute():
            path = Path.cwd() / path
        return path


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
