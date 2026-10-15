from datetime import datetime
from typing import Annotated, Self

from fastapi import APIRouter, Depends, Request, Response
from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)

from app.application.auth import AuthService
from app.domain.user import User
from app.presentation.auth_dependencies import get_auth_service, get_current_user
from app.presentation.session_cookie import (
    clear_session,
    require_browser_request,
    set_session,
)

router = APIRouter(prefix="/api/v1/auth", tags=["Autenticação"])


class Credentials(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: EmailStr = Field(max_length=254)
    password: str = Field(min_length=8, max_length=128, repr=False)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value):
        return value.strip().casefold() if isinstance(value, str) else value


class Registration(Credentials):
    name: str = Field(default="", max_length=100)

    @field_validator("name")
    @classmethod
    def trim_name(cls, value: str) -> str:
        return value.strip()


class ProfileUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = Field(default=None, min_length=1, max_length=100)
    email: EmailStr | None = Field(default=None, max_length=254)

    @field_validator("name", "email", mode="before")
    @classmethod
    def normalize(cls, value, info):
        if isinstance(value, str):
            return (
                value.strip().casefold()
                if info.field_name == "email"
                else value.strip()
            )
        return value

    @model_validator(mode="after")
    def valid_changes(self) -> Self:
        if not self.model_fields_set or any(
            getattr(self, field) is None for field in self.model_fields_set
        ):
            raise ValueError("Informe nome ou e-mail válidos")
        return self


class PasswordChange(BaseModel):
    model_config = ConfigDict(extra="forbid")
    current_password: str = Field(min_length=1, max_length=128, repr=False)
    password: str = Field(min_length=8, max_length=128, repr=False)


class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    created_at: datetime | None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


@router.post("/register", response_model=UserResponse, status_code=201)
def register(
    data: Registration, service: Annotated[AuthService, Depends(get_auth_service)]
):
    return service.register(str(data.email), data.password, data.name)


@router.post("/login", response_model=TokenResponse)
def login(
    data: Credentials,
    request: Request,
    response: Response,
    service: Annotated[AuthService, Depends(get_auth_service)],
):
    token = service.login(str(data.email), data.password)
    duration = request.app.state.settings.access_token_expire_minutes * 60
    set_session(response, request, token, duration)
    return TokenResponse(access_token=token, expires_in=duration)


@router.post("/logout", status_code=204)
def logout(request: Request, response: Response) -> None:
    require_browser_request(request)
    clear_session(response, request)


@router.get("/me", response_model=UserResponse)
def me(user: Annotated[User, Depends(get_current_user)], response: Response):
    response.headers["Cache-Control"] = "no-store"
    return user


@router.patch("/me", response_model=UserResponse)
def update_me(
    data: ProfileUpdate,
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[AuthService, Depends(get_auth_service)],
):
    return service.update_profile(user.id, data.model_dump(exclude_unset=True))


@router.post("/change-password", status_code=204)
def change_password(
    data: PasswordChange,
    user: Annotated[User, Depends(get_current_user)],
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> Response:
    service.change_password(user, data.current_password, data.password)
    return Response(status_code=204)
