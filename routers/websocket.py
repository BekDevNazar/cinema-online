import jwt
from fastapi import APIRouter, Query, Depends, WebSocket
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.websockets import WebSocketDisconnect

from config import settings
from database import get_db
from models.message import Message
from models.notification import Notification
from models.user import User
from websocket_manager import manager

router = APIRouter(
    prefix="/ws",
    tags=["Websocket"]
)


@router.websocket("/chat/{user_id}")
async def send_message(
        user_id: int,
        websocket: WebSocket,
        token: str = Query(),
        db: AsyncSession = Depends(get_db),
):
    try:
        access_token = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"require": ["sub", "exp", "type"]},
        )
        if access_token.get("type") != "access":
            await websocket.close(code=1008)
            return
        my_id = int(access_token["sub"])
    except (jwt.InvalidTokenError, ValueError, TypeError):
        await websocket.close(code=1008)
        return

    recipient = await db.get(User, user_id)
    if recipient is None:
        await websocket.close(code=1008)
        return
    user = await db.get(User, my_id)

    if user is None:
        await websocket.close(code=1008)
        return

    if my_id == user_id:
        await websocket.close(code=1008)
        return
    await manager.connect(
        websocket, my_id
    )
    try:
        while True:
            data = await websocket.receive_json()
            if not isinstance(data, dict):
                await websocket.close(code=1008)
                return
            event_type  = data.get("type")
            if event_type  == "message":
                text = data.get("text")
                if not isinstance(text, str):
                    await websocket.close(code=1008)
                    return
                text = text.strip()
                if not text or len(text) > 2000:
                    await websocket.close(code=1008)
                    return
                message = Message(
                    sender_id=my_id,
                    receiver_id=user_id,
                    text=text,
                )
                notification = Notification(
                    user_id=user_id,
                    type="new_message",
                    message=f"User {user.username} sent you a message",
                    is_read=False,
                )
                try:
                    db.add(message)
                    db.add(notification)
                    await db.commit()
                    await db.refresh(message)
                except Exception:
                    await db.rollback()
                    await websocket.close(code=1008)
                    return
                message_data = {
                    "type": "message",
                    "id": message.id,
                    "sender_id": message.sender_id,
                    "receiver_id": message.receiver_id,
                    "text": message.text,
                    "is_read": message.is_read,
                    "created_at": message.created_at.isoformat(),
                }

                await manager.send_personal_message(
                    user_id=user_id,
                    data=message_data,
                )
                await manager.send_personal_message(
                    user_id=my_id,
                    data=message_data,
                )
            elif event_type == "message_read":
                message_id = data.get("message_id")
                if type(message_id) is not int or message_id <= 0:
                    await websocket.close(code=1008)
                    return
                message = await db.get(Message, message_id)
                if (
                        message is None
                        or message.receiver_id != my_id
                        or message.sender_id != user_id
                ):
                    await websocket.close(code=1008)
                    return
                try:
                    message.is_read = True
                    await db.commit()
                except Exception:
                    await db.rollback()
                    await websocket.close(code=1008)
                    return
                await manager.send_personal_message(
                    user_id=message.sender_id,
                    data={
                        "type": "message_read",
                        "message_id": message.id,
                    },
                )
            else:
                await websocket.close(code=1008)
                return
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket, my_id)
