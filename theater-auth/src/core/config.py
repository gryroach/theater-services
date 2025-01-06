import os

from logging import config as logging_config
from typing import Any

from dotenv import find_dotenv, load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from core.logger import LOGGING

logging_config.dictConfig(LOGGING)
DOTENV_PATH = find_dotenv(".env")
load_dotenv(DOTENV_PATH)


class AppSettings(BaseSettings):
    project_name: str = Field(default="Movies auth API")
    api_production: bool = Field(default=True)

    # Настройки Postgres
    postgres_user: str = Field(default="postgres")
    postgres_password: str = Field(default="pass")
    postgres_host: str = Field(default="db")
    postgres_port: int = Field(default=5432)
    postgres_db: str = Field(default="movies_auth")
    echo_queries: bool = Field(default=False)
    test_db: str = Field(default="test_db")

    # Настройки Redis
    redis_host: str = Field(default="redis")
    redis_port: int = Field(default=6379)
    redis_db: int = Field(default=1)
    test_redis_host: str = Field(default="redis")
    test_redis_port: int = Field(default=6379)
    test_redis_db: int = Field(default=0)

    # Настройки аутентификации
    ACCESS_TOKEN_EXPIRE_DAYS: int = Field(default=7)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=30)
    private_key: str = Field(default="/app/keys/private_key.pem")
    public_key: str = Field(default="/app/keys/public_key.pem")
    jwt_algorithm: str = Field(default="RS256")

    # Константы
    SESSION_VERSION_KEY_TEMPLATE: str = "session_version:{}"
    INVALID_REFRESH_TOKEN_TEMPLATE: str = "invalid:refresh:{}"

    # Трассировка
    jaeger_host: str = Field(default="jaeger")
    jaeger_port: int = Field(default=6831)

    # Google OAuth
    google_client_file_path: str = Field(
        default="/app/keys/google_oauth_client_secret.json"
    )
    google_redirect_host: str = Field(default="localhost")
    google_client_id: str = Field()

    # Другие настройки
    test_mode: bool = Field(default=False)
    request_limit_per_minute: int = Field(default=20)

    model_config = SettingsConfigDict(
        env_file=DOTENV_PATH,
        env_file_encoding="utf-8",
        extra="ignore",
        env_prefix="auth_"
    )

    def model_post_init(self, __context: Any) -> None:
        if not self.api_production:
            os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    @property
    def database_dsn(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:"
            f"{self.postgres_password}@"
            f"{self.postgres_host}:"
            f"{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def test_database_dsn(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:"
            f"{self.postgres_password}@"
            f"{self.postgres_host}:"
            f"{self.postgres_port}/{self.test_db}"
        )

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"


settings = AppSettings()
