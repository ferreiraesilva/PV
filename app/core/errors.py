from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.core.logging import logger
from app.observability.metrics import ERROR_COUNTER


class ErrorResponse(BaseModel):
    code: str
    message: str
    detail: Any | None = None
    request_id: str | None = None


class AppException(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400, detail: Any | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.detail = detail


def _build_payload(request: Request, *, code: str, message: str, detail: Any | None = None) -> ErrorResponse:
    request_id = getattr(request.state, "request_id", None)
    return ErrorResponse(code=code, message=message, detail=detail, request_id=request_id)


def _log_error(request: Request, *, code: str, message: str, status_code: int, detail: Any | None) -> None:
    logger.bind(component="api", request_id=getattr(request.state, "request_id", None)).error(
        {
            "error_code": code,
            "status_code": status_code,
            "message": message,
            "detail": detail,
            "path": request.url.path,
            "method": request.method,
        }
    )
    ERROR_COUNTER.labels(code=code, endpoint=request.url.path).inc()


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def handle_app_exception(request: Request, exc: AppException) -> JSONResponse:
        _log_error(request, code=exc.code, message=exc.message, status_code=exc.status_code, detail=exc.detail)
        payload = _build_payload(request, code=exc.code, message=exc.message, detail=exc.detail)
        return JSONResponse(status_code=exc.status_code, content=payload.model_dump())

    @app.exception_handler(HTTPException)
    async def handle_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
        code = "http_error"
        message = exc.detail if isinstance(exc.detail, str) else "HTTP error"
        detail = None if isinstance(exc.detail, str) else exc.detail
        _log_error(request, code=code, message=message, status_code=exc.status_code, detail=detail)
        payload = _build_payload(request, code=code, message=message, detail=detail)
        return JSONResponse(status_code=exc.status_code, content=payload.model_dump())

    @app.exception_handler(RequestValidationError)
    async def handle_validation_exception(request: Request, exc: RequestValidationError) -> JSONResponse:
        code = "validation_error"
        message = "Payload validation failed"
        detail = exc.errors()
        _log_error(request, code=code, message=message, status_code=422, detail=detail)
        payload = _build_payload(request, code=code, message=message, detail=detail)
        return JSONResponse(status_code=422, content=payload.model_dump())

    @app.exception_handler(Exception)
    async def handle_unexpected_exception(request: Request, exc: Exception) -> JSONResponse:
        code = "internal_error"
        message = "Unexpected internal error"
        detail = str(exc)
        _log_error(request, code=code, message=message, status_code=500, detail=detail)
        payload = _build_payload(request, code=code, message=message)
        return JSONResponse(status_code=500, content=payload.model_dump())
