from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.modules.database import get_db, User
from app.modules.auth_handler import authenticate_user, create_access_token, get_password_hash, get_current_user
from app.schemas.auth import UserCreate, UserLogin, Token, UserResponse
from app.modules.logger import logger, log_api_call
from datetime import timedelta
import time
import os

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    start_time = time.time()
    
    try:
        logger.info(f"User registration attempt for username: {user.username}")
        
        db_user = db.query(User).filter(User.username == user.username).first()
        if db_user:
            logger.warning(f"Registration failed: username {user.username} already exists")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        db_user = db.query(User).filter(User.email == user.email).first()
        if db_user:
            logger.warning(f"Registration failed: email {user.email} already exists")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        hashed_password = get_password_hash(user.password)
        db_user = User(
            username=user.username,
            email=user.email,
            hashed_password=hashed_password
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        duration = time.time() - start_time
        log_api_call("/auth/register", db_user.id, duration)
        logger.info(f"User registered successfully: {user.username}")
        
        return UserResponse(
            id=db_user.id,
            username=db_user.username,
            email=db_user.email,
            created_at=db_user.created_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        duration = time.time() - start_time
        log_api_call("/auth/register", error=str(e))
        logger.error(f"User registration failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )

@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    start_time = time.time()
    
    try:
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
        
        duration = time.time() - start_time
        log_api_call("/auth/login", user.id, duration)
        logger.info(f"User logged in successfully: {user_credentials.username}")
        
        return {"access_token": access_token, "token_type": "bearer"}
        
    except HTTPException:
        raise
    except Exception as e:
        duration = time.time() - start_time
        log_api_call("/auth/login", error=str(e))
        logger.error(f"Login failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/refresh", response_model=Token)
async def refresh_token(current_user: User = Depends(get_current_user)):
    start_time = time.time()
    
    try:
        logger.info(f"Token refresh for user: {current_user.username}")
        
        access_token_expires = timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")))
        access_token = create_access_token(
            data={"sub": current_user.username}, expires_delta=access_token_expires
        )
        
        duration = time.time() - start_time
        log_api_call("/auth/refresh", current_user.id, duration)
        
        return {"access_token": access_token, "token_type": "bearer"}
        
    except Exception as e:
        duration = time.time() - start_time
        log_api_call("/auth/refresh", current_user.id if current_user else None, error=str(e))
        logger.error(f"Token refresh failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
