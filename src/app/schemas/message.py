from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict, field_validator


class MessageCreate(BaseModel):
    text: str = Field(min_length=1, max_length=2000)

    @field_validator("text", mode="before")
    @classmethod
    def strip_text(cls, value):
        if isinstance(value, str):
            return value.strip()
        return value


class MessageResponse(BaseModel):
    sender_id: int
    receiver_id: int
    text: str
    is_read: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatResponse(BaseModel):
    user_id: int
    username: str
    last_message: str
    last_message_created_at: datetime
