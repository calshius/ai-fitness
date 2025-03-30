import logging
import time
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any

from ..database import get_db
from ..models import QueryRequest, EnhancedQueryResponse
from ..processor import FitnessDataProcessor
from ..llm import analyze_fitness_data
from ..agents.recipe_agent import RecipeAgent
from ..recipe_extractor import extract_food_suggestions

# Set up logging
logger = logging.getLogger("ai_fitness_api.routers.query")

router = APIRouter(
    prefix="/query",
    tags=["query"],
    responses={404: {"description": "Not found"}},
)

# Create a recipe agent instance
recipe_agent = RecipeAgent()

@router.post("/", response_model=EnhancedQueryResponse)
async def query_fitness_data(request: QueryRequest, db: Session = Depends(get_db)):
    """
    Query the fitness data using natural language.
    The system will retrieve relevant information and generate a response.
    If include_recipes is set to true, the response will include food suggestions for meals
    and generate recipes based on those suggestions.
    """
    start_time = time.time()
    logger.info(f"Received query request: '{request.query[:50]}...'")
    logger.info(f"System role: '{request.system_role[:50]}...'")
    logger.info(f"Top_k: {request.top_k}")
    logger.info(f"Model: {request.model}")
    logger.info(f"Include recipes: {request.include_recipes}")

    try:
        # Initialize processor with database session
        logger.info("Initializing FitnessDataProcessor")
        processor = FitnessDataProcessor(db=db)

        # Load documents from database
        logger.info("Loading documents from database")
        processor.load_documents_from_db()

        # If no documents found, try loading from files
        if not processor.documents:
            logger.warning("No documents found in database, loading from files")
            processor.load_data()
            processor.create_documents()

        # Get response from LLM
        logger.info("Getting response from LLM")
        llm_start_time = time.time()
        response = analyze_fitness_data(
            processor,
            request.query,
            system_role=request.system_role,
            top_k=request.top_k,
            model=request.model,
            include_recipes=request.include_recipes
        )
        logger.info(
            f"LLM response received in {time.time() - llm_start_time:.2f} seconds"
        )
        logger.info(f"Response length: {len(response)} characters")

        # Initialize the response object
        result = EnhancedQueryResponse(response=response)

        # If recipes are requested, generate them
        if request.include_recipes:
            logger.info("Generating recipes based on LLM response")
            
            # Extract food suggestions from the LLM response
            food_suggestions = extract_food_suggestions(response)
            
            if any(food_suggestions.values()):
                # Generate recipes for each meal type
                recipes = {}
                
                # Sample macros - in a real app, these would come from user data
                macros = {
                    "breakfast": {"protein": 30, "carbs": 40, "fat": 15, "calories": 400},
                    "lunch": {"protein": 40, "carbs": 50, "fat": 20, "calories": 600},
                    "dinner": {"protein": 45, "carbs": 45, "fat": 25, "calories": 650}
                }
                
                # Generate recipes for each meal type
                for meal_type, food_items in food_suggestions.items():
                    if food_items:
                        recipe = await recipe_agent.generate_meal_plan(
                            macros=macros.get(meal_type, {}),
                            meal_type=meal_type
                        )
                        recipes[meal_type] = recipe
                
                # Add recipes to the response
                result.recipes = recipes
                logger.info(f"Generated {len(recipes)} recipes")
            else:
                logger.warning("No food suggestions found in LLM response")

        total_time = time.time() - start_time
        logger.info(f"Total query processing time: {total_time:.2f} seconds")

        return result

    except Exception as e:
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")
