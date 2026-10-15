from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.application.auth import AuthService
from app.domain.errors import AuthenticationError
from app.domain.user import User
from app.infrastructure.auth import JwtTokens, SqlUserRepository, get_passwords
from app.presentation.dependencies import get_session
from app.presentation.session_cookie import SESSION_COOKIE, require_browser_request

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
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> User:
    if request.headers.get("Authorization"):
        if credentials is None:
            raise AuthenticationError("Autenticação necessária")
        return service.authenticate(credentials.credentials)
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        raise AuthenticationError("Autenticação necessária")
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        require_browser_request(request)
    return service.authenticate(token)
