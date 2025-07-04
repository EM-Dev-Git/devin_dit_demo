from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class MinutesBase(BaseModel):
    meeting_title: str
    transcript: str

class MinutesCreate(MinutesBase):
    pass

class MinutesUpdate(BaseModel):
    meeting_title: Optional[str] = None
    summary: Optional[str] = None
    key_points: Optional[List[str]] = None
    action_items: Optional[List[str]] = None
    participants: Optional[List[str]] = None

class MinutesResponse(BaseModel):
    id: int
    meeting_title: str
    summary: str
    key_points: List[str]
    action_items: List[str]
    participants: List[str]
    created_at: datetime
    updated_at: datetime
    user_id: int

    class Config:
        from_attributes = True

class MinutesGenerated(BaseModel):
    success: bool
    data: MinutesResponse
    message: str
