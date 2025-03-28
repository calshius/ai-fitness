import os
import shutil
import logging
import time
from typing import List
from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Form,
    HTTPException,
    Depends,
    BackgroundTasks,
)
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import UploadResponse
from ..processor import FitnessDataProcessor

# Set up logging
logger = logging.getLogger("ai_fitness_api.routers.upload")

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
    db: Session = Depends(get_db),
):
    """
    Upload fitness data files (CSV format).

    - file_type: Type of file being uploaded ("mfp" for MyFitnessPal or "garmin" for Garmin data)
    """
    start_time = time.time()
    logger.info(f"Received upload request for {len(files)} files of type '{file_type}'")

    if file_type not in ["mfp", "garmin"]:
        logger.warning(f"Invalid file_type: {file_type}")
        raise HTTPException(
            status_code=400, detail="Invalid file_type. Must be 'mfp' or 'garmin'"
        )

    # Create data directory if it doesn't exist
    data_dir = "data"
    try:
        os.makedirs(os.path.join(data_dir, file_type), exist_ok=True)
        logger.info(f"Created/verified directory: {os.path.join(data_dir, file_type)}")
    except Exception as e:
        logger.error(f"Error creating directory: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error creating directory: {str(e)}"
        )

    processed_files = []

    try:
        for file in files:
            # Save file to appropriate directory
            file_path = os.path.join(data_dir, file_type, file.filename)
            logger.info(f"Saving file to {file_path}")

            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            processed_files.append(file.filename)
            logger.info(f"Successfully saved file: {file.filename}")

        # Process data in background to create embeddings
        logger.info("Adding background task to process uploaded data")
        background_tasks.add_task(process_uploaded_data, db)

        total_time = time.time() - start_time
        logger.info(
            f"Upload completed in {total_time:.2f} seconds. Processed {len(processed_files)} files."
        )

        return UploadResponse(
            message="Files uploaded successfully. Data processing started in background.",
            files_processed=processed_files,
        )

    except Exception as e:
        logger.error(f"Error uploading files: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error uploading files: {str(e)}")


def process_uploaded_data(db: Session):
    """Process uploaded data in background to create documents and embeddings"""
    logger.info("Starting background processing of uploaded data")
    start_time = time.time()

    try:
        logger.info("Initializing FitnessDataProcessor")
        processor = FitnessDataProcessor(db=db)

        logger.info("Loading data from files")
        processor.load_data()

        logger.info("Creating documents")
        processor.create_documents()

        logger.info("Creating embeddings")
        processor.create_embeddings()

        total_time = time.time() - start_time
        logger.info(f"Background processing completed in {total_time:.2f} seconds")
    except Exception as e:
        logger.error(f"Error processing uploaded data: {str(e)}", exc_info=True)
