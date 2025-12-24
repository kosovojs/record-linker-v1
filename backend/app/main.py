"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import api_router
from app.config import get_settings
from app.services.exceptions import (
    ConflictError,
    InvalidStateTransitionError,
    NotFoundError,
    ServiceError,
    ValidationError,
)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown events."""
    # Startup
    # Note: In production, use Alembic migrations instead of init_db
    # from app.database import init_db
    # await init_db()
    yield
    # Shutdown
    # Add cleanup logic here if needed


app = FastAPI(
    title=settings.app_name,
    description="A data reconciliation system for matching external data sources to Wikidata entities",
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS middleware - configurable via settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handlers for service layer exceptions
@app.exception_handler(NotFoundError)
async def not_found_exception_handler(request: Request, exc: NotFoundError):
    """Convert NotFoundError to 404 response."""
    return JSONResponse(status_code=404, content={"detail": exc.message})


@app.exception_handler(ConflictError)
async def conflict_exception_handler(request: Request, exc: ConflictError):
    """Convert ConflictError to 409 response."""
    return JSONResponse(status_code=409, content={"detail": exc.message})


@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """Convert ValidationError to 400 response."""
    return JSONResponse(status_code=400, content={"detail": exc.message})


@app.exception_handler(ServiceError)
async def service_exception_handler(request: Request, exc: ServiceError):
    """Convert generic ServiceError to 500 response."""
    return JSONResponse(status_code=500, content={"detail": exc.message})


@app.exception_handler(InvalidStateTransitionError)
async def invalid_state_exception_handler(request: Request, exc: InvalidStateTransitionError):
    """Convert InvalidStateTransitionError to 409 response."""
    return JSONResponse(status_code=409, content={"detail": exc.message})


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "app": settings.app_name}


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "api": settings.api_v1_prefix,
    }


# Include API v1 router
app.include_router(api_router, prefix=settings.api_v1_prefix)
