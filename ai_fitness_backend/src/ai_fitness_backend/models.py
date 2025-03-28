from typing import List, Optional
from pydantic import BaseModel

class QueryRequest(BaseModel):
    query: str
    system_role: Optional[str] = "You are a helpful fitness and nutrition assistant."
    top_k: int = 5

class QueryResponse(BaseModel):
    response: str

class UploadResponse(BaseModel):
    message: str
    files_processed: List[str]
