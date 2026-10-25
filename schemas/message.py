from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class MessageCreate(BaseModel):
    text: str = Field(min_length=1, max_length=2000)


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
