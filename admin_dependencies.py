from fastapi import Depends, HTTPException
from starlette import status

from dependencies import get_current_user
from models.user import User


async def get_current_admin(
        current_user: User = Depends(get_current_user),
):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not admin"
        )
    return current_user
