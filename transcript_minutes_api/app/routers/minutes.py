from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.modules.database import get_db, Minutes, User
from app.modules.auth_handler import get_current_user
from app.modules.openai_client import generate_meeting_minutes
from app.schemas.minutes import MinutesCreate, MinutesResponse, MinutesGenerate
from app.modules.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/minutes", tags=["meeting minutes"])

@router.post("/generate", response_model=MinutesResponse)
async def generate_minutes(
    minutes_data: MinutesGenerate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    logger.info(f"Generating minutes for user: {current_user.username}")
    
    try:
        generated_content = await generate_meeting_minutes(
            transcript=minutes_data.transcript,
            title=minutes_data.title
        )
        
        db_minutes = Minutes(
            user_id=current_user.id,
            title=minutes_data.title or "Generated Meeting Minutes",
            transcript=minutes_data.transcript,
            generated_minutes=generated_content
        )
        
        db.add(db_minutes)
        db.commit()
        db.refresh(db_minutes)
        
        logger.info(f"Minutes generated and saved successfully for user: {current_user.username}")
        return MinutesResponse(
            id=db_minutes.id,
            user_id=db_minutes.user_id,
            title=db_minutes.title,
            transcript=db_minutes.transcript,
            generated_minutes=db_minutes.generated_minutes,
            created_at=db_minutes.created_at
        )
        
    except Exception as e:
        logger.error(f"Failed to generate minutes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate meeting minutes: {str(e)}"
        )

@router.get("/history", response_model=List[MinutesResponse])
async def get_minutes_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 10
):
    logger.info(f"Fetching minutes history for user: {current_user.username}")
    
    minutes = db.query(Minutes).filter(
        Minutes.user_id == current_user.id
    ).offset(skip).limit(limit).all()
    
    return [
        MinutesResponse(
            id=minute.id,
            user_id=minute.user_id,
            title=minute.title,
            transcript=minute.transcript,
            generated_minutes=minute.generated_minutes,
            created_at=minute.created_at
        )
        for minute in minutes
    ]

@router.get("/{minutes_id}", response_model=MinutesResponse)
async def get_minutes_by_id(
    minutes_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    logger.info(f"Fetching minutes {minutes_id} for user: {current_user.username}")
    
    minutes = db.query(Minutes).filter(
        Minutes.id == minutes_id,
        Minutes.user_id == current_user.id
    ).first()
    
    if not minutes:
        logger.warning(f"Minutes {minutes_id} not found for user: {current_user.username}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting minutes not found"
        )
    
    return MinutesResponse(
        id=minutes.id,
        user_id=minutes.user_id,
        title=minutes.title,
        transcript=minutes.transcript,
        generated_minutes=minutes.generated_minutes,
        created_at=minutes.created_at
    )
