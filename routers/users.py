from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from database import get_db
from dependencies import get_current_user
from models.favorite import Favorite
from models.follow import Follow
from models.movie import Movie
from models.review import Review
from models.user import User
from schemas.movie import ResponseMovieScheme
from schemas.user import PublicUserProfileResponse, PublicUserResponse

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.get(
    "/me/favorites/",
    response_model=list[ResponseMovieScheme],
)
async def get_user_favorite(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Movie)
        .join(
            Favorite,
            Favorite.movie_id == Movie.id,
        )
        .where(
            Favorite.user_id == current_user.id
        )
    )

    movies = result.scalars().all()

    return movies


@router.get(
    "/{user_id}/",
    response_model=PublicUserProfileResponse
)
async def search_user(
        user_id: int,
        db: AsyncSession = Depends(get_db)
):
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    result = await db.execute(
        select(Review, Movie).join(Movie, Review.movie_id == Movie.id)
        .where(Review.user_id == user_id)
        .order_by(Review.created_at.desc())
    )
    rows = result.all()

    reviews_data = []
    for review, movie in rows:
        reviews_data.append(
            {
                "id": review.id,
                "text": review.text,
                "rating": review.rating,
                "created_at": review.created_at,
                "movie": {
                    "id": movie.id,
                    "title": movie.title,
                    "poster_url": movie.poster_url
                }
            }
        )
    return {
        "id": user.id,
        "username": user.username,
        "created_at": user.created_at,
        "reviews": reviews_data
    }


@router.post(
    "/{user_id}/follow/",
    status_code=status.HTTP_201_CREATED
)
async def follow_user(
        user_id: int,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    following_user = await db.get(User, user_id)
    if following_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You can't follow yourself",
        )
    result = await db.execute(
        select(Follow).where(Follow.follower_id == current_user.id,
                             Follow.following_id == user_id)
    )
    is_follow = result.scalar_one_or_none()
    if is_follow is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already follow this user"
        )

    follow = Follow(
        follower_id=current_user.id,
        following_id=user_id,
    )

    db.add(follow)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already followed this user",
        )

    await db.refresh(follow)
    return follow


@router.delete(
    "/{user_id}/follow/",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_follow(
        user_id: int,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    user = await db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    result = await db.execute(
        select(Follow).where(Follow.follower_id == current_user.id,
                             Follow.following_id == user_id)
    )
    follow = result.scalar_one_or_none()
    if follow is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You are not follow at this user"
        )
    await db.delete(follow)
    await db.commit()


@router.get(
    "/{user_id}/followers/",
    response_model=list[PublicUserResponse]
)
async def search_followers(
        user_id: int,
        db: AsyncSession = Depends(get_db)
):
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not user"
        )
    result = await db.execute(
        select(User)
        .join(Follow, Follow.follower_id == User.id)
        .where(Follow.following_id == user_id)
    )
    user_followers = result.scalars().all()
    return user_followers


@router.get(
    "/{user_id}/following/",
    response_model=list[PublicUserResponse]
)
async def search_following(
        user_id: int,
        db: AsyncSession = Depends(get_db)
):
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not user"
        )
    result = await db.execute(
        select(User)
        .join(Follow, Follow.following_id == User.id)
        .where(Follow.follower_id == user_id)
    )
    user_following = result.scalars().all()
    return user_following
