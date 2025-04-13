from fastapi import APIRouter
from .upload import router as upload_router
from .scraper import router as scraper_router
from .recipe import router as recipe_router
from .fitness import router as fitness_router

router = APIRouter()
router.include_router(upload_router)
router.include_router(scraper_router)
router.include_router(recipe_router)
router.include_router(fitness_router)
