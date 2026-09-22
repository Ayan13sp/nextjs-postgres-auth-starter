from typing import Optional, Annotated, List # Import List
from beanie import Document, init_beanie, Link, Indexed
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import EmailStr, Field
from app.core.config import settings

class User(Document):
    username: Annotated[str, Indexed(unique=True)]
    email: Optional[EmailStr] = None
    hashed_password: Optional[str] = None
    role: str

    class Settings:
        name = "users"

class QuestionSet(Document):
    title: str
    question: str
    model_answer: str
    creator: Link[User]
    assigned_students: List[Link[User]] = []

    class Settings:
        name = "question_sets"

class Submission(Document):
    question_set: Link[QuestionSet]
    student: Link[User]
    student_answer: str
    ai_score: int
    ai_feedback: str
    final_score: Optional[int] = None

    class Settings:
        name = "submissions"

async def init_db():
    client = AsyncIOMotorClient(settings.DATABASE_URL)
    await init_beanie(
        database=client.get_default_database(), 
        document_models=[User, QuestionSet, Submission]
    )
    print("Database initialized successfully with all models.")
