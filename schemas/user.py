from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ProfileMovieResponse(BaseModel):
    id: int
    title: str
    poster_url: str | None

    model_config = ConfigDict(from_attributes=True)


class ProfileReviewResponse(BaseModel):
    id: int
    text: str
    rating: float
    created_at: datetime
    movie: ProfileMovieResponse

    model_config = ConfigDict(from_attributes=True)


class PublicUserProfileResponse(BaseModel):
    id: int
    username: str
    created_at: datetime
    reviews: list[ProfileReviewResponse]

    model_config = ConfigDict(from_attributes=True)


class PublicUserResponse(BaseModel):
    id: int
    username: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
