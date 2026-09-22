from pydantic import BaseModel, EmailStr, Field, BeforeValidator
from typing import Annotated
from bson import ObjectId

def object_id_to_str(v):
    if isinstance(v, ObjectId):
        return str(v)
    return v

PyObjectId = Annotated[str, BeforeValidator(object_id_to_str)]

class UserCreate(BaseModel):
    """Pydantic model for creating a new user."""
    username: str = Field(..., min_length=3, max_length=20)
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: str

class UserOut(BaseModel):
    """Pydantic model for representing a user in API responses."""
    id: PyObjectId
    username: str 
    email: str | None = None
    role: str

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True
