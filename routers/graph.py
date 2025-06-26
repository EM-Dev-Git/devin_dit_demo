from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import time

from modules.database import get_db, User
from modules.auth import get_current_user
from modules.graph_client import GraphClient
from modules.openai_client import OpenAIClient
from modules.logger import log_request, get_logger
from schemas.graph import TranscriptListResponse, TranscriptContentResponse, GraphTranscriptMinutesRequest
from schemas.minutes import MinutesOutput

router = APIRouter()
logger = get_logger(__name__)

@router.get("/meetings/{meeting_id}/transcripts", response_model=TranscriptListResponse)
async def list_meeting_transcripts(
    meeting_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    start_time = time.time()
    
    try:
        graph_client = GraphClient()
        transcripts = graph_client.list_meeting_transcripts(current_user, db, meeting_id)
        
        processing_time = time.time() - start_time
        log_request(f"/graph/meetings/{meeting_id}/transcripts", current_user.id, processing_time)
        
        return TranscriptListResponse(
            meeting_id=meeting_id,
            transcripts=transcripts,
            count=len(transcripts)
        )
        
    except Exception as e:
        logger.error(f"Error listing transcripts for meeting {meeting_id}: {str(e)}")
        if "not authorized" in str(e).lower() or "re-authorize" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve meeting transcripts"
        )

@router.get("/transcripts/{transcript_id}/content", response_model=TranscriptContentResponse)
async def get_transcript_content(
    transcript_id: str,
    meeting_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    start_time = time.time()
    
    try:
        graph_client = GraphClient()
        content = graph_client.get_transcript_content(current_user, db, meeting_id, transcript_id)
        
        processing_time = time.time() - start_time
        log_request(f"/graph/transcripts/{transcript_id}/content", current_user.id, processing_time)
        
        return TranscriptContentResponse(
            transcript_id=transcript_id,
            meeting_id=meeting_id,
            content=content,
            length=len(content)
        )
        
    except Exception as e:
        logger.error(f"Error retrieving transcript content {transcript_id}: {str(e)}")
        if "not authorized" in str(e).lower() or "re-authorize" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve transcript content"
        )

@router.post("/transcripts/generate-minutes", response_model=MinutesOutput)
async def generate_minutes_from_graph_transcript(
    request: GraphTranscriptMinutesRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    start_time = time.time()
    
    try:
        graph_client = GraphClient()
        transcript_content = graph_client.get_transcript_content(
            current_user, db, request.meeting_id, request.transcript_id
        )
        
        openai_client = OpenAIClient()
        result = openai_client.generate_minutes(
            transcript_content,
            request.meeting_title,
            request.participants
        )
        
        from modules.database import Minutes
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
        log_request("/graph/transcripts/generate-minutes", current_user.id, processing_time)
        logger.info(f"Generated minutes from Graph transcript {request.transcript_id} for user {current_user.id}")
        
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
        logger.error(f"Error generating minutes from Graph transcript: {str(e)}")
        if "not authorized" in str(e).lower() or "re-authorize" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate minutes from transcript"
        )
