from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class GraphAuthRequest(BaseModel):
    state: Optional[str] = None

class GraphAuthResponse(BaseModel):
    auth_url: str
    state: Optional[str] = None

class GraphCallbackRequest(BaseModel):
    code: str
    state: Optional[str] = None

class GraphTokenStatus(BaseModel):
    is_authorized: bool
    expires_at: Optional[datetime] = None
    needs_reauth: bool = False

class TranscriptMetadata(BaseModel):
    id: str
    created_date_time: Optional[str] = None
    meeting_id: str
    transcript_content_url: Optional[str] = None

class TranscriptListResponse(BaseModel):
    meeting_id: str
    transcripts: List[TranscriptMetadata]
    count: int

class TranscriptContentResponse(BaseModel):
    transcript_id: str
    meeting_id: str
    content: str
    length: int

class GraphTranscriptMinutesRequest(BaseModel):
    meeting_id: str
    transcript_id: str
    meeting_title: Optional[str] = None
    participants: Optional[List[str]] = None
