from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from app.modules.database import get_db, create_tables
from app.modules.auth_handler import (
    authenticate_user, 
    create_user, 
    create_access_token,
    get_user_by_username,
    get_user_by_email,
    get_current_user
)
from app.schemas.auth import UserCreate, UserLogin, Token, UserResponse
from app.modules.logger import get_logger
from datetime import timedelta
import os

logger = get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=UserResponse)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    logger.info(f"User registration attempt for username: {user.username}")
    
    existing_user = get_user_by_username(db, user.username)
    if existing_user:
        logger.warning(f"Registration failed: username {user.username} already exists")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    existing_email = get_user_by_email(db, user.email)
    if existing_email:
        logger.warning(f"Registration failed: email {user.email} already exists")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    try:
        db_user = create_user(db, user.username, user.email, user.password)
        logger.info(f"User registered successfully: {user.username}")
        return UserResponse(
            id=db_user.id,
            username=db_user.username,
            email=db_user.email,
            created_at=db_user.created_at.isoformat()
        )
    except Exception as e:
        logger.error(f"User registration failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )

@router.post("/login", response_model=Token)
async def login_user(user_credentials: UserLogin, db: Session = Depends(get_db)):
    logger.info(f"Login attempt for username: {user_credentials.username}")
    
    user = authenticate_user(db, user_credentials.username, user_credentials.password)
    if not user:
        logger.warning(f"Login failed for username: {user_credentials.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")))
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    logger.info(f"User logged in successfully: {user_credentials.username}")
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/refresh", response_model=Token)
async def refresh_token(current_user = Depends(get_current_user)):
    logger.info(f"Token refresh for user: {current_user.username}")
    
    access_token_expires = timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")))
    access_token = create_access_token(
        data={"sub": current_user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}
