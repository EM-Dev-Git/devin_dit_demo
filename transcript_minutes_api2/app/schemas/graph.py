from pydantic import BaseModel, Field
from typing import List, Optional

class MeetingInfo(BaseModel):
    id: str
    subject: Optional[str]
    start_time: Optional[str]
    end_time: Optional[str]
    join_url: Optional[str]

class MeetingListResponse(BaseModel):
    meetings: List[MeetingInfo]
    
class TranscriptInfo(BaseModel):
    id: str
    created_date_time: Optional[str]
    end_date_time: Optional[str]
    content_url: Optional[str]

class TranscriptListResponse(BaseModel):
    transcripts: List[TranscriptInfo]

class TranscriptContentResponse(BaseModel):
    transcript_id: str
    content: str
    
class GraphMinutesGenerate(BaseModel):
    user_id: str = Field(..., description="Microsoft Graph user ID")
    meeting_id: str = Field(..., description="Online meeting ID")
    transcript_id: str = Field(..., description="Transcript ID")
    title: Optional[str] = Field(None, max_length=200, description="Optional meeting title")
