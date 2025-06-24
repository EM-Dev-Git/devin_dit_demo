from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.modules.database import get_db, User, Minutes
from app.modules.auth_handler import get_current_user
from app.modules.graph_client import graph_client
from app.modules.openai_client import generate_minutes
from app.schemas.graph import (
    MeetingListResponse, 
    TranscriptListResponse, 
    TranscriptContentResponse,
    GraphMinutesGenerate
)
from app.schemas.minutes import MinutesResponse
from app.modules.logger import logger, log_api_call
import time

router = APIRouter(prefix="/graph", tags=["microsoft graph"])

@router.get("/meetings/{user_id}", response_model=MeetingListResponse)
async def get_user_meetings(
    user_id: str,
    current_user: User = Depends(get_current_user)
):
    start_time = time.time()
    
    try:
        logger.info(f"Fetching meetings for Graph user: {user_id}")
        
        meetings = await graph_client.get_user_meetings(user_id)
        
        duration = time.time() - start_time
        log_api_call(f"/graph/meetings/{user_id}", current_user.id, duration)
        
        return MeetingListResponse(meetings=meetings)
        
    except Exception as e:
        duration = time.time() - start_time
        log_api_call(f"/graph/meetings/{user_id}", current_user.id, error=str(e))
        logger.error(f"Failed to fetch meetings: {str(e)}")
        
        if "Graph client not initialized" in str(e):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Microsoft Graph integration not configured"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch meetings from Microsoft Graph"
            )

@router.get("/meetings/{user_id}/{meeting_id}/transcripts", response_model=TranscriptListResponse)
async def get_meeting_transcripts(
    user_id: str,
    meeting_id: str,
    current_user: User = Depends(get_current_user)
):
    start_time = time.time()
    
    try:
        logger.info(f"Fetching transcripts for meeting: {meeting_id}")
        
        transcripts = await graph_client.get_meeting_transcripts(user_id, meeting_id)
        
        duration = time.time() - start_time
        log_api_call(f"/graph/meetings/{user_id}/{meeting_id}/transcripts", current_user.id, duration)
        
        return TranscriptListResponse(transcripts=transcripts)
        
    except Exception as e:
        duration = time.time() - start_time
        log_api_call(f"/graph/meetings/{user_id}/{meeting_id}/transcripts", current_user.id, error=str(e))
        logger.error(f"Failed to fetch transcripts: {str(e)}")
        
        if "Graph client not initialized" in str(e):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Microsoft Graph integration not configured"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch transcripts from Microsoft Graph"
            )

@router.get("/meetings/{user_id}/{meeting_id}/transcripts/{transcript_id}/content", response_model=TranscriptContentResponse)
async def get_transcript_content(
    user_id: str,
    meeting_id: str,
    transcript_id: str,
    current_user: User = Depends(get_current_user)
):
    start_time = time.time()
    
    try:
        logger.info(f"Fetching transcript content: {transcript_id}")
        
        content = await graph_client.get_transcript_content(user_id, meeting_id, transcript_id)
        
        duration = time.time() - start_time
        log_api_call(f"/graph/meetings/{user_id}/{meeting_id}/transcripts/{transcript_id}/content", current_user.id, duration)
        
        return TranscriptContentResponse(
            transcript_id=transcript_id,
            content=content
        )
        
    except Exception as e:
        duration = time.time() - start_time
        log_api_call(f"/graph/meetings/{user_id}/{meeting_id}/transcripts/{transcript_id}/content", current_user.id, error=str(e))
        logger.error(f"Failed to fetch transcript content: {str(e)}")
        
        if "Graph client not initialized" in str(e):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Microsoft Graph integration not configured"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to fetch transcript content from Microsoft Graph"
            )

@router.post("/minutes/generate", response_model=MinutesResponse, status_code=status.HTTP_201_CREATED)
async def generate_minutes_from_graph(
    request: GraphMinutesGenerate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    start_time = time.time()
    
    try:
        logger.info(f"Generating minutes from Graph transcript: {request.transcript_id}")
        
        transcript_content = await graph_client.get_transcript_content(
            request.user_id, 
            request.meeting_id, 
            request.transcript_id
        )
        
        if not transcript_content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transcript content not found"
            )
        
        generated_content = await generate_minutes(
            transcript=transcript_content,
            user_id=current_user.id,
            title=request.title
        )
        
        db_minutes = Minutes(
            user_id=current_user.id,
            title=request.title or f"Meeting Minutes from Graph ({request.meeting_id})",
            transcript=transcript_content,
            generated_minutes=generated_content
        )
        
        db.add(db_minutes)
        db.commit()
        db.refresh(db_minutes)
        
        duration = time.time() - start_time
        log_api_call("/graph/minutes/generate", current_user.id, duration)
        logger.info(f"Minutes generated from Graph transcript successfully")
        
        return MinutesResponse(
            id=db_minutes.id,
            user_id=db_minutes.user_id,
            title=db_minutes.title,
            transcript=db_minutes.transcript,
            generated_minutes=db_minutes.generated_minutes,
            created_at=db_minutes.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        duration = time.time() - start_time
        log_api_call("/graph/minutes/generate", current_user.id, error=str(e))
        logger.error(f"Failed to generate minutes from Graph: {str(e)}")
        
        if "Graph client not initialized" in str(e):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Microsoft Graph integration not configured"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate minutes from Microsoft Graph transcript"
            )
