from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import time

from modules.database import get_db, User
from modules.auth import get_current_user
from modules.logger import log_request, get_logger
from schemas.users import UserProfile, UserUpdate

router = APIRouter()
logger = get_logger(__name__)

@router.get("/profile", response_model=UserProfile)
async def get_profile(current_user: User = Depends(get_current_user)):
    start_time = time.time()
    processing_time = time.time() - start_time
    log_request("/users/profile", current_user.id, processing_time)
    
    return UserProfile(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        created_at=current_user.created_at,
        is_active=current_user.is_active
    )

@router.put("/profile", response_model=UserProfile)
async def update_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    start_time = time.time()
    
    if user_update.email:
        existing_user = db.query(User).filter(
            User.email == user_update.email,
            User.id != current_user.id
        ).first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        current_user.email = user_update.email
    
    db.commit()
    db.refresh(current_user)
    
    processing_time = time.time() - start_time
    log_request("/users/profile", current_user.id, processing_time)
    logger.info(f"Profile updated for user {current_user.id}")
    
    return UserProfile(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        created_at=current_user.created_at,
        is_active=current_user.is_active
    )
