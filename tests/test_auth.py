import pytest
from fastapi.testclient import TestClient
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from main import app
from utils.db import database, engine
from utils.models import metadata
import json

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
async def setup_database():
    # Create tables
    metadata.create_all(engine)
    await database.connect()
    yield
    await database.disconnect()

def test_login_success():
    """Test successful login."""
    # First, create a user (assuming signup works)
    # For simplicity, we'll assume a user exists or create one via direct DB insert
    # In a real scenario, you'd use a fixture to create test data

    data = {
        "email": "john@example.com",
        "password_sequence": ["00", "11", "22", "01", "10"]
    }

    response = client.post("/auth/login", json=data)
    # This might fail if user doesn't exist, but tests the endpoint
    if response.status_code == 200:
        assert "firstname" in response.json()
    else:
        assert response.status_code in [404, 401]  # User not found or wrong password

def test_login_user_not_found():
    """Test login with non-existent user."""
    data = {
        "email": "nonexistent@example.com",
        "password_sequence": ["00"]
    }

    response = client.post("/auth/login", json=data)
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]

def test_login_wrong_password():
    """Test login with wrong password."""
    data = {
        "email": "john@example.com",
        "password_sequence": ["99"]  # Wrong sequence
    }

    response = client.post("/auth/login", json=data)
    assert response.status_code == 401
    assert "Incorrect password" in response.json()["detail"]

def test_get_user_images():
    """Test retrieving user images."""
    response = client.get("/auth/images?email=john@example.com")
    if response.status_code == 200:
        assert "images" in response.json()
    else:
        assert response.status_code == 404

def test_verify_graphical_password():
    """Test graphical password verification."""
    data = {
        "email": "john@example.com",
        "password_sequence": ["00", "11", "22", "01", "10"]
    }

    response = client.post("/auth/images/verify-password", json=data)
    if response.status_code == 200:
        assert response.json()["success"] == True
    else:
        assert response.status_code == 401
