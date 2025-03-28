import os
import logging
from datetime import datetime
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    DateTime,
    LargeBinary,
    Text,
    ForeignKey,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv

# Set up logging
logger = logging.getLogger("ai_fitness_api.database")

# Load environment variables
load_dotenv()

# Database setup
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost/ai_fitness"
)
logger.info(f"Using database URL: {DATABASE_URL}")

try:
    engine = create_engine(DATABASE_URL)
    logger.info("Database engine created successfully")
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    logger.info("Session maker initialized")
except Exception as e:
    logger.error(f"Error setting up database connection: {str(e)}")
    raise

Base = declarative_base()


# Database models
class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text)
    type = Column(String)
    date = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


class Embedding(Base):
    __tablename__ = "embeddings"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    embedding = Column(LargeBinary)  # Store numpy array as binary
    created_at = Column(DateTime, default=datetime.utcnow)


# Create tables
def create_tables():
    try:
        logger.info("Creating database tables if they don't exist")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")
        raise


# Dependency to get DB session
def get_db():
    logger.debug("Creating new database session")
    db = SessionLocal()
    try:
        yield db
    finally:
        logger.debug("Closing database session")
        db.close()
