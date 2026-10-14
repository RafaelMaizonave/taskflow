from typing import Annotated

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.application.auth import AuthService
from app.domain.user import User
from app.presentation.auth_dependencies import get_auth_service, get_current_user

router = APIRouter(prefix="/api/v1/auth", tags=["Autenticação"])


class Credentials(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: EmailStr = Field(max_length=254)
    password: str = Field(min_length=8, max_length=128, repr=False)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value):
        return value.strip().casefold() if isinstance(value, str) else value


class UserResponse(BaseModel):
    id: int
    email: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


@router.post("/register", response_model=UserResponse, status_code=201)
def register(
    data: Credentials, service: Annotated[AuthService, Depends(get_auth_service)]
):
    return service.register(str(data.email), data.password)


@router.post("/login", response_model=TokenResponse)
def login(
    data: Credentials,
    request: Request,
    service: Annotated[AuthService, Depends(get_auth_service)],
):
    return TokenResponse(
        access_token=service.login(str(data.email), data.password),
        expires_in=request.app.state.settings.access_token_expire_minutes * 60,
    )


@router.get("/me", response_model=UserResponse)
def me(user: Annotated[User, Depends(get_current_user)]):
    return user
