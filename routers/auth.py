from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import timedelta
import time

from modules.database import get_db, User
from modules.auth import (
    authenticate_user, create_access_token, create_refresh_token,
    get_password_hash, verify_token, get_current_user
)
from modules.logger import log_request, get_logger
from schemas.auth import Token, RefreshTokenRequest
from schemas.users import UserCreate, UserLogin, User as UserSchema

router = APIRouter()
logger = get_logger(__name__)

@router.post("/register", response_model=UserSchema)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    start_time = time.time()
    
    db_user = db.query(User).filter(
        (User.username == user.username) | (User.email == user.email)
    ).first()
    
    if db_user:
        if db_user.username == user.username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        password_hash=hashed_password
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    processing_time = time.time() - start_time
    log_request("/auth/register", db_user.id, processing_time)
    logger.info(f"New user registered: {user.username}")
    
    return db_user

@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    start_time = time.time()
    
    user = authenticate_user(db, user_credentials.username, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.username})
    refresh_token = create_refresh_token(data={"sub": user.username})
    
    processing_time = time.time() - start_time
    log_request("/auth/login", user.id, processing_time)
    logger.info(f"User logged in: {user.username}")
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_request: RefreshTokenRequest, db: Session = Depends(get_db)):
    start_time = time.time()
    
    try:
        username = verify_token(refresh_request.refresh_token, "refresh")
        user = db.query(User).filter(User.username == username).first()
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        access_token = create_access_token(data={"sub": user.username})
        new_refresh_token = create_refresh_token(data={"sub": user.username})
        
        processing_time = time.time() - start_time
        log_request("/auth/refresh", user.id, processing_time)
        
        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refreshing token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

@router.get("/me", response_model=UserSchema)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    start_time = time.time()
    processing_time = time.time() - start_time
    log_request("/auth/me", current_user.id, processing_time)
    return current_user
