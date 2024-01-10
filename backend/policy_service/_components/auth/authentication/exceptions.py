"""Exceptions that are used throughout the backend."""

from buildflow.exceptions import HTTPException


class RefreshTokenNotFound(HTTPException):
    """Raised when a refresh token is not found."""

    def __init__(self) -> None:
        super().__init__(404, "refresh token was not found")


class UserNotFound(HTTPException):
    """Raised when a user is not found."""

    def __init__(self) -> None:
        super().__init__(404, "user was not found")


class ExpiredTokenError(HTTPException):
    """Raised when a token has expired."""

    def __init__(self) -> None:
        super().__init__(401, "token has expired")
