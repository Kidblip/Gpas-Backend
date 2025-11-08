from fastapi import APIRouter, Form, HTTPException, status, Body, Query
from sqlalchemy import select
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from utils.db import database
from utils.models import users

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login")
async def login(data: dict = Body(...)):
    """
    Authenticate a user with email + graphical password (sequence).
    """
    email = data.get("email")
    password_sequence = data.get("password_sequence")

    if not email or not password_sequence:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email and password sequence required"
        )

    query = select(
        users.c.id, users.c.firstname, users.c.email, users.c.graphical_password
    ).where(users.c.email == email)
    row = await database.fetch_one(query)

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    try:
        stored_sequence = json.loads(row["graphical_password"])
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Stored password format invalid")

    if stored_sequence != password_sequence:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password"
        )

    return {"firstname": row["firstname"]}


@router.get("/images")
async def get_user_images(
    email: str = Query(..., description="User email to fetch images for")
):
    """Retrieve stored images JSON for a user by email."""
    query = select(users.c.user_images).where(users.c.email == email)
    row = await database.fetch_one(query)

    if not row:
        raise HTTPException(status_code=404, detail="User not found")

    data = row["user_images"]
    if not data:
        raise HTTPException(status_code=404, detail="No images found for this user")

    try:
        images = json.loads(data)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Invalid image data format")

    return {"images": images}


@router.post("/images/verify-password")
async def verify_graphical_password(
    email: str = Body(..., embed=True),
    password_sequence: list = Body(..., embed=True),
):
    """Verify graphical password for a user."""
    query = select(users.c.graphical_password).where(users.c.email == email)
    row = await database.fetch_one(query)

    if not row or not row["graphical_password"]:
        raise HTTPException(status_code=404, detail="User not found or no password set")

    try:
        stored_sequence = json.loads(row["graphical_password"])
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Stored password format invalid")

    # Simple match check (you can later enhance with tolerance rules, etc.)
    if stored_sequence == password_sequence:
        return {"success": True, "message": "Login successful"}
    else:
        raise HTTPException(status_code=401, detail="Invalid graphical password")
