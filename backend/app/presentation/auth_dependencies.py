from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.application.auth import AuthService
from app.domain.errors import AuthenticationError
from app.domain.user import User
from app.infrastructure.auth import JwtTokens, SqlUserRepository, get_passwords
from app.presentation.dependencies import get_session

bearer = HTTPBearer(auto_error=False)


def get_auth_service(
    request: Request, session: Annotated[Session, Depends(get_session)]
) -> AuthService:
    return AuthService(
        SqlUserRepository(session),
        get_passwords(),
        JwtTokens(request.app.state.settings),
    )


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> User:
    if credentials is None:
        raise AuthenticationError("Autenticação necessária")
    return service.authenticate(credentials.credentials)
