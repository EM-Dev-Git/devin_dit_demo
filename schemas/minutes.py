from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class TranscriptInput(BaseModel):
    transcript: str
    meeting_title: Optional[str] = None
    participants: Optional[List[str]] = None

class MinutesBase(BaseModel):
    meeting_title: str
    summary: str
    key_points: List[str]
    action_items: List[str]
    participants: List[str]

class MinutesCreate(MinutesBase):
    pass

class MinutesOutput(MinutesBase):
    id: int
    created_at: datetime
    user_id: int
    
    class Config:
        from_attributes = True

class MinutesList(BaseModel):
    id: int
    meeting_title: str
    summary: str
    created_at: datetime
    
    class Config:
        from_attributes = True
