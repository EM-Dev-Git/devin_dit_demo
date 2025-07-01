from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import time
import json

from modules.database import get_db, User, Minutes
from modules.auth import get_current_user
from modules.openai_client import generate_minutes_from_transcript
from modules.logger import log_request, log_error, get_logger
from schemas.minutes import MinutesCreate, MinutesResponse, MinutesUpdate, MinutesGenerated

router = APIRouter()
logger = get_logger(__name__)

@router.post("/generate", response_model=MinutesGenerated)
async def generate_minutes(
    minutes_data: MinutesCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    start_time = time.time()
    
    try:
        generated_data = generate_minutes_from_transcript(
            minutes_data.transcript,
            minutes_data.meeting_title
        )
        
        db_minutes = Minutes(
            meeting_title=minutes_data.meeting_title,
            transcript=minutes_data.transcript,
            summary=generated_data["summary"],
            key_points=json.dumps(generated_data["key_points"]),
            action_items=json.dumps(generated_data["action_items"]),
            participants=json.dumps(generated_data["participants"]),
            user_id=current_user.id
        )
        
        db.add(db_minutes)
        db.commit()
        db.refresh(db_minutes)
        
        processing_time = time.time() - start_time
        log_request("/minutes/generate", current_user.id, processing_time)
        logger.info(f"Minutes generated for user {current_user.id}, meeting: {minutes_data.meeting_title}")
        
        response_data = MinutesResponse(
            id=db_minutes.id,
            meeting_title=db_minutes.meeting_title,
            summary=db_minutes.summary,
            key_points=db_minutes.get_key_points_list(),
            action_items=db_minutes.get_action_items_list(),
            participants=db_minutes.get_participants_list(),
            created_at=db_minutes.created_at,
            updated_at=db_minutes.updated_at,
            user_id=db_minutes.user_id
        )
        
        return MinutesGenerated(
            success=True,
            data=response_data,
            message="議事録が正常に生成されました"
        )
        
    except Exception as e:
        processing_time = time.time() - start_time
        log_error(str(e), "/minutes/generate", current_user.id)
        logger.error(f"Error generating minutes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate minutes: {str(e)}"
        )

@router.get("/{minutes_id}", response_model=MinutesResponse)
async def get_minutes(
    minutes_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    start_time = time.time()
    
    db_minutes = db.query(Minutes).filter(
        Minutes.id == minutes_id,
        Minutes.user_id == current_user.id
    ).first()
    
    if not db_minutes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Minutes not found"
        )
    
    processing_time = time.time() - start_time
    log_request(f"/minutes/{minutes_id}", current_user.id, processing_time)
    
    return MinutesResponse(
        id=db_minutes.id,
        meeting_title=db_minutes.meeting_title,
        summary=db_minutes.summary,
        key_points=db_minutes.get_key_points_list(),
        action_items=db_minutes.get_action_items_list(),
        participants=db_minutes.get_participants_list(),
        created_at=db_minutes.created_at,
        updated_at=db_minutes.updated_at,
        user_id=db_minutes.user_id
    )

@router.get("/", response_model=List[MinutesResponse])
async def list_minutes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    start_time = time.time()
    
    db_minutes = db.query(Minutes).filter(
        Minutes.user_id == current_user.id
    ).offset(skip).limit(limit).all()
    
    processing_time = time.time() - start_time
    log_request("/minutes/", current_user.id, processing_time)
    
    return [
        MinutesResponse(
            id=minutes.id,
            meeting_title=minutes.meeting_title,
            summary=minutes.summary,
            key_points=minutes.get_key_points_list(),
            action_items=minutes.get_action_items_list(),
            participants=minutes.get_participants_list(),
            created_at=minutes.created_at,
            updated_at=minutes.updated_at,
            user_id=minutes.user_id
        )
        for minutes in db_minutes
    ]

@router.put("/{minutes_id}", response_model=MinutesResponse)
async def update_minutes(
    minutes_id: int,
    minutes_update: MinutesUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    start_time = time.time()
    
    db_minutes = db.query(Minutes).filter(
        Minutes.id == minutes_id,
        Minutes.user_id == current_user.id
    ).first()
    
    if not db_minutes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Minutes not found"
        )
    
    update_data = minutes_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        if field == "key_points" and value is not None:
            db_minutes.set_key_points_list(value)
        elif field == "action_items" and value is not None:
            db_minutes.set_action_items_list(value)
        elif field == "participants" and value is not None:
            db_minutes.set_participants_list(value)
        else:
            setattr(db_minutes, field, value)
    
    db.commit()
    db.refresh(db_minutes)
    
    processing_time = time.time() - start_time
    log_request(f"/minutes/{minutes_id}", current_user.id, processing_time)
    logger.info(f"Minutes {minutes_id} updated by user {current_user.id}")
    
    return MinutesResponse(
        id=db_minutes.id,
        meeting_title=db_minutes.meeting_title,
        summary=db_minutes.summary,
        key_points=db_minutes.get_key_points_list(),
        action_items=db_minutes.get_action_items_list(),
        participants=db_minutes.get_participants_list(),
        created_at=db_minutes.created_at,
        updated_at=db_minutes.updated_at,
        user_id=db_minutes.user_id
    )

@router.delete("/{minutes_id}")
async def delete_minutes(
    minutes_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    start_time = time.time()
    
    db_minutes = db.query(Minutes).filter(
        Minutes.id == minutes_id,
        Minutes.user_id == current_user.id
    ).first()
    
    if not db_minutes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Minutes not found"
        )
    
    db.delete(db_minutes)
    db.commit()
    
    processing_time = time.time() - start_time
    log_request(f"/minutes/{minutes_id}", current_user.id, processing_time)
    logger.info(f"Minutes {minutes_id} deleted by user {current_user.id}")
    
    return {"message": "Minutes deleted successfully"}
