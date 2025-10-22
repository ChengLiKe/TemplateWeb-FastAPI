# app/models/errors.py
from enum import Enum


class ErrorCode(Enum):
    E_NOT_FOUND = "E_NOT_FOUND"
    E_VALIDATION = "E_VALIDATION"
    E_AUTH_FAILED = "E_AUTH_FAILED"
    E_FORBIDDEN = "E_FORBIDDEN"
    E_SERVER_ERROR = "E_SERVER_ERROR"
    E_BAD_REQUEST = "E_BAD_REQUEST"

    @classmethod
    def from_status(cls, status_code: int) -> "ErrorCode":
        if status_code == 400:
            return cls.E_BAD_REQUEST
        if status_code == 401:
            return cls.E_AUTH_FAILED
        if status_code == 403:
            return cls.E_FORBIDDEN
        if status_code == 404:
            return cls.E_NOT_FOUND
        if 500 <= status_code <= 599:
            return cls.E_SERVER_ERROR
        return cls.E_BAD_REQUEST