import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session

# Load .env file and get database_url
load_dotenv()
DATABASE_URL = os.environ["DATABASE_URL"]

# Create engine
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(
    autoflush=False,
    autocommit=False,
    bind=engine,
)

# Create a base class for SQLAlchemy database models
Base = declarative_base()

# Define get_db() 