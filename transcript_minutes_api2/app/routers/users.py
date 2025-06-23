from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.modules.database import get_db, User
from app.modules.auth_handler import get_current_user
from app.schemas.users import UserProfileResponse, UserUpdate
from app.modules.logger import logger, log_api_call
import time

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/profile", response_model=UserProfileResponse)
async def get_profile(current_user: User = Depends(get_current_user)):
    start_time = time.time()
    
    try:
        logger.info(f"Fetching profile for user: {current_user.username}")
        
        duration = time.time() - start_time
        log_api_call("/users/profile", current_user.id, duration)
        
        return UserProfileResponse(
            username=current_user.username,
            email=current_user.email
        )
        
    except Exception as e:
        duration = time.time() - start_time
        log_api_call("/users/profile", current_user.id if current_user else None, error=str(e))
        logger.error(f"Failed to fetch profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.put("/profile", response_model=UserProfileResponse)
async def update_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    start_time = time.time()
    
    try:
        logger.info(f"Updating profile for user: {current_user.username}")
        
        if user_update.username is not None and user_update.username != current_user.username:
            existing_user = db.query(User).filter(
                User.username == user_update.username,
                User.id != current_user.id
            ).first()
            if existing_user:
                logger.warning(f"Username {user_update.username} already exists")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken"
                )
            current_user.username = user_update.username
        
        if user_update.email is not None and user_update.email != current_user.email:
            existing_user = db.query(User).filter(
                User.email == user_update.email,
                User.id != current_user.id
            ).first()
            if existing_user:
                logger.warning(f"Email {user_update.email} already exists")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already taken"
                )
            current_user.email = user_update.email
        
        db.commit()
        db.refresh(current_user)
        
        duration = time.time() - start_time
        log_api_call("/users/profile", current_user.id, duration)
        logger.info(f"Profile updated successfully for user: {current_user.username}")
        
        return UserProfileResponse(
            username=current_user.username,
            email=current_user.email
        )
        
    except HTTPException:
        raise
    except Exception as e:
        duration = time.time() - start_time
        log_api_call("/users/profile", current_user.id if current_user else None, error=str(e))
        logger.error(f"Failed to update profile: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )
