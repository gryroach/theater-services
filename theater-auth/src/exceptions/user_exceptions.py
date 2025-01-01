from exceptions.base import CustomException


class UserError(CustomException):
    """Базовое исключение для всех ошибок, связанных с пользователями."""

    pass


class UserAlreadyExistsError(UserError):
    """Ошибка, если пользователь уже существует"""

    pass


class UserDoesNotExistsError(UserError):
    """Ошибка, если пользователь не существует."""

    pass
