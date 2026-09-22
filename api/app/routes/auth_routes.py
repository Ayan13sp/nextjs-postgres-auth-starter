from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.db.database import User
from app.models.user_models import UserOut

router = APIRouter()

class NaiveLoginRequest(BaseModel):
    username: str
    role: str

@router.post("/login", response_model=UserOut)
async def login(req: NaiveLoginRequest):
    user = await User.find_one(User.username == req.username)
    if not user:
        # Auto-signup if not found
        user = User(
            username=req.username,
            role=req.role
        )
        await user.insert()
    elif user.role != req.role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User exists but is a {user.role}, not a {req.role}"
        )
    return user
