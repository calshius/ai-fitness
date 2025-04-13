from fastapi import APIRouter
from .query import router as query_router
from .upload import router as upload_router
from .scraper import router as scraper_router

router = APIRouter()
router.include_router(query_router)
router.include_router(upload_router)
router.include_router(scraper_router)
