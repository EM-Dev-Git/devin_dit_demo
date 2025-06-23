from pydantic import BaseModel, EmailStr
from typing import Optional

class UserProfile(BaseModel):
    username: str
    email: EmailStr

class UserProfileUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
