import pytest
from fastapi.testclient import TestClient
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from main import app
from utils.db import database, engine
from utils.models import metadata
import json
import base64
from io import BytesIO
from PIL import Image

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
async def setup_database():
    # Create tables
    metadata.create_all(engine)
    await database.connect()
    yield
    await database.disconnect()
    # Optionally drop tables after tests

def create_test_image():
    """Create a small test image."""
    img = Image.new('RGB', (100, 100), color='red')
    buffer = BytesIO()
    img.save(buffer, format='JPEG')
    buffer.seek(0)
    return buffer.getvalue()

def test_signup_success():
    """Test successful user signup."""
    test_image = create_test_image()

    files = {"images": ("test.jpg", test_image, "image/jpeg")}
    data = {
        "firstname": "John",
        "email": "john@example.com",
        "password_sequence": json.dumps([
            {"image_index": 0, "grid": ["00"]},
            {"image_index": 0, "grid": ["11"]},
            {"image_index": 0, "grid": ["22"]},
            {"image_index": 0, "grid": ["01"]},
            {"image_index": 0, "grid": ["10"]}
        ])
    }

    response = client.post("/create/signup", files=files, data=data)
    assert response.status_code == 201
    assert response.json() == {"message": "Signup successful"}

def test_signup_duplicate_email():
    """Test signup with existing email."""
    test_image = create_test_image()

    files = {"images": ("test.jpg", test_image, "image/jpeg")}
    data = {
        "firstname": "Jane",
        "email": "john@example.com",  # Same email as previous test
        "password_sequence": json.dumps([
            {"image_index": 0, "grid": ["00"]}
        ])
    }

    response = client.post("/create/signup", files=files, data=data)
    assert response.status_code == 409
    assert "User already exists" in response.json()["detail"]

def test_signup_invalid_email():
    """Test signup with invalid data."""
    data = {
        "firstname": "Test",
        "email": "",  # Empty email
        "password_sequence": json.dumps([]),
        "images": []
    }

    response = client.post("/create/signup", data=data)
    assert response.status_code == 400

def test_signup_missing_images():
    """Test signup without images."""
    data = {
        "firstname": "Test",
        "email": "test@example.com",
        "password_sequence": json.dumps([{"image_index": 0, "grid": ["00"]}]),
        "images": []
    }

    response = client.post("/create/signup", data=data)
    assert response.status_code == 400
    assert "No images provided" in response.json()["detail"]
