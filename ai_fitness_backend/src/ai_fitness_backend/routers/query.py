from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import QueryRequest, QueryResponse
from ..processor import FitnessDataProcessor
from ..llm import analyze_fitness_data

router = APIRouter(
    prefix="/query",
    tags=["query"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=QueryResponse)
async def query_fitness_data(
    request: QueryRequest,
    db: Session = Depends(get_db)
):
    """
    Query the fitness data using natural language.
    The system will retrieve relevant information and generate a response.
    """
    try:
        # Initialize processor with database session
        processor = FitnessDataProcessor(db=db)
        
        # Load documents from database
        processor.load_documents_from_db()
        
        # If no documents found, try loading from files
        if not processor.documents:
            processor.load_data()
            processor.create_documents()
        
        # Get response from LLM
        response = analyze_fitness_data(
            processor, 
            request.query, 
            system_role=request.system_role,
            top_k=request.top_k
        )
        
        return QueryResponse(response=response)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")
