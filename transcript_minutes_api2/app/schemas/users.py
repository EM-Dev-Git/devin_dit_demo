from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class UserProfileResponse(BaseModel):
    username: str
    email: str
    
    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50, pattern=r'^[a-zA-Z0-9_-]+$')
    email: Optional[EmailStr] = Field(None, max_length=100)
