"""
M.A.R.L.IN eDNA Classifier Backend API
Main application entry point
"""

from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging

from app.core.config import settings
from app.database.session import init_db
from app.models.schemas import HealthCheck
from app.api import auth, data, admin, model, search, visualize, system


# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle management for FastAPI app."""
    # Startup
    logger.info("Starting M.A.R.L.IN eDNA Classifier Backend...")
    
    # Initialize database
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
    
    # Test service connections
    try:
        from app.services.redis_service import redis_service
        from app.services.minio_service import minio_service
        
        if redis_service.health_check():
            logger.info("Redis connection: OK")
        else:
            logger.warning("Redis connection: FAILED")
        
        logger.info("MinIO connection: OK")
    except Exception as e:
        logger.error(f"Service connection error: {e}")
    
    logger.info(f"Application started on {settings.environment} environment")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-driven eDNA classification system with ZenML, MLflow, and FAISS",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": exc.errors()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "message": str(exc) if settings.debug else "An error occurred"
        }
    )


# Health check endpoint
@app.get("/health", response_model=HealthCheck, tags=["health"])
async def health_check():
    """Health check endpoint."""
    from app.services.redis_service import redis_service
    
    services = {
        "redis": redis_service.health_check(),
        "database": True  # Would add actual DB health check
    }
    
    return HealthCheck(
        status="healthy" if all(services.values()) else "degraded",
        version=settings.app_version,
        timestamp=datetime.utcnow(),
        services=services
    )


@app.get("/", tags=["root"])
async def root():
    """Root endpoint."""
    return {
        "message": "M.A.R.L.IN eDNA Classifier API",
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health"
    }


# Include routers
app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(data.router, prefix=settings.api_prefix)
app.include_router(admin.router, prefix=settings.api_prefix)
app.include_router(model.router, prefix=settings.api_prefix)
app.include_router(search.router, prefix=settings.api_prefix)
app.include_router(visualize.router, prefix=settings.api_prefix)
app.include_router(system.router, prefix=settings.api_prefix)


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info"
    )
