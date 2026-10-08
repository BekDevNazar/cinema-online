from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from starlette import status
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.movie import Movie
from schemas.movie import ResponseMovieScheme, CreateMovieScheme

router = APIRouter(
    prefix="/movies",
    tags=["Movies"]
)


@router.post(
    "/",
    response_model=ResponseMovieScheme,
    status_code=status.HTTP_201_CREATED
)
async def create_movie(
        data: CreateMovieScheme,
        db: AsyncSession = Depends(get_db)
):
    movie = Movie(
        title=data.title,
        description=data.description,
        release_year=data.release_year,
        duration_minutes=data.duration_minutes,
        rating=data.rating,
        genre=data.genre,
        poster_url=data.poster_url,
    )
    db.add(movie)
    await db.commit()
    await db.refresh(movie)
    return movie
