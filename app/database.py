"""
Database layer for the Machine Downtime Log application.
Handles SQLite connection and session management.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DB_PATH = os.getenv("DB_PATH", "/data/downtime.db")
# Ensure the directory exists
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# Create database engine
engine = create_engine(
    f"sqlite:///{DB_PATH}",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False  # Set to True for SQL query logging
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()


def create_tables():
    """Create database tables if they don't exist."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info(f"Database tables created/verified at {DB_PATH}")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise


@contextmanager
def get_db_session() -> Session:
    """Context manager for database sessions."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()


def get_db():
    """Dependency for FastAPI to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize the database with tables."""
    create_tables()
    logger.info("Database initialized successfully")