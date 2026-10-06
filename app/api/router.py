from fastapi import APIRouter
from app.api.jobs import router as jobs_router
from app.api.certificates import router as certs_router
from app.api.upload import router as upload_router

api_router = APIRouter()
api_router.include_router(jobs_router)
api_router.include_router(certs_router)
api_router.include_router(upload_router)
