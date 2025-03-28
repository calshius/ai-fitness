import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv

from .database import create_tables
from .routers import router

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("ai_fitness_api.log")],
)
logger = logging.getLogger("ai_fitness_api")

# Load environment variables
load_dotenv()
logger.info("Environment variables loaded")

# Initialize FastAPI app
app = FastAPI(
    title="AI Fitness API",
    description="API for fitness data analysis using AI",
    version="1.0.0",
)
logger.info("FastAPI app initialized")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)
logger.info("CORS middleware added")

# Include routers
app.include_router(router, prefix="/api")
logger.info("Routers included")


# Create database tables on startup
@app.on_event("startup")
async def startup_event():
    logger.info("Application startup: Creating database tables")
    create_tables()
    logger.info("Database tables created successfully")


@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {
        "message": "Welcome to AI Fitness API",
        "docs": "/docs",
        "endpoints": {"query": "/api/query", "upload": "/api/upload"},
    }


if __name__ == "__main__":
    logger.info("Starting uvicorn server")
    uvicorn.run("ai_fitness_backend.main:app", host="0.0.0.0", port=8000, reload=True)
