from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class JobBase(BaseModel):
    title: str
    company: str
    location: str
    type: str
    description: str
    salary: Optional[str] = None
    tags: List[str] = []
    logo_url: Optional[str] = None

class JobCreate(JobBase):
    pass

class JobUpdate(JobBase):
    pass

class Job(JobBase):
    id: str
    created_at: datetime
    updated_at: datetime
    is_active: bool = True
    applications_count: int = 0

    class Config:
        populate_by_name = True

class JobInDB(JobBase):
    _id: str
    created_at: datetime
    updated_at: datetime
    is_active: bool = True
    applications_count: int = 0

class Application(BaseModel):
    id: Optional[str] = None
    job_id: str
    user_id: str
    cover_letter: str
    cv_url: str
    status: str = "pending"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True

class ApplicationInDB(Application):
    _id: Optional[str] = None