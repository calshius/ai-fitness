import logging
import time
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import QueryRequest, QueryResponse
from ..processor import FitnessDataProcessor
from ..llm import analyze_fitness_data

# Set up logging
logger = logging.getLogger("ai_fitness_api.routers.query")

router = APIRouter(
    prefix="/query",
    tags=["query"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", response_model=QueryResponse)
async def query_fitness_data(request: QueryRequest, db: Session = Depends(get_db)):
    """
    Query the fitness data using natural language.
    The system will retrieve relevant information and generate a response.
    """
    start_time = time.time()
    logger.info(f"Received query request: '{request.query[:50]}...'")
    logger.info(f"System role: '{request.system_role[:50]}...'")
    logger.info(f"Top_k: {request.top_k}")
    logger.info(f"Model: {request.model}")

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
        )
        logger.info(
            f"LLM response received in {time.time() - llm_start_time:.2f} seconds"
        )
        logger.info(f"Response length: {len(response)} characters")

        total_time = time.time() - start_time
        logger.info(f"Total query processing time: {total_time:.2f} seconds")

        return QueryResponse(response=response)

    except Exception as e:
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")
