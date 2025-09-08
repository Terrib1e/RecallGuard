"""Database configuration and setup."""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

__all__ = ["engine", "SessionLocal", "Base", "get_db"]

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Use PostgreSQL by default, fallback to SQLite for demo
if not DATABASE_URL:
    # Try to detect if PostgreSQL is available
    try:
        import psycopg2
        DATABASE_URL = "postgresql://username:password@localhost:5432/recallguard"
        print("Using PostgreSQL database (update DATABASE_URL in .env for custom connection)")
    except ImportError:
        DATABASE_URL = "sqlite:///./recallguard.db"
        print("PostgreSQL not available, using SQLite database")

# Create SQLAlchemy engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class
Base = declarative_base()


def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()