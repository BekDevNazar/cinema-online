from datetime import datetime

from sqlalchemy import ForeignKey, String, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    type: Mapped[str] = mapped_column(
        String(64),
        nullable=False
    )
    message: Mapped[str] = mapped_column(
        String(2000),
        nullable=False
    )
    is_read: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )