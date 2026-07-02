import sys
from datetime import datetime
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.core.logging.logger import logger

def setup_exception_handlers(app: FastAPI) -> None:
    """Registers standard handlers to intercept validation, HTTP, and runtime errors."""

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        """Translates Pydantic Validation errors into a clean standardized response."""
        logger.warning(
            f"Validation failure: {request.method} {request.url.path}",
            extra={"extra_info": {"errors": exc.errors()}}
        )
        
        # Flatten structure for visual consumer readability
        details = [
            {
                "field": " -> ".join(map(str, error.get("loc", []))),
                "issue": error.get("msg"),
                "type": error.get("type")
            }
            for error in exc.errors()
        ]
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Input validation failed. See fields details.",
                    "details": details,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            }
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        """Translates standard HTTP Exceptions into standardized JSON."""
        logger.warning(
            f"HTTP Exception {exc.status_code}: {request.method} {request.url.path} - {exc.detail}"
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": f"HTTP_EXCEPTION_{exc.status_code}",
                    "message": exc.detail,
                    "details": [],
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            }
        )

    @app.exception_handler(Exception)
    async def unexpected_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Captures untyped code bugs, preventing server error leak configurations."""
        logger.error(
            f"Unhandled system error: {request.method} {request.url.path} - {str(exc)}",
            exc_info=exc
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred. Please contact the security desk.",
                    "details": [],
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            }
        )
