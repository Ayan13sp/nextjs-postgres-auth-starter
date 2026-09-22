from pydantic import BaseModel

class EvaluationRequest(BaseModel):
    """Request body for the evaluation endpoint."""
    model_answer: str
    student_answer: str

class EvaluationResponse(BaseModel):
    """Response body for the evaluation endpoint."""
    score: int
    feedback: str
    