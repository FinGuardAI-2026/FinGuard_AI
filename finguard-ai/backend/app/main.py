from fastapi import FastAPI
from app.core.config import settings
from app.core.logging.logger import logger
from app.middleware.request_context import setup_middleware
from app.exceptions.handlers import setup_exception_handlers
from app.routers.system import router as system_router
from app.routers.auth import router as auth_router
from app.routers.transaction import router as transaction_router
from app.routers.prediction import router as prediction_router
from app.db.connection import db_manager
from app.routers.analytics import router as analytics_router
from app.routers.reports import router as reports_router

def create_app() -> FastAPI:
    """FastAPI Application Factory constructing configurations, routing, and middlewares."""
    
    # Instantiate app with strict OpenAPI metadata specifications
    app = FastAPI(
        title=settings.APP_NAME,
        description="FinGuard AI is an enterprise-grade financial fraud detection, analysis, and investigation workspace.",
        version=settings.APP_VERSION,
        contact={
            "name": "FinGuard AI Security Incident Team",
            "email": "security-response@finguard.ai",
            "url": "https://finguard.ai/security",
        },
        license_info={
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT",
        },
        openapi_url="/api/v1/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # Register core middlewares
    setup_middleware(app)
    
    # Register centralized exceptions handler filters
    setup_exception_handlers(app)
    
    # Register APIRouters
    app.include_router(system_router)
    app.include_router(auth_router)
    app.include_router(transaction_router)
    app.include_router(prediction_router)
    app.include_router(analytics_router)
    app.include_router(reports_router)
    
    @app.on_event("startup")
    async def startup_event():
        logger.info(
            f"Starting {settings.APP_NAME} under {settings.ENVIRONMENT} mode. Server parameters: Host={settings.HOST}, Port={settings.PORT}"
        )
        try:
            await db_manager.connect_to_database()
        except Exception:
            logger.warning("FastAPI startup warning: Database offline, operating in degraded mode.")
        logger.info("Service interfaces warmups finalized successfully.")

    @app.on_event("shutdown")
    async def shutdown_event():
        logger.info("Stopping services and shutting down connection pools...")
        await db_manager.close_database_connection()
        logger.info("Service shutdown routines completed.")
        
    return app

# Instantiate entry point for ASGI servers (Uvicorn/Gunicorn)
app = create_app()
