from fastapi import Request
from sqlalchemy import exc as sqlalchemy_exc
from starlette import status
from starlette.responses import JSONResponse

from exceptions.auth_exceptions import AuthError
from exceptions.user_exceptions import UserError


async def auth_exception_handler(_: Request, exc: AuthError):
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": str(exc)},
    )


async def user_exception_handler(_: Request, exc: UserError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)},
    )


async def integrity_error_handler(_: Request, __: Exception):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": "Record already exists"},
    )


exception_handlers = {
    sqlalchemy_exc.IntegrityError: integrity_error_handler,
    UserError: user_exception_handler,
    AuthError: auth_exception_handler,
}
