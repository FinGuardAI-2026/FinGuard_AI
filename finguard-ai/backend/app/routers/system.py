from fastapi import APIRouter
from app.core.config import settings

from app.db.connection import db_manager

router = APIRouter()

@router.get("/", tags=["Root"])
async def root_info():
    """Returns general project description metadata."""
    return {
        "project": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "description": "Intelligent Financial Fraud Detection & Investigation Platform",
        "docs_url": "/docs"
    }

@router.get("/api/v1/health", tags=["Health"])
async def health_check():
    """Performs system liveness probes and database connection verification."""
    db_status = "disconnected"
    status_overall = "healthy"
    
    if db_manager.client is not None:
        try:
            # Quick database ping check
            await db_manager.client.admin.command("ping")
            db_status = "connected"
        except Exception:
            db_status = "disconnected"
            status_overall = "degraded"
    else:
        status_overall = "degraded"

    return {
        "status": status_overall,
        "database": db_status,
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION
    }

@router.get("/api/v1/version", tags=["Version"])
async def version_info():
    """Returns version details matching settings."""
    return {
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "debug_mode": settings.DEBUG
    }
