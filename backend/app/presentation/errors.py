from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.domain.errors import (
    AuthenticationError,
    ConflictError,
    DomainError,
    NotFoundError,
    PasswordMismatchError,
)


def domain_error_handler(_request: Request, error: DomainError) -> JSONResponse:
    statuses = (
        (NotFoundError, 404),
        (ConflictError, 409),
        (AuthenticationError, 401),
        (PasswordMismatchError, 403),
    )
    for error_type, code in statuses:
        if isinstance(error, error_type):
            status = code
            break
    else:
        raise error
    headers = {"WWW-Authenticate": "Bearer"} if status == 401 else None
    return JSONResponse(
        status_code=status, content={"detail": str(error)}, headers=headers
    )


def validation_error_handler(
    _request: Request, error: RequestValidationError
) -> JSONResponse:
    details = [
        {"loc": list(item["loc"]), "msg": item["msg"], "type": item["type"]}
        for item in error.errors()
    ]
    return JSONResponse(status_code=422, content={"detail": details})
