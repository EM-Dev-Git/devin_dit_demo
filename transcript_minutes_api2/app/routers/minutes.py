from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from app.modules.database import get_db, User, Minutes
from app.modules.auth_handler import get_current_user
from app.modules.openai_client import generate_minutes
from app.schemas.minutes import MinutesGenerate, MinutesResponse, MinutesHistoryResponse
from app.modules.logger import logger, log_api_call
import time

router = APIRouter(prefix="/minutes", tags=["meeting minutes"])

@router.post("/generate", response_model=MinutesResponse, status_code=status.HTTP_201_CREATED)
async def generate_meeting_minutes(
    minutes_request: MinutesGenerate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    start_time = time.time()
    
    try:
        logger.info(f"Generating minutes for user: {current_user.username}")
        
        generated_content = await generate_minutes(
            transcript=minutes_request.transcript,
            user_id=current_user.id,
            title=minutes_request.title
        )
        
        db_minutes = Minutes(
            user_id=current_user.id,
            title=minutes_request.title or "Generated Meeting Minutes",
            transcript=minutes_request.transcript,
            generated_minutes=generated_content
        )
        
        db.add(db_minutes)
        db.commit()
        db.refresh(db_minutes)
        
        duration = time.time() - start_time
        log_api_call("/minutes/generate", current_user.id, duration)
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
        duration = time.time() - start_time
        log_api_call("/minutes/generate", current_user.id, error=str(e))
        logger.error(f"Failed to generate minutes: {str(e)}")
        
        if "OpenAI" in str(e) or "議事録の生成に失敗しました" in str(e):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(e)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate meeting minutes"
            )

@router.get("/history", response_model=List[MinutesHistoryResponse])
async def get_minutes_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Number of records to return")
):
    start_time = time.time()
    
    try:
        logger.info(f"Fetching minutes history for user: {current_user.username}")
        
        minutes = db.query(Minutes).filter(
            Minutes.user_id == current_user.id
        ).order_by(
            Minutes.created_at.desc()
        ).offset(skip).limit(limit).all()
        
        duration = time.time() - start_time
        log_api_call("/minutes/history", current_user.id, duration)
        
        return [
            MinutesHistoryResponse(
                id=minute.id,
                title=minute.title,
                created_at=minute.created_at
            )
            for minute in minutes
        ]
        
    except Exception as e:
        duration = time.time() - start_time
        log_api_call("/minutes/history", current_user.id, error=str(e))
        logger.error(f"Failed to fetch minutes history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/{minutes_id}", response_model=MinutesResponse)
async def get_minutes(
    minutes_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    start_time = time.time()
    
    try:
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
        
        duration = time.time() - start_time
        log_api_call(f"/minutes/{minutes_id}", current_user.id, duration)
        
        return MinutesResponse(
            id=minutes.id,
            user_id=minutes.user_id,
            title=minutes.title,
            transcript=minutes.transcript,
            generated_minutes=minutes.generated_minutes,
            created_at=minutes.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        duration = time.time() - start_time
        log_api_call(f"/minutes/{minutes_id}", current_user.id, error=str(e))
        logger.error(f"Failed to fetch minutes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
