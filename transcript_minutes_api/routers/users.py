from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import time

from modules.database import get_db, User
from modules.auth import get_current_user, get_password_hash
from modules.logger import log_request, get_logger
from schemas.users import User as UserSchema, UserUpdate

router = APIRouter()
logger = get_logger(__name__)

@router.get("/me", response_model=UserSchema)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    start_time = time.time()
    processing_time = time.time() - start_time
    log_request("/users/me", current_user.id, processing_time)
    return current_user

@router.put("/me", response_model=UserSchema)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    start_time = time.time()
    
    update_data = user_update.dict(exclude_unset=True)
    
    if "email" in update_data:
        existing_user = db.query(User).filter(
            User.email == update_data["email"],
            User.id != current_user.id
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        current_user.email = update_data["email"]
    
    if "password" in update_data:
        current_user.password_hash = get_password_hash(update_data["password"])
    
    db.commit()
    db.refresh(current_user)
    
    processing_time = time.time() - start_time
    log_request("/users/me", current_user.id, processing_time)
    logger.info(f"User {current_user.id} updated their profile")
    
    return current_user

@router.delete("/me")
async def delete_current_user(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    start_time = time.time()
    
    current_user.is_active = False
    db.commit()
    
    processing_time = time.time() - start_time
    log_request("/users/me", current_user.id, processing_time)
    logger.info(f"User {current_user.id} deactivated their account")
    
    return {"message": "Account deactivated successfully"}
