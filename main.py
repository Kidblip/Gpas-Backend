from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import os
sys.path.append(os.path.dirname(__file__))
from utils.db import database, engine
from utils import models
from Routes.auth import router as auth_router
from Routes.signup import router as signup_router

app = FastAPI(title="Graphical Password Backend", version="1.0.0")

# CORS (allow all for dev; restrict in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup/shutdown
@app.on_event("startup")
async def on_startup():
    models.metadata.create_all(engine)  # 👈 CREATE TABLES
    await database.connect()

@app.on_event("shutdown")
async def on_shutdown():
    await database.disconnect()

# Routers
app.include_router(auth_router)
app.include_router(signup_router)

@app.get("/health")
async def health():
    return {"status": "ok"}
