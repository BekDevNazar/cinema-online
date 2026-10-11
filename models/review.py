from datetime import datetime

from sqlalchemy import ForeignKey, String, DateTime, func, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class Review(Base):
    __tablename__ = "reviews"

    __table_args__ = (
        CheckConstraint(
            "rating >= 0 AND rating <= 10",
            name="check_review_rating_range"
        ),
        UniqueConstraint(
            "movie_id", "user_id",
            name="uq_review_movie_user"
        )
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    movie_id: Mapped[int] = mapped_column(
        ForeignKey("movies.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    text: Mapped[str] = mapped_column(
        String(550),
        nullable=False
    )
    rating: Mapped[float] = mapped_column(
        nullable=False,
        default=0,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
