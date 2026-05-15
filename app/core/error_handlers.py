import traceback

from core.config import settings
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from schemas.error import ErrorResponse, ValidationErrorResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from utils import bot

from .exceptions import AppException


# Error handlers for the FastAPI application
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            status_code=exc.status_code, error=exc.error, detail=exc.detail
        ).model_dump(),
    )


# Validation error handler for request validation errors
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = [
        {"field": " -> ".join(str(loc) for loc in err["loc"]), "message": err["msg"]}
        for err in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content=ValidationErrorResponse(
            status_code=422, error="ValidationError", detail=errors
        ).model_dump(),
    )


# HTTP exception handler for Starlette HTTP exceptions
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if settings.APP_MODE == "PRODUCTION":
        if 500 <= exc.status_code <= 599:
            await bot.send_message(
                error_text=f"HTTPException at {request.url}: {exc.detail}",
                error_code=exc.status_code,
            )

    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            status_code=exc.status_code, error=exc.detail, detail="HTTPError"
        ).model_dump(),
    )


# General exception handler for unhandled exceptions
async def unhandled_exception_handler(request: Request, exc: Exception):
    maxLen = 3500
    traceback.print_exc()
    tb = traceback.format_exc()

    # 1-chi qism: qisqartirilgan traceback
    short_tb = tb[:maxLen]

    # 2-chi qism: qolgan (agar bo‘lsa)
    rest_tb = ""
    if len(tb) > maxLen:
        has_rest = True
        rest_tb = tb[maxLen:]
    else:
        has_rest = False

    if settings.APP_MODE == "PRODUCTION":
        # 1️⃣ Birinchi xabar: short traceback
        await bot.send_message(
            error_code=500,
            error_text=f"Unhandled exception at {request.url}\n👤 User: {request.user}\n{short_tb}",
        )

        # 2️⃣ Ikkinchi xabar: qolgan traceback
        if has_rest:
            await bot.send_message(
                error_code=500,
                error_text=f"Remaining traceback:\n{rest_tb}",
            )
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            status_code=500,
            error="Kutilmagan xatolik yuz berdi. Iltimos, keyinroq yana urinib ko‘ring.",
            detail="InternalServerError",
        ).model_dump(),
    )
