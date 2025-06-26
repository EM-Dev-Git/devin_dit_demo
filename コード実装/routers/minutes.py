from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import time

from modules.database import get_db, User, Minutes
from modules.auth import get_current_user
from modules.openai_client import OpenAIClient
from modules.logger import log_request, get_logger
from schemas.minutes import TranscriptInput, MinutesOutput, MinutesList

router = APIRouter()
logger = get_logger(__name__)

@router.post("/generate", response_model=MinutesOutput)
async def generate_minutes(
    transcript_input: TranscriptInput,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    start_time = time.time()
    
    try:
        openai_client = OpenAIClient()
        result = openai_client.generate_minutes(
            transcript_input.transcript,
            transcript_input.meeting_title,
            transcript_input.participants
        )
        
        db_minutes = Minutes(
            meeting_title=result["meeting_title"],
            summary=result["summary"],
            user_id=current_user.id
        )
        
        db_minutes.set_key_points_list(result["key_points"])
        db_minutes.set_action_items_list(result["action_items"])
        db_minutes.set_participants_list(result["participants"])
        
        db.add(db_minutes)
        db.commit()
        db.refresh(db_minutes)
        
        processing_time = time.time() - start_time
        log_request("/minutes/generate", current_user.id, processing_time)
        logger.info(f"Minutes generated for user {current_user.id}, minutes ID: {db_minutes.id}")
        
        return MinutesOutput(
            id=db_minutes.id,
            meeting_title=db_minutes.meeting_title,
            summary=db_minutes.summary,
            key_points=db_minutes.get_key_points_list(),
            action_items=db_minutes.get_action_items_list(),
            participants=db_minutes.get_participants_list(),
            created_at=db_minutes.created_at,
            user_id=db_minutes.user_id
        )
        
    except ValueError as e:
        logger.error(f"OpenAI configuration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OpenAI service not configured properly"
        )
    except Exception as e:
        logger.error(f"Error generating minutes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate minutes"
        )

@router.get("/", response_model=List[MinutesList])
async def get_minutes_list(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    start_time = time.time()
    
    minutes = db.query(Minutes).filter(Minutes.user_id == current_user.id).order_by(Minutes.created_at.desc()).all()
    
    processing_time = time.time() - start_time
    log_request("/minutes/", current_user.id, processing_time)
    
    return [
        MinutesList(
            id=minute.id,
            meeting_title=minute.meeting_title,
            summary=minute.summary,
            created_at=minute.created_at
        )
        for minute in minutes
    ]

@router.get("/{minutes_id}", response_model=MinutesOutput)
async def get_minutes(
    minutes_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    start_time = time.time()
    
    minutes = db.query(Minutes).filter(
        Minutes.id == minutes_id,
        Minutes.user_id == current_user.id
    ).first()
    
    if not minutes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Minutes not found"
        )
    
    processing_time = time.time() - start_time
    log_request(f"/minutes/{minutes_id}", current_user.id, processing_time)
    
    return MinutesOutput(
        id=minutes.id,
        meeting_title=minutes.meeting_title,
        summary=minutes.summary,
        key_points=minutes.get_key_points_list(),
        action_items=minutes.get_action_items_list(),
        participants=minutes.get_participants_list(),
        created_at=minutes.created_at,
        user_id=minutes.user_id
    )

@router.delete("/{minutes_id}")
async def delete_minutes(
    minutes_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    start_time = time.time()
    
    minutes = db.query(Minutes).filter(
        Minutes.id == minutes_id,
        Minutes.user_id == current_user.id
    ).first()
    
    if not minutes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Minutes not found"
        )
    
    db.delete(minutes)
    db.commit()
    
    processing_time = time.time() - start_time
    log_request(f"/minutes/{minutes_id}", current_user.id, processing_time)
    logger.info(f"Minutes deleted: ID {minutes_id} by user {current_user.id}")
    
    return {"message": "Minutes deleted successfully"}
