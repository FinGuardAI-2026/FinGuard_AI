import time
import uuid
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging.logger import logger

class RequestContextMiddleware(BaseHTTPMiddleware):
    """Intercepts requests to log telemetry, track request IDs, and measure latency."""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # Extract or generate Request ID trace token
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        
        # Attach request_id to request state for access in dependencies
        request.state.request_id = request_id
        
        start_time = time.perf_counter()
        
        # Log request entrance
        logger.info(
            f"Incoming: {request.method} {request.url.path}",
            extra={"request_id": request_id}
        )
        
        try:
            response: Response = await call_next(request)
        except Exception as e:
            # Logs on unhandled bubble issues
            process_time = (time.perf_counter() - start_time) * 1000
            logger.error(
                f"Failed: {request.method} {request.url.path} - Latency: {process_time:.2f}ms",
                extra={"request_id": request_id},
                exc_info=e
            )
            raise e
            
        process_time = (time.perf_counter() - start_time) * 1000
        
        # Append telemetry trace headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time-Ms"] = f"{process_time:.2f}"
        
        # Log request completion status
        logger.info(
            f"Completed: {request.method} {request.url.path} -> Status: {response.status_code} - Latency: {process_time:.2f}ms",
            extra={"request_id": request_id}
        )
        
        return response

from fastapi.middleware.cors import CORSMiddleware
from app.middleware.security import SecurityHeadersMiddleware

def setup_middleware(app: FastAPI) -> None:
    """Registers application-wide middlewares in proper sequence."""
    # CORS policy
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestContextMiddleware)
