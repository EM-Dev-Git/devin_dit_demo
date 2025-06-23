from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class MinutesBase(BaseModel):
    title: Optional[str] = None
    transcript: str

class MinutesCreate(MinutesBase):
    pass

class MinutesResponse(MinutesBase):
    id: int
    user_id: int
    generated_minutes: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class MinutesGenerate(BaseModel):
    transcript: str
    title: Optional[str] = None
