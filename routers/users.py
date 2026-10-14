from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from database import get_db
from dependencies import get_current_user
from models.favorite import Favorite
from models.movie import Movie
from models.review import Review
from models.user import User
from schemas.movie import ResponseMovieScheme
from schemas.user import PublicUserProfileResponse

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