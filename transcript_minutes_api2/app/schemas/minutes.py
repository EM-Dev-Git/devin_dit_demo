from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class MinutesGenerate(BaseModel):
    transcript: str = Field(..., min_length=10, max_length=10000)
    title: Optional[str] = Field(None, max_length=200)

class MinutesResponse(BaseModel):
    id: int
    user_id: int
    title: Optional[str]
    transcript: str
    generated_minutes: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class MinutesHistoryResponse(BaseModel):
    id: int
    title: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True
