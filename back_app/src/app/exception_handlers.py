import traceback
from typing import Optional, List, Union

from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from starlette import status
from starlette.responses import JSONResponse

from src.services.telegram_service import send_alert


class ErrorInfoModel:
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message

    def __repr__(self):
        return f"code:{self.code},message:{self.message}"


class ErrorInfoContainer:
    unhandled_error = ErrorInfoModel(code=1, message="Internal server error")
    model_validation_error = ErrorInfoModel(code=3, message="Model validation error")
    not_found_error = ErrorInfoModel(code=4, message="Not found")
    incorrect_username_password = ErrorInfoModel(code=8, message="Incorrect username or password")
    token_expired = ErrorInfoModel(
        code=9,
        message="token_expired set Authorization in the header " "with value 'Bearer valid_token' ",
    )
    invalid_token = ErrorInfoModel(
        code=10,
        message="Invalid token set Authorization in the header with" " value 'Bearer valid_token' ",
    )
    error_code_not_found = ErrorInfoModel(code=202, message="Error code not found.")


class ErrorResponseModel(BaseModel):
    error_code: int = None
    error_message: str = None
    error_detail: list | None = None


class ErrorCodeResponse(Exception):
    def __init__(self, error: ErrorInfoContainer, status_code=400, dev_details=None):
        self.error = error
        self.status = status_code
        self.dev_details = dev_details

    def __str__(self):
        return f"error_code:{self.error} status:{self.status} dev_details:{self.dev_details}"

    def __repr__(self):
        return f"error_code:{self.error} status:{self.status} dev_details:{self.dev_details}"


class ExceptionHandlers:
    @staticmethod
    async def unhandled_exception(request, exc: Exception):  # noqa
        send_alert(str(exc))
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ExceptionHandlers.__get_error_content(
                error_info=ErrorInfoContainer.unhandled_error,
                # error_detail=[ExceptionHandlers.__get_stack_trace(exc)] if ReturnTraceback else [],
                error_detail=[],
            ),
        )

    @staticmethod
    def http_exception(request, exc: HTTPException):  # noqa
        status_code_responses = {
            404: ErrorInfoContainer.not_found_error,
            401: ErrorInfoContainer.invalid_token,
        }
        return JSONResponse(
            status_code=exc.status_code,
            content=ExceptionHandlers.__get_error_content(
                error_info=status_code_responses.get(exc.status_code, ErrorInfoContainer.unhandled_error),
                error_detail=[exc.detail],
            ),
        )

    @staticmethod
    def validation_exception(request, exc):  # noqa
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ExceptionHandlers.__get_error_content(
                error_info=ErrorInfoContainer.model_validation_error,
                error_detail=exc.errors(),
            ),
        )

    @staticmethod
    def error_code_response(request, exc: ErrorCodeResponse):  # noqa
        return JSONResponse(
            status_code=exc.status,
            content=ExceptionHandlers.__get_error_content(error_info=exc.error, error_detail=None),
        )

    @staticmethod
    def __get_error_content(
        error_info: Union[ErrorInfoModel, ErrorInfoContainer],
        error_detail: Optional[List] = None,
    ):
        return jsonable_encoder(
            ErrorResponseModel(
                error_code=error_info.code,
                error_message=error_info.message,
                error_detail=error_detail,
            ).dict()
        )

    @staticmethod
    def __get_stack_trace(exc: Exception) -> str:
        return "".join(traceback.TracebackException.from_exception(exc).format())
