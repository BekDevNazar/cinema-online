from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from dependencies import get_current_user
from models.movie import Favorite, Movie
from models.user import User
from schemas.movie import ResponseMovieScheme

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