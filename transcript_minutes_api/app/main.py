from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.modules.database import create_tables
from app.routers import auth, minutes, users
from app.modules.logger import get_logger
import os
from dotenv import load_dotenv

load_dotenv()

logger = get_logger(__name__)

app = FastAPI(
    title="Transcript to Meeting Minutes API",
    description="API for generating meeting minutes from transcripts using OpenAI",
    version="1.0.0"
)

# Disable CORS. Do not remove this for full-stack development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

app.include_router(auth.router)
app.include_router(minutes.router)
app.include_router(users.router)

@app.on_event("startup")
async def startup_event():
    logger.info("Starting up the application")
    create_tables()
    logger.info("Database tables created successfully")

@app.get("/healthz")
async def healthz():
    return {"status": "ok", "message": "Transcript to Meeting Minutes API is running"}

@app.get("/")
async def root():
    return {
        "message": "Welcome to Transcript to Meeting Minutes API",
        "docs": "/docs",
        "health": "/healthz"
    }
