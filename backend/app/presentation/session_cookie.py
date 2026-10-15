from fastapi import HTTPException, Request, Response

SESSION_COOKIE = "taskflow_session"
SESSION_PATH = "/api/v1"


def require_browser_request(request: Request) -> None:
    if request.headers.get("X-Requested-With") != "XMLHttpRequest":
        raise HTTPException(
            status_code=403, detail="Origem da solicitação não permitida"
        )


def set_session(
    response: Response, request: Request, token: str, duration: int
) -> None:
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=duration,
        path=SESSION_PATH,
        httponly=True,
        secure=request.url.scheme == "https",
        samesite="strict",
    )
    response.headers["Cache-Control"] = "no-store"


def clear_session(response: Response, request: Request) -> None:
    response.delete_cookie(
        SESSION_COOKIE,
        path=SESSION_PATH,
        httponly=True,
        secure=request.url.scheme == "https",
        samesite="strict",
    )
    response.headers["Cache-Control"] = "no-store"
