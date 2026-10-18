from datetime import datetime

from sqlalchemy import ForeignKey, String, DateTime, func, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class Message(Base):
    __tablename__ = "messages"

    __table_args__ = (
        CheckConstraint(
            "sender_id != receiver_id",
            name="ck_message_not_self",
        ),
    )
    
    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True
    )
    sender_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    receiver_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    text: Mapped[str] = mapped_column(
        String(2000),
        nullable=False
    )
    is_read: Mapped[bool] = mapped_column(
        default=False,
        server_default="false",
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
