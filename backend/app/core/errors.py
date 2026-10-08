from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class AppError(Exception):
    """Base domain error. Routers never build error responses by hand."""

    status_code = 400
    default_code = "bad_request"
    default_message = "Bad request"

    def __init__(self, message: str | None = None, *, code: str | None = None) -> None:
        self.message = message or self.default_message
        self.code = code or self.default_code
        super().__init__(self.message)


class UnauthorizedError(AppError):
    status_code = 401
    default_code = "unauthorized"
    default_message = "Authentication required"


class ForbiddenError(AppError):
    status_code = 403
    default_code = "forbidden"
    default_message = "You do not have permission to do that"


class NotFoundError(AppError):
    status_code = 404
    default_code = "not_found"
    default_message = "Resource not found"


class ConflictError(AppError):
    status_code = 409
    default_code = "conflict"
    default_message = "Resource already exists"


class PayloadTooLargeError(AppError):
    status_code = 413
    default_code = "payload_too_large"
    default_message = "File is too large"


class UnsupportedMediaError(AppError):
    status_code = 415
    default_code = "unsupported_media"
    default_message = "Unsupported file type"


def _error_body(code: str, message: str, details: list[dict[str, str]] | None = None) -> dict:
    body: dict = {"code": code, "message": message}
    if details:
        body["details"] = details
    return {"error": body}


async def _handle_app_error(_: Request, exc: AppError) -> JSONResponse:
    headers = {"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else None
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_body(exc.code, exc.message),
        headers=headers,
    )


async def _handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
    details = [
        {"field": ".".join(str(part) for part in err["loc"][1:]), "message": err["msg"]}
        for err in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content=_error_body("validation_error", "Invalid request", details),
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, _handle_app_error)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, _handle_validation_error)  # type: ignore[arg-type]
