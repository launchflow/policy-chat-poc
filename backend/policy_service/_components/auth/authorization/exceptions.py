"""Exceptions that are used throughout the backend."""

from buildflow.exceptions import HTTPException


class RoleNotFound(HTTPException):
    """Raised when a role is not found."""

    def __init__(self) -> None:
        super().__init__(404, "role was not found")


class InvalidRole(HTTPException):
    """Raised when a role is invalid."""

    def __init__(self) -> None:
        super().__init__(400, "role is invalid")
