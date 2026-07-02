from fastapi import Request

async def get_request_id(request: Request) -> str:
    """Retrieves the request ID attached by the request context middleware."""
    return getattr(request.state, "request_id", "unknown-request-id")
