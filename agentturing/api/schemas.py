from pydantic import BaseModel
from typing import Optional, List

class AskRequest(BaseModel):
    question: str

class AskResponse(BaseModel):
    answer: str
    route: str
    sources: Optional[List[str]] = []

class FeedbackRequest(BaseModel):
    question: str
    answer: str
    rating: Optional[float] = None
    comment: Optional[str] = None
    route: Optional[str] = None
