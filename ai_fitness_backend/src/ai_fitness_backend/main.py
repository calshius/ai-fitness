import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv

from .database import create_tables
from .routers import router

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="AI Fitness API",
    description="API for fitness data analysis using AI",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include routers
app.include_router(router, prefix="/api")

# Create database tables on startup
@app.on_event("startup")
async def startup_event():
    create_tables()

@app.get("/")
async def root():
    return {
        "message": "Welcome to AI Fitness API",
        "docs": "/docs",
        "endpoints": {
            "query": "/api/query",
            "upload": "/api/upload"
        }
    }

if __name__ == "__main__":
    uvicorn.run("ai_fitness_backend.main:app", host="0.0.0.0", port=8000, reload=True)
