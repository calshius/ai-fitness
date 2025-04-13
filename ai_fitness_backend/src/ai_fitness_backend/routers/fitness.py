import logging
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..agents.fitness_agent import FitnessAgent

logger = logging.getLogger("ai_fitness_api")
router = APIRouter(prefix="/fitness", tags=["fitness"])
fitness_agent = FitnessAgent()


class FitnessRequest(BaseModel):
    """
    Unified request model for fitness data analysis

    This model combines all possible parameters for different types of fitness analysis.
    """

    # Request type
    request_type: str  # "workout_progress", "nutrition_needs", "workout_recommendations", "body_metrics", "general"

    # User identification
    user_id: Optional[str] = None

    # Time period for analysis
    timeframe: Optional[int] = 30  # Default to 30 days

    # Personal metrics for nutrition calculations
    weight: Optional[float] = None  # in kg
    height: Optional[float] = None  # in cm
    age: Optional[int] = None
    gender: Optional[str] = None
    activity_level: Optional[str] = (
        None  # "sedentary", "light", "moderate", "active", "very_active"
    )

    # Fitness goals and equipment
    goal: Optional[str] = None  # "lose_weight", "gain_muscle", "improve_fitness"
    available_equipment: Optional[List[str]] = None

    # For general queries
    query: Optional[str] = None


@router.post("/analyze")
async def analyze_fitness_data(request: FitnessRequest):
    """
    Unified endpoint for all fitness data analysis operations

    This endpoint handles:
    1. Analyzing workout progress
    2. Calculating nutrition needs
    3. Recommending workouts
    4. Analyzing body metrics
    5. General fitness queries

    The operation performed depends on the request_type provided in the request.
    """
    try:
        # Convert request to dictionary for easier handling
        request_data = request.dict()

        # Process the request using the fitness agent
        result = await fitness_agent.process_fitness_request(request_data)

        return result
    except Exception as e:
        logger.error(f"Error analyzing fitness data: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to analyze fitness data: {str(e)}"
        )
