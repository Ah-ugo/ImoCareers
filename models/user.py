from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    name: str

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    id: str
    role: str
    created_at: datetime
    photo_url: Optional[str] = None

    class Config:
        from_attributes = True

class User(UserBase):
    id: str
    role: str
    created_at: datetime
    photo_url: Optional[str] = None

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    name: Optional[str] = None
    photo_url: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    # location: Optional[str] = None
    # bio: Optional[str] = None

class Education(BaseModel):
    school: str
    degree: str
    field: str
    start_date: datetime
    end_date: Optional[datetime] = None
    current: bool = False

class Experience(BaseModel):
    company: str
    position: str
    description: str
    start_date: datetime
    end_date: Optional[datetime] = None
    current: bool = False

class CV(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None
    skills: List[str] = []
    education: List[Education] = []
    experience: List[Experience] = []
    cv_url: Optional[str] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)