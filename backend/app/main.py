from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on startup if using SQLite or fresh db
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="ExpiryOS API",
    description="Multi-tenant SaaS for retail pharmacies to manage near-expiry stock, automate return workflows, and track distributor credit reconciliation.",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for local dev / preview
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["System Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": "ExpiryOS Core API",
        "version": "1.0.0",
    }


@app.get("/", tags=["System Health"])
async def root():
    return {
        "message": "Welcome to ExpiryOS — Pharmacy Near-Expiry Stock & Return Automation SaaS",
        "docs": f"{settings.API_V1_STR}/docs",
        "health": "/health",
    }


# Include all v1 API routes
app.include_router(api_router, prefix=settings.API_V1_STR)
