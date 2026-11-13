# test/conftest.py

import os
import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base, get_db
from main import app
from auth import hash_password
from models import Product, User

load_dotenv()  # Load environment variables from .env file

test_engine = create_engine(os.getenv("TEST_DATABASE_URL"))
TestSessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=test_engine
)

@pytest.fixture
def db_session():
    """
    Fixture to provide a SQLAlchemy session for testing.
    It creates all tables before the test and drops them after.
    """
    Base.metadata.create_all(bind=test_engine)
    session = TestSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=test_engine)

@pytest.fixture
def client(db_session):
    """
    Fixture to provide a TestClient for the FastAPI app.
    """
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db  # Override the get_db dependency to use the test database session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()  # Clear overrides after the test

def make_user(db_session, email, role="customer"):
    """
    Helper function to create a user in the test database.
    """
    user = User(
        email=email,
        hashed_password=hash_password("secret123"),
        full_name="Test User",
        role=role,
    )
    db_session.add(user)
    db_session.commit()
    return user

def login(client, email):
    """
    Helper function to log in a user and return the access token.
    """
    resp = client.post(
        "/token",
        data={
            "username": email,
            "password": "secret123"
        }
    )
    return {
        "Authorization": f"Bearer {resp.json()['access_token']}"
    }

@pytest.fixture
def product(db_session):
    """
    Fixture to create a sample product in the test database.
    """
    item = Product(
        name="Keyboard",
        category="electronics",
        price=49.99,
        stock=10,
    )
    db_session.add(item)
    db_session.commit()
    return item

@pytest.fixture
def user_headers(client, db_session):
    """
    Fixture to create a user and return the authorization headers for that user.
    """
    make_user(db_session, "alice@example.com")
    return login(client, "alice@example.com")

@pytest.fixture
def other_user_headers(client, db_session):
    """
    Fixture to create another user and return the authorization headers for that user.
    """
    make_user(db_session, "bob@example.com")
    return login(client, "bob@example.com")

@pytest.fixture
def admin_headers(client, db_session):
    """
    Fixture to create an admin user and return the authorization headers for that user.
    """
    make_user(db_session, "admin@example.com", role="admin")
    return login(client, "admin@example.com")
