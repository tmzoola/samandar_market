import asyncio
import traceback

from utils import bot


class AppException(Exception):
    def __init__(self, error: str, detail: str, status_code: int = 400):
        self.error = error
        self.detail = detail
        self.status_code = status_code

        # capture the stack at the time of raising the exception
        self.stack_trace = "".join(traceback.format_stack(limit=10))


class BusinessException(AppException):
    def __init__(self, detail: str):
        super().__init__(error="BusinessError", detail=detail, status_code=400)


class NotFoundException(AppException):
    def __init__(self, detail: str):
        super().__init__(error="NotFound", detail=detail, status_code=404)


class ExternalServiceException(AppException):
    def __init__(self, service: str, detail: str):
        super().__init__(error=f"{service}Error", detail=detail, status_code=502)


class CustomValidationException(AppException):
    def __init__(self, detail: str):
        super().__init__(error="ValidationError", detail=detail, status_code=422)
