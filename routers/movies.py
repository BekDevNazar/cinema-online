from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from starlette import status
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.movie import Movie
from schemas.movie import ResponseMovieScheme, CreateMovieScheme, MovieList

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


@router.get("/", response_model=MovieList)
async def get_movies(
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1, le=20),
        db: AsyncSession = Depends(get_db)
):
    offset = (page - 1) * page_size

    result = await db.execute(
        select(Movie)
        .order_by(Movie.id.desc())
        .offset(offset)
        .limit(page_size)
    )

    movies = result.scalars().all()
    total_items = await db.scalar(
        select(func.count(Movie.id))
    )
    total_pages = (total_items + page_size - 1) // page_size
    prev_page = None
    if page > 1:
        prev_page = f"/movies/?page={page - 1}&page_size={page_size}"

    next_page = None
    if page < total_pages:
        next_page = f"/movies/?page={page + 1}&page_size={page_size}"

    return {
        "movies": movies,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items,
        "page": page,
        "page_size": page_size,
    }
