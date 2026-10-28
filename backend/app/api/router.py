from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.distributors import router as distributors_router
from app.api.v1.batches import router as batches_router
from app.api.v1.ingestion import router as ingestion_router
from app.api.v1.returns import router as returns_router
from app.api.v1.credit_notes import router as credit_notes_router
from app.api.v1.dashboard import router as dashboard_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(distributors_router)
api_router.include_router(batches_router)
api_router.include_router(ingestion_router)
api_router.include_router(returns_router)
api_router.include_router(credit_notes_router)
api_router.include_router(dashboard_router)
