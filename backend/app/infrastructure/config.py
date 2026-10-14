from typing import Literal
from urllib.parse import urlsplit

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        hide_input_in_errors=True,
    )

    jwt_secret: SecretStr
    jwt_algorithm: Literal["HS256"] = "HS256"
    access_token_expire_minutes: int = Field(default=30, ge=1, le=1440)
    database_url: str = "sqlite:///./data/taskflow.db"
    cors_origins: list[str] = Field(default_factory=list)

    @field_validator("jwt_secret")
    @classmethod
    def validate_secret(cls, value: SecretStr) -> SecretStr:
        if len(value.get_secret_value().strip()) < 32:
            raise ValueError("JWT_SECRET deve conter pelo menos 32 caracteres")
        return value

    @field_validator("database_url")
    @classmethod
    def validate_database(cls, value: str) -> str:
        try:
            url = make_url(value)
        except ArgumentError as error:
            raise ValueError("DATABASE_URL inválida") from error
        if url.drivername != "sqlite" or not url.database:
            raise ValueError("DATABASE_URL deve apontar para um banco SQLite")
        if url.query:
            raise ValueError("Parâmetros na URL SQLite não são suportados")
        return value

    @field_validator("cors_origins")
    @classmethod
    def validate_origins(cls, values: list[str]) -> list[str]:
        for value in values:
            parsed = urlsplit(value)
            if (
                parsed.scheme not in {"http", "https"}
                or not parsed.hostname
                or parsed.username
                or parsed.password
                or parsed.path
                or parsed.query
                or parsed.fragment
                or "*" in value
            ):
                raise ValueError("CORS_ORIGINS deve conter origens HTTP explícitas")
            try:
                _ = parsed.port
            except ValueError as error:
                raise ValueError("Porta inválida em CORS_ORIGINS") from error
        return values
