# schemas.py
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class FeedbackCreate(BaseModel):
    title: str
    content: str
    tag: str = "general"

class FeedbackOut(BaseModel):
    id: int
    title: str
    content: str
    tag: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)