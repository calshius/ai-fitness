import os
import shutil
from typing import List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import UploadResponse
from ..processor import FitnessDataProcessor

router = APIRouter(
    prefix="/upload",
    tags=["upload"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=UploadResponse)
async def upload_fitness_data(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    file_type: str = Form(...),  # "mfp" or "garmin"
    db: Session = Depends(get_db)
):
    """
    Upload fitness data files (CSV format).
    
    - file_type: Type of file being uploaded ("mfp" for MyFitnessPal or "garmin" for Garmin data)
    """
    if file_type not in ["mfp", "garmin"]:
        raise HTTPException(status_code=400, detail="Invalid file_type. Must be 'mfp' or 'garmin'")
    
    # Create data directory if it doesn't exist
    data_dir = "data"
    os.makedirs(os.path.join(data_dir, file_type), exist_ok=True)
    
    processed_files = []
    
    try:
        for file in files:
            # Save file to appropriate directory
            file_path = os.path.join(data_dir, file_type, file.filename)
            
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            processed_files.append(file.filename)
        
        # Process data in background to create embeddings
        background_tasks.add_task(process_uploaded_data, db)
        
        return UploadResponse(
            message="Files uploaded successfully. Data processing started in background.",
            files_processed=processed_files
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading files: {str(e)}")

def process_uploaded_data(db: Session):
    """Process uploaded data in background to create documents and embeddings"""
    try:
        processor = FitnessDataProcessor(db=db)
        processor.load_data()
        processor.create_documents()
        processor.create_embeddings()
    except Exception as e:
        print(f"Error processing uploaded data: {str(e)}")
