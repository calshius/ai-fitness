import logging
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..agents.recipe_agent import RecipeAgent

logger = logging.getLogger("ai_fitness_api")
router = APIRouter(prefix="/recipe", tags=["recipe"])
recipe_agent = RecipeAgent()


class RecipeRequest(BaseModel):
    """
    Unified request model for recipe-related operations

    This model combines all possible parameters for recipe generation,
    ingredient search, and food suggestions.
    """

    # Macro requirements
    protein: Optional[float] = None
    carbs: Optional[float] = None
    fat: Optional[float] = None
    calories: Optional[float] = None

    # Meal information
    meal_type: Optional[str] = None

    # Food items (for ingredient search or recipe generation)
    food_items: Optional[List[str]] = None

    # Supermarket preference
    supermarket: Optional[str] = None


@router.post("/process")
async def process_recipe_request(request: RecipeRequest):
    """
    Unified endpoint for all recipe-related operations

    This endpoint handles:
    1. Generating meal plans based on macro requirements
    2. Getting ingredients for specific food items
    3. Getting food suggestions based on macro requirements

    The operation performed depends on the parameters provided in the request.
    """
    try:
        # Convert request to dictionary for easier handling
        request_data = request.dict()

        # Process the request using the recipe agent
        result = await recipe_agent.process_recipe_request(request_data)

        return result
    except Exception as e:
        logger.error(f"Error processing recipe request: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to process recipe request: {str(e)}"
        )
