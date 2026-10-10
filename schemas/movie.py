from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field
from enum import Enum


class MovieGenre(str, Enum):
    action = "action"
    comedy = "comedy"
    drama = "drama"
    horror = "horror"
    sci_fi = "sci-fi"
    thriller = "thriller"
    fantasy = "fantasy"
    animation = "animation"
    documentary = "documentary"


class CreateMovieScheme(BaseModel):
    title: str = Field(
        max_length=255,
        min_length=1,
    )
    description: str = Field(min_length=1)
    release_year: int = Field(
        ge=1900,
        le=datetime.now(timezone.utc).year
    )
    duration_minutes: int = Field(gt=0)
    rating: float = Field(
        default=0,
        ge=0,
        le=10
    )
    genre: MovieGenre
    poster_url: str | None = Field(default=None)


class ResponseMovieScheme(CreateMovieScheme):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class MovieList(BaseModel):
    movies: list[ResponseMovieScheme]
    prev_page: str | None
    next_page: str | None
    total_pages: int
    total_items: int
    page: int
    page_size: int
