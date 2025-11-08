from fastapi import APIRouter, Form, File, UploadFile, HTTPException, status
from typing import List
from sqlalchemy import insert, select, update
import base64, json, sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from utils.db import database
from utils.models import users

router = APIRouter(prefix="/create", tags=["Signup"])

# ------------------------------
# STEP 1: Collect basic user info
# ------------------------------
@router.post("/signup/basic", status_code=status.HTTP_200_OK)
async def signup_basic(firstname: str = Form(...), email: str = Form(...)):
    query = select(users.c.id, users.c.status).where(users.c.email == email)
    existing_user = await database.fetch_one(query)

    if existing_user:
        # User exists
        if existing_user["status"] == "active":
            raise HTTPException(status_code=409, detail="User already completed signup")
        # User exists but pending → allow to continue
        await database.execute(
            update(users).where(users.c.email == email).values(firstname=firstname)
        )
        return {"message": "Basic info updated, status: pending"}

    # New user → insert with status pending
    new_user = {
        "firstname": firstname,
        "email": email,
        "user_images": None,
        "graphical_password": None,
        "status": "pending"
    }
    await database.execute(insert(users).values(**new_user))
    return {"message": "Basic info saved, status: pending"}


# ------------------------------
# STEP 2: Upload images
# ------------------------------
@router.post("/signup/images", status_code=status.HTTP_200_OK)
async def signup_images(email: str = Form(...), images: List[UploadFile] = File(...)):
    if not images:
        raise HTTPException(status_code=400, detail="No images provided")
    if len(images) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 images allowed")

    image_data = []
    max_size = 5 * 1024 * 1024  # 5MB
    for image in images:
        contents = await image.read()
        if not image.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail=f"Invalid file type: {image.filename}")
        if len(contents) > max_size:
            raise HTTPException(status_code=400, detail=f"File too large: {image.filename}")

        encoded = base64.b64encode(contents).decode("utf-8")
        image_data.append({
            "filename": image.filename,
            "content_type": image.content_type,
            "data": encoded,
            "size": len(contents),
        })

    # Check user
    user_query = select(users.c.firstname, users.c.graphical_password, users.c.status).where(users.c.email == email)
    user = await database.fetch_one(user_query)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user["status"] == "active":
        raise HTTPException(status_code=400, detail="User already completed signup")

    # Update images and determine status
    status_value = "active" if user["firstname"] and user["graphical_password"] else "pending"
    await database.execute(
        update(users).where(users.c.email == email).values(
            user_images=json.dumps(image_data),
            status=status_value
        )
    )

    return {"message": f"{len(images)} images uploaded", "status": status_value}


# ------------------------------
# STEP 3: Finalize signup with graphical password
# ------------------------------
@router.post("/signup/finalize", status_code=status.HTTP_201_CREATED)
async def signup_finalize(email: str = Form(...), password_sequence: str = Form(...)):
    # Validate password sequence format
    try:
        sequence = json.loads(password_sequence)
        if not isinstance(sequence, list) or len(sequence) == 0:
            raise ValueError
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid password sequence format")

    # Check user
    user_query = select(users.c.firstname, users.c.user_images, users.c.status).where(users.c.email == email)
    user = await database.fetch_one(user_query)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user["status"] == "active":
        raise HTTPException(status_code=400, detail="User already completed signup")

    # Update graphical password and potentially activate user
    status_value = "active" if user["firstname"] and user["user_images"] else "pending"
    await database.execute(
        update(users).where(users.c.email == email).values(
            graphical_password=json.dumps(sequence),
            status=status_value
        )
    )

    return {"message": "Signup complete", "status": status_value}
