from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class Movie(Base):
    __tablename__ = "movies"

    __table_args__ = (
        CheckConstraint(
            "duration_minutes > 0",
            name="check_movie_duration_positive",
        ),
        CheckConstraint(
            "rating >= 0 AND rating <= 10",
            name="check_movie_rating_range",
        ),
        CheckConstraint(
            "release_year >= 1900",
            name="check_movie_release_year"
        )
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    release_year: Mapped[int] = mapped_column(
        nullable=False,
    )

    duration_minutes: Mapped[int] = mapped_column(
        nullable=False,
    )

    rating: Mapped[float] = mapped_column(
        nullable=False,
        default=0,
    )

    genre: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    poster_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
