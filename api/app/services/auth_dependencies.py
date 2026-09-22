from fastapi import Header, HTTPException, status
from app.db.database import User
from bson import ObjectId

async def get_current_user(x_user_id: str = Header(None)) -> User:
    """
    Naive authentication: reads x-user-id header and fetches user from DB.
    """
    if not x_user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-User-ID header"
        )
    try:
        user = await User.get(ObjectId(x_user_id))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        return user
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID format"
        )
