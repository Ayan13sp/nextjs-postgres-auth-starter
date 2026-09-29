import hashlib
import secrets
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.db.database import User
from app.models.user_models import UserOut

router = APIRouter()

def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    )
    return f"{salt}${key.hex()}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        if '$' in hashed_password:
            salt, key_hex = hashed_password.split('$', 1)
            new_key = hashlib.pbkdf2_hmac(
                'sha256',
                plain_password.encode('utf-8'),
                salt.encode('utf-8'),
                100000
            )
            return secrets.compare_digest(new_key.hex(), key_hex)
        else:
            try:
                import bcrypt
                return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
            except Exception:
                return False
    except Exception:
        return False

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
    
    hashed_pwd = hash_password(req.password)
    user = User(
        username=req.username,
        role=req.role,
        hashed_password=hashed_pwd
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
    
    if not user.hashed_password or not verify_password(req.password, user.hashed_password):
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
