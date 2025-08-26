from typing import Optional
from src.utils.logger import get_logger

logger = get_logger()


class CustomBaseException(Exception):
    """Base class for all custom exceptions with logging."""

    def __init__(
        self,
        message: str,
        code: int = 500,
        excep: Optional[Exception] = None,
        notify: bool = False,
    ):
        super().__init__(f"[Error {code}] {message}")
        self.message = message
        self.code = code
        self.excep = excep
        self.log()
        if notify:
            self.notify()

    def log(self):
        """Internal logging for exceptions."""
        logger.error(
            f"{self.__class__.__name__} - Code: {self.code}, Message: {self.message}",
            exc_info=exec,
        )

    def notify(self):
        pass


class ClientException(CustomBaseException):
    """For errors caused by invalid client requests (4xx errors)."""

    def __init__(
        self, message: str, code: int = 400, excep: Optional[Exception] = None
    ):
        super().__init__(message, code, excep)

    def log(self):
        """Internal logging for exceptions."""
        logger.info(
            f"{self.__class__.__name__} - Code: {self.code}, Message: {self.message}"
        )


class ServerException(CustomBaseException):
    """For internal server errors (5xx errors)."""

    def __init__(
        self, message: str, code: int = 500, excep: Optional[Exception] = None
    ):
        super().__init__(message, code, excep)


class FatalException(CustomBaseException):
    """For unrecoverable, critical failures."""

    def __init__(
        self, message: str, code: int = 500, excep: Optional[Exception] = None
    ):
        super().__init__(message, code, excep, notify=True)

    def log(self):
        logger.critical(
            f"{self.__class__.__name__} - Code: {self.code}, Message: {self.message}",
            exc_info=exec,
        )
