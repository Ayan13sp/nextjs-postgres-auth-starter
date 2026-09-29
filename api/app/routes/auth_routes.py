from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from passlib.context import CryptContext

from app.db.database import User
from app.models.user_models import UserOut

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class SignupRequest(BaseModel):
    username: str
    password: str
    role: str

class LoginRequest(BaseModel):
    username: str
    password: str
    role: str

@router.post("/signup", response_model=UserOut)
async def signup(req: SignupRequest):
    existing_user = await User.find_one(User.username == req.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    hashed_password = pwd_context.hash(req.password)
    user = User(
        username=req.username,
        role=req.role,
        hashed_password=hashed_password
    )
    await user.insert()
    return user

@router.post("/login", response_model=UserOut)
async def login(req: LoginRequest):
    user = await User.find_one(User.username == req.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    if not user.hashed_password or not pwd_context.verify(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
        
    if user.role != req.role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"User exists but is a {user.role}, not a {req.role}"
        )
        
    return user
