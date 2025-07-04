from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class GraphMeetingRequest(BaseModel):
    user_id: str
    limit: Optional[int] = 50

class GraphMeetingInfo(BaseModel):
    id: str
    subject: Optional[str]
    start_time: Optional[str]
    end_time: Optional[str]
    join_url: Optional[str]
    organizer: Optional[str]

class GraphMeetingListResponse(BaseModel):
    success: bool
    meetings: List[GraphMeetingInfo]
    message: str

class GraphTranscriptRequest(BaseModel):
    user_id: str
    meeting_id: str

class GraphTranscriptInfo(BaseModel):
    id: str
    created_date_time: Optional[str]
    meeting_id: str
    transcript_content_url: Optional[str]

class GraphTranscriptListResponse(BaseModel):
    success: bool
    transcripts: List[GraphTranscriptInfo]
    message: str

class GraphTranscriptContentRequest(BaseModel):
    user_id: str
    meeting_id: str
    transcript_id: str

class GraphTranscriptContentResponse(BaseModel):
    success: bool
    content: str
    transcript_id: str
    meeting_id: str
    message: str

class GraphMinutesGenerateRequest(BaseModel):
    user_id: str
    meeting_id: str
    transcript_id: str
    meeting_title: Optional[str] = None
