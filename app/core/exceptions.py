class AppError(Exception):
    status_code: int = 500
    code: str = "internal_error"
    message: str = "Something went wrong"

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.message
        super().__init__(self.message)


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"
    message = "Resource not found"


class UnauthorizedError(AppError):
    status_code = 401
    code = "unauthorized"
    message = "Invalid credentials"


class ConflictError(AppError):
    status_code = 409
    code = "conflict"
    message = "Resource already exists"


class ForbiddenError(AppError):
    status_code = 403
    code = "forbidden"
    message = "You do not have access"


class InvalidCredentials(UnauthorizedError):
    code = "invalid_credentials"
    message = "Invalid email or password"
