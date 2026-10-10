from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select, func
from starlette import status
from sqlalchemy.ext.asyncio import AsyncSession
from urllib.parse import urlencode

from database import get_db
from models.movie import Movie
from schemas.movie import ResponseMovieScheme, CreateMovieScheme, MovieList, MovieGenre

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
        genre=data.genre.value,
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
        search: str | None = Query(None, min_length=1),
        genre: MovieGenre | None = Query(None),
        release_year: int | None = Query(None),
        min_rating: float | None = Query(None, ge=0, le=10),
        db: AsyncSession = Depends(get_db)
):
    filters = []

    if search is not None:
        filters.append(
            Movie.title.ilike(f"%{search}%")
        )
    if genre is not None:
        filters.append(
            Movie.genre == genre.value
        )
    if release_year is not None:
        filters.append(
            Movie.release_year == release_year
        )
    if min_rating is not None:
        filters.append(
            Movie.rating >= min_rating
        )

    offset = (page - 1) * page_size
    query_movies = (
        select(Movie)
        .where(*filters)
        .order_by(Movie.id.desc())
        .offset(offset)
        .limit(page_size)
    )

    result = await db.execute(
        query_movies
    )

    movies = result.scalars().all()
    total_items = await db.scalar(select(func.count(Movie.id)).where(*filters))
    total_items = total_items or 0
    total_pages = (total_items + page_size - 1) // page_size

    params = {
        "page_size": page_size
    }
    if search is not None:
        params["search"] = search
    if genre is not None:
        params["genre"] = genre.value
    if min_rating is not None:
        params["min_rating"] = min_rating
    if release_year is not None:
        params["release_year"] = release_year

    prev_page = None
    if page > 1:
        prev_params = {
            **params,
            "page": page - 1
        }
        prev_page = f"/movies/?{urlencode(prev_params)}"

    next_page = None
    if page < total_pages:
        next_params = {
            **params,
            "page": page + 1
        }
        next_page = f"/movies/?{urlencode(next_params)}"


    return {
        "movies": movies,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items,
        "page": page,
        "page_size": page_size,
    }


@router.get(
    "/{movie_id}/",
    response_model=ResponseMovieScheme,
    status_code=status.HTTP_200_OK
)
async def get_movie_by_id(
        movie_id: int,
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Movie).where(Movie.id == movie_id)
    )
    movie = result.scalar_one_or_none()

    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found"
        )
    return movie







