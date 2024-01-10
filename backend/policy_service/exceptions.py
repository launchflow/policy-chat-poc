"""Exceptions that are used throughout the backend."""

from buildflow.exceptions import HTTPException


class AccountNotFound(HTTPException):
    """Raised when an account is not found."""

    def __init__(self) -> None:
        super().__init__(404, "account was not found")


class PolicyNotFound(HTTPException):
    """Raised when a policy is not found."""

    def __init__(self) -> None:
        super().__init__(404, "policy was not found")
