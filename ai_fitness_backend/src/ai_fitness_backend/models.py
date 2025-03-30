import logging
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, validator, Field

# Set up logging
logger = logging.getLogger("ai_fitness_api.models")


class QueryRequest(BaseModel):
    query: str
    system_role: str = "You are a helpful fitness and nutrition assistant."
    top_k: int = 7
    model: str = "mistralai/Mistral-7B-Instruct-v0.2"
    include_recipes: bool = Field(default=False, description="Whether to include food suggestions for recipes")


    @validator("query")
    def query_must_not_be_empty(cls, v):
        if not v.strip():
            logger.warning("Empty query received")
            raise ValueError("Query cannot be empty")
        logger.debug(f"Query validated: {v[:50]}...")
        return v

    @validator("top_k")
    def top_k_must_be_positive(cls, v):
        if v <= 0:
            logger.warning(f"Invalid top_k value received: {v}")
            raise ValueError("top_k must be positive")
        logger.debug(f"top_k validated: {v}")
        return v


class QueryResponse(BaseModel):
    response: str

    def __init__(self, **data):
        super().__init__(**data)
        logger.debug(f"Created QueryResponse with length: {len(self.response)} chars")

class EnhancedQueryResponse(QueryResponse):
    recipes: Optional[Dict[str, Any]] = None
    def __init__(self, **data):
        super().__init__(**data)
        logger.debug(f"Created EnhancedQueryResponse with length: {len(self.response)} chars")

class UploadResponse(BaseModel):
    message: str
    files_processed: List[str]

    def __init__(self, **data):
        super().__init__(**data)
        logger.debug(
            f"Created UploadResponse with {len(data.get('files_processed', []))} files"
        )
