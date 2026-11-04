import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from collections.abc import Generator

# Load .env file and get database_url
load_dotenv()
DATABASE_URL = os.environ["DATABASE_URL"]

# Create engine
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(
    autoflush=False,
    autocommit=False, # changes will not be saved automatically
    bind=engine, 
)

# Create a base class for SQLAlchemy database models
Base = declarative_base()

# Provide a database session to FastAPI endpoints and close it during cleanup.
def get_db() -> Generator[Session, None, None]:
    """
    Yield a database session and close it during dependency cleanup.

    Used as a FastAPI dependency via Depends(get_db). The session is
    closed even if request handling raises an exception.

    Yields:
        Session: A SQLAlchemy session for database operations.
    """
    db = SessionLocal()  # Create a session.
    try:
        yield db  # Supply the session to the endpoint and pause.
    finally:
        db.close()  # Release session resources during cleanup.