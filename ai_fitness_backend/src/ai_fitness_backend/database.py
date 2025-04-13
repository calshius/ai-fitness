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
from sqlalchemy.orm import sessionmaker, Session, relationship
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
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        String, unique=True, index=True
    )  # External user identifier (e.g., "Callum")
    name = Column(String)
    email = Column(String, unique=True, index=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship to documents
    documents = relationship("Document", back_populates="user")


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text)
    type = Column(String)
    date = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"))  # Foreign key to users table

    # Relationship to user
    user = relationship("User", back_populates="documents")


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


# Function to create default user if it doesn't exist
def create_default_user(db: Session):
    try:
        # Check if default user exists
        default_user = db.query(User).filter(User.user_id == "Callum").first()

        if not default_user:
            logger.info("Creating default user 'Callum'")
            default_user = User(
                user_id="Callum", name="Callum", email="callum@example.com"
            )
            db.add(default_user)
            db.commit()
            logger.info("Default user created successfully")
        else:
            logger.info("Default user 'Callum' already exists")

        return default_user
    except Exception as e:
        logger.error(f"Error creating default user: {str(e)}")
        db.rollback()
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
