from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.modules.database import get_db, User
from app.modules.auth_handler import get_current_user, get_user_by_username, get_user_by_email
from app.schemas.users import UserProfile, UserProfileUpdate
from app.modules.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/users", tags=["user management"])

@router.get("/profile", response_model=UserProfile)
async def get_user_profile(current_user: User = Depends(get_current_user)):
    logger.info(f"Fetching profile for user: {current_user.username}")
    
    return UserProfile(
        username=current_user.username,
        email=current_user.email
    )

@router.put("/profile", response_model=UserProfile)
async def update_user_profile(
    profile_update: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    logger.info(f"Updating profile for user: {current_user.username}")
    
    if profile_update.username and profile_update.username != current_user.username:
        existing_user = get_user_by_username(db, profile_update.username)
        if existing_user:
            logger.warning(f"Username {profile_update.username} already exists")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
    
    if profile_update.email and profile_update.email != current_user.email:
        existing_email = get_user_by_email(db, profile_update.email)
        if existing_email:
            logger.warning(f"Email {profile_update.email} already exists")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already taken"
            )
    
    if profile_update.username:
        current_user.username = profile_update.username
    if profile_update.email:
        current_user.email = profile_update.email
    
    try:
        db.commit()
        db.refresh(current_user)
        logger.info(f"Profile updated successfully for user: {current_user.username}")
        
        return UserProfile(
            username=current_user.username,
            email=current_user.email
        )
    except Exception as e:
        logger.error(f"Failed to update profile: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )
