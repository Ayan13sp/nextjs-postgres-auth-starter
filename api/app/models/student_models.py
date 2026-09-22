from pydantic import BaseModel, Field
from typing import Optional, List
from .user_models import PyObjectId, UserOut 

class QuestionSetForStudentOut(BaseModel):
    """A simplified QuestionSet view for students."""
    id: PyObjectId
    title: str
    question: str
    creator: UserOut 

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True

class SubmissionCreate(BaseModel):
    """Request body for a student submitting an answer."""
    question_set_id: str
    answer: str = Field(..., min_length=5)

class SubmissionResultOut(BaseModel):
    """Detailed result view for a student's own submission."""
    id: PyObjectId
    question_set: QuestionSetForStudentOut
    student_answer: str
    ai_score: int
    ai_feedback: str
    final_score: Optional[int] = None

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True
