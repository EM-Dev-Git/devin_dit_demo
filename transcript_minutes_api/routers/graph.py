from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import time
import json

from modules.database import get_db, User, Minutes
from modules.auth import get_current_user
from modules.graph_client import get_user_meetings_list, get_meeting_transcripts_list, retrieve_transcript_content
from modules.openai_client import generate_minutes_from_transcript
from modules.logger import log_request, log_error, get_logger
from schemas.graph import (
    GraphMeetingRequest, GraphMeetingListResponse, GraphMeetingInfo,
    GraphTranscriptRequest, GraphTranscriptListResponse, GraphTranscriptInfo,
    GraphTranscriptContentRequest, GraphTranscriptContentResponse,
    GraphMinutesGenerateRequest
)
from schemas.minutes import MinutesGenerated, MinutesResponse

router = APIRouter()
logger = get_logger(__name__)

@router.post("/meetings", response_model=GraphMeetingListResponse)
async def list_user_meetings(
    request: GraphMeetingRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    start_time = time.time()
    
    try:
        meetings = await get_user_meetings_list(request.user_id, request.limit)
        
        meeting_list = [
            GraphMeetingInfo(
                id=meeting["id"],
                subject=meeting["subject"],
                start_time=meeting["start_time"],
                end_time=meeting["end_time"],
                join_url=meeting["join_url"],
                organizer=meeting["organizer"]
            )
            for meeting in meetings
        ]
        
        processing_time = time.time() - start_time
        log_request("/graph/meetings", current_user.id, processing_time)
        logger.info(f"Retrieved {len(meeting_list)} meetings for user {request.user_id}")
        
        return GraphMeetingListResponse(
            success=True,
            meetings=meeting_list,
            message=f"{len(meeting_list)}件の会議を取得しました"
        )
        
    except Exception as e:
        processing_time = time.time() - start_time
        log_error(str(e), "/graph/meetings", current_user.id)
        logger.error(f"Error retrieving meetings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve meetings: {str(e)}"
        )

@router.post("/meetings/{meeting_id}/transcripts", response_model=GraphTranscriptListResponse)
async def list_meeting_transcripts(
    meeting_id: str,
    request: GraphTranscriptRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    start_time = time.time()
    
    try:
        transcripts = await get_meeting_transcripts_list(request.user_id, meeting_id)
        
        transcript_list = [
            GraphTranscriptInfo(
                id=transcript["id"],
                created_date_time=transcript["created_date_time"],
                meeting_id=transcript["meeting_id"],
                transcript_content_url=transcript["transcript_content_url"]
            )
            for transcript in transcripts
        ]
        
        processing_time = time.time() - start_time
        log_request(f"/graph/meetings/{meeting_id}/transcripts", current_user.id, processing_time)
        logger.info(f"Retrieved {len(transcript_list)} transcripts for meeting {meeting_id}")
        
        return GraphTranscriptListResponse(
            success=True,
            transcripts=transcript_list,
            message=f"{len(transcript_list)}件のトランスクリプトを取得しました"
        )
        
    except Exception as e:
        processing_time = time.time() - start_time
        log_error(str(e), f"/graph/meetings/{meeting_id}/transcripts", current_user.id)
        logger.error(f"Error retrieving transcripts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve transcripts: {str(e)}"
        )

@router.post("/transcripts/content", response_model=GraphTranscriptContentResponse)
async def get_transcript_content(
    request: GraphTranscriptContentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    start_time = time.time()
    
    try:
        content = await retrieve_transcript_content(
            request.user_id,
            request.meeting_id,
            request.transcript_id
        )
        
        processing_time = time.time() - start_time
        log_request("/graph/transcripts/content", current_user.id, processing_time)
        logger.info(f"Retrieved transcript content for transcript {request.transcript_id}")
        
        return GraphTranscriptContentResponse(
            success=True,
            content=content,
            transcript_id=request.transcript_id,
            meeting_id=request.meeting_id,
            message="トランスクリプトの内容を取得しました"
        )
        
    except Exception as e:
        processing_time = time.time() - start_time
        log_error(str(e), "/graph/transcripts/content", current_user.id)
        logger.error(f"Error retrieving transcript content: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve transcript content: {str(e)}"
        )

@router.post("/generate-minutes", response_model=MinutesGenerated)
async def generate_minutes_from_graph(
    request: GraphMinutesGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    start_time = time.time()
    
    try:
        transcript_content = await retrieve_transcript_content(
            request.user_id,
            request.meeting_id,
            request.transcript_id
        )
        
        if not transcript_content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transcript content not found"
            )
        
        meeting_title = request.meeting_title or f"Meeting {request.meeting_id}"
        
        generated_data = generate_minutes_from_transcript(
            transcript_content,
            meeting_title
        )
        
        db_minutes = Minutes(
            meeting_title=meeting_title,
            transcript=transcript_content,
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
        log_request("/graph/generate-minutes", current_user.id, processing_time)
        logger.info(f"Minutes generated from Graph transcript for user {current_user.id}, meeting: {meeting_title}")
        
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
            message="Microsoft Graphから取得したトランスクリプトから議事録が正常に生成されました"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        processing_time = time.time() - start_time
        log_error(str(e), "/graph/generate-minutes", current_user.id)
        logger.error(f"Error generating minutes from Graph: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate minutes from Graph: {str(e)}"
        )
