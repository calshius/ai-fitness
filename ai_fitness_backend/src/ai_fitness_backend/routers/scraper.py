import logging
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any

from ..scrapers.tesco_scraper import TescoScraper
from ..scrapers.morrisons_scraper import MorrisonsScraper
from ..scrapers.sainsburys_scraper import SainsburysScraper
from ..scrapers.marks_and_spencer_scraper import MarksAndSpencerScraper
from ..models import ScraperRequest, ScraperResponse

# Set up logging
logger = logging.getLogger("ai_fitness_api.routers.scraper")

router = APIRouter(
    prefix="/scraper",
    tags=["scraper"],
    responses={404: {"description": "Not found"}},
)


@router.post("/tesco", response_model=ScraperResponse)
async def search_tesco(request: ScraperRequest):
    """
    Search for a food item on Tesco's website and return basic information.

    - **product_name**: Name of the food item to search for
    """
    logger.info(f"Received Tesco search request for: '{request.product_name}'")

    try:
        # Initialize the Tesco scraper
        scraper = TescoScraper()

        # Search for the product
        results = await scraper.search_product(request.product_name)

        logger.info(f"Found {len(results)} results for '{request.product_name}'")

        return ScraperResponse(
            message=f"Successfully searched for '{request.product_name}'",
            results=results,
        )

    except Exception as e:
        logger.error(f"Error searching Tesco: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error searching Tesco: {str(e)}")


@router.post("/morisons", response_model=ScraperResponse)
async def search_morisons(request: ScraperRequest):
    """
    Search for a food item on Morrisons website and return basic information.

    - **product_name**: Name of the food item to search for
    """
    logger.info(f"Received Morrisons search request for: '{request.product_name}'")

    try:
        # Initialize the Morrisons scraper
        scraper = MorrisonsScraper()

        # Search for the product
        results = await scraper.search_product(request.product_name)

        logger.info(f"Found {len(results)} results for '{request.product_name}'")

        return ScraperResponse(
            message=f"Successfully searched for '{request.product_name}'",
            results=results,
        )

    except Exception as e:
        logger.error(f"Error searching Morrisons: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error searching Tesco: {str(e)}")


@router.post("/sainsburys", response_model=ScraperResponse)
async def search_sainsburys(request: ScraperRequest):
    """
    Search for a food item on Sainsburys website and return basic information.

    - **product_name**: Name of the food item to search for
    """
    logger.info(f"Received Sainsburys search request for: '{request.product_name}'")

    try:
        # Initialize the Sainsburys scraper
        scraper = SainsburysScraper()

        # Search for the product
        results = await scraper.search_product(request.product_name)

        logger.info(f"Found {len(results)} results for '{request.product_name}'")

        return ScraperResponse(
            message=f"Successfully searched for '{request.product_name}'",
            results=results,
        )

    except Exception as e:
        logger.error(f"Error searching Sainsburys: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error searching Tesco: {str(e)}")


@router.post("/mns", response_model=ScraperResponse)
async def search_mns(request: ScraperRequest):
    """
    Search for a food item on MarksAndSpencer website and return basic information.

    - **product_name**: Name of the food item to search for
    """
    logger.info(
        f"Received MarksAndSpencers search request for: '{request.product_name}'"
    )

    try:
        # Initialize the MarksAndSpencer scraper
        scraper = MarksAndSpencerScraper()

        # Search for the product
        results = await scraper.search_product(request.product_name)

        logger.info(f"Found {len(results)} results for '{request.product_name}'")

        return ScraperResponse(
            message=f"Successfully searched for '{request.product_name}'",
            results=results,
        )

    except Exception as e:
        logger.error(f"Error searching MarksAndSpencer: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error searching Tesco: {str(e)}")
