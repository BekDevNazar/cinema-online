from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from config import settings
from database import get_db
from dependencies import get_current_user
from models.user import User, RefreshToken
from schemas.auth import UserRegisterSchema, UserResponseSchema, TokenResponseSchema, UserLoginSchema, \
    RefreshTokenCheckSchema
from security import hash_password, verify_password, create_access_token, generate_refresh_token, \
    hash_refresh_token

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


def create_refresh_token(user_id: int, refresh_token: str) -> RefreshToken:
    refresh_token_hash = hash_refresh_token(refresh_token)
    refresh_token_record = RefreshToken(
        user_id=user_id,
        token_hash=refresh_token_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        ),
    )
    return refresh_token_record


@router.post(
    "/register",
    response_model=UserResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
async def register_user(
    user_data: UserRegisterSchema,
    db: AsyncSession = Depends(get_db),
):
    user = User(
        username=user_data.username.lower(),
        email=str(user_data.email).lower(),
        password_hash=await run_in_threadpool(
            hash_password,
            user_data.password,
        ),
        role="user",
    )

    db.add(user)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Email or username already exists",
        )

    await db.refresh(user)

    return UserResponseSchema.model_validate(user)


@router.post(
    "/login/",
    response_model=TokenResponseSchema
)
async def user_login(
        user_data: UserLoginSchema,
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(User)
        .where(User.email == str(user_data.email).lower())
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )
    is_valid = await run_in_threadpool(
        verify_password,
        user_data.password,
        user.password_hash,
    )
    if not is_valid:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )
    access_token = create_access_token(user.id)

    refresh_token = generate_refresh_token()
    refresh_token_record = create_refresh_token(user.id, refresh_token)

    db.add(refresh_token_record)
    await db.commit()

    return TokenResponseSchema(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.get(
    "/me",
    response_model=UserResponseSchema,
)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
):
    return current_user


@router.post(
    "/refresh/",
    response_model=TokenResponseSchema
)
async def update_access_token(
        refresh_data: RefreshTokenCheckSchema,
        db: AsyncSession = Depends(get_db)
):
    refresh_token_hash = hash_refresh_token(refresh_data.refresh_token)

    result = await db.execute(
        select(RefreshToken)
        .where(RefreshToken.token_hash == refresh_token_hash)
    )
    refresh_token = result.scalar_one_or_none()
    if ((refresh_token is None)
            or (refresh_token.expires_at < datetime.now(timezone.utc)))\
            or (refresh_token.revoked_at is not None):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Problem with refresh token"
        )
    user_id = refresh_token.user_id
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not User"
        )

    new_access_token = create_access_token(
        user.id
    )
    refresh_token.revoked_at = datetime.now(timezone.utc)
    raw_refresh_token = generate_refresh_token()
    new_refresh_token = create_refresh_token(user_id, raw_refresh_token)
    db.add(new_refresh_token)
    await db.commit()
    return {
        "access_token": new_access_token,
        "refresh_token": raw_refresh_token
    }


@router.post("/logout/")
async def logout(
        data: RefreshTokenCheckSchema,
        db: AsyncSession = Depends(get_db)
):
    hash_token = hash_refresh_token(data.refresh_token)
    result = await db.execute(
        select(RefreshToken)
        .where(RefreshToken.token_hash == hash_token)
    )
    refresh_token = result.scalar_one_or_none()
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Refresh token not found",
        )
    if refresh_token.revoked_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refresh token has already been revoked",
        )
    refresh_token.revoked_at = datetime.now(timezone.utc)
    await db.commit()
    return {
        "detail": "Logout was completed"
    }









