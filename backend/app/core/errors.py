import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger("jd_select.errors")


class ErrorDetail(BaseModel):
    loc: list[str | int]
    type: str
    message: str


class ErrorPayload(BaseModel):
    code: str
    message: str
    details: list[ErrorDetail] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    error: ErrorPayload


def error_response(status: int, code: str, message: str, details=None, headers=None):
    return JSONResponse(
        status_code=status,
        content={"error": {"code": code, "message": message, "details": details or []}},
        headers=headers,
    )


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        # Avoid returning Pydantic's input/context, which can contain resume text.
        details = [
            {"loc": list(item["loc"]), "type": item["type"], "message": item["msg"]}
            for item in exc.errors()
        ]
        return error_response(422, "VALIDATION_ERROR", "请求参数不符合要求", details)

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException):
        codes = {404: "NOT_FOUND", 405: "METHOD_NOT_ALLOWED"}
        message = exc.detail if isinstance(exc.detail, str) else "请求失败"
        return error_response(exc.status_code, codes.get(exc.status_code, "HTTP_ERROR"), message, headers=exc.headers)

    @app.exception_handler(SQLAlchemyError)
    async def database_error(request: Request, exc: SQLAlchemyError):
        logger.error("Database request failed: %s", type(exc).__name__)
        return error_response(503, "DATABASE_ERROR", "数据库暂不可用，请稍后重试")

    @app.middleware("http")
    async def handle_unexpected_error(request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as exc:
            # Never log request bodies, database parameters or exception messages.
            logger.error("Unhandled request failure: %s", type(exc).__name__)
            return error_response(500, "INTERNAL_ERROR", "服务内部错误")
