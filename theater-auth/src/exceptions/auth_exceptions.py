from exceptions.base import CustomException


class AuthError(CustomException):
    """Базовое исключение для всех ошибок аутентификации."""

    pass


class InvalidCredentialsError(AuthError):
    """Ошибка при некорректных учетных данных."""

    pass


class TokenExpiredError(AuthError):
    """Ошибка истечения срока действия токена."""

    pass


class InvalidTokenError(AuthError):
    """Ошибка недействительного токена."""

    pass


class InvalidSessionError(AuthError):
    """Ошибка недействительной или истекшей сессии."""

    pass


class InvalidAuthenticationScheme(AuthError):
    """Ошибка неправильной аутентификации."""

    pass


class InvalidAlgorithmError(AuthError):
    """Ошибка алгоритма шифрования."""

    pass


class InvalidProviderError(AuthError):
    """Ошибка при несуществующем провайдере."""

    pass
