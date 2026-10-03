from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from database import get_db
from models.user import User
from schemas.auth import UserRegisterSchema, UserResponseSchema, TokenResponseSchema, UserLoginSchema
from security import hash_password, verify_password, create_access_token

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


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
    return TokenResponseSchema(
        access_token=access_token
    )
