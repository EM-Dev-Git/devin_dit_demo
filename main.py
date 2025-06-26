from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

from modules.database import create_tables
from modules.logger import setup_logging
from routers import auth, minutes, users

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    create_tables()
    yield

app = FastAPI(
    title=os.getenv("APP_NAME", "Minutes Generator API"),
    version=os.getenv("APP_VERSION", "1.0.0"),
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(minutes.router, prefix="/minutes", tags=["minutes"])
app.include_router(users.router, prefix="/users", tags=["users"])

@app.get("/")
async def root():
    return {"message": "Minutes Generator API", "version": os.getenv("APP_VERSION", "1.0.0")}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
