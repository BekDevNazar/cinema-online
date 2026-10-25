from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from database import get_db
from dependencies import get_current_user
from models.favorite import Favorite
from models.follow import Follow
from models.message import Message
from models.movie import Movie
from models.notification import Notification
from models.review import Review
from models.user import User
from schemas.message import MessageResponse, MessageCreate, ChatResponse
from schemas.movie import ResponseMovieScheme
from schemas.notification import NotificationResponseSchema
from schemas.user import PublicUserProfileResponse, PublicUserResponse

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.get(
    "/me/favorites/",
    response_model=list[ResponseMovieScheme],
)
async def get_user_favorite(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Movie)
        .join(
            Favorite,
            Favorite.movie_id == Movie.id,
        )
        .where(
            Favorite.user_id == current_user.id
        )
    )

    movies = result.scalars().all()

    return movies


@router.get(
    "/{user_id}/",
    response_model=PublicUserProfileResponse
)
async def search_user(
        user_id: int,
        db: AsyncSession = Depends(get_db)
):
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    result = await db.execute(
        select(Review, Movie).join(Movie, Review.movie_id == Movie.id)
        .where(Review.user_id == user_id)
        .order_by(Review.created_at.desc())
    )
    rows = result.all()

    reviews_data = []
    for review, movie in rows:
        reviews_data.append(
            {
                "id": review.id,
                "text": review.text,
                "rating": review.rating,
                "created_at": review.created_at,
                "movie": {
                    "id": movie.id,
                    "title": movie.title,
                    "poster_url": movie.poster_url
                }
            }
        )
    return {
        "id": user.id,
        "username": user.username,
        "created_at": user.created_at,
        "reviews": reviews_data
    }


@router.post(
    "/{user_id}/follow/",
    status_code=status.HTTP_201_CREATED
)
async def follow_user(
        user_id: int,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    following_user = await db.get(User, user_id)
    if following_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You can't follow yourself",
        )
    result = await db.execute(
        select(Follow).where(Follow.follower_id == current_user.id,
                             Follow.following_id == user_id)
    )
    is_follow = result.scalar_one_or_none()
    if is_follow is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already follow this user"
        )
    follow = Follow(
        follower_id=current_user.id,
        following_id=user_id,
    )

    notification = Notification(
        user_id=user_id,
        type="new_follower",
        message=f"User {current_user.id} started following you",
        is_read=False,
    )

    db.add(follow)
    db.add(notification)


    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already followed this user",
        )

    await db.refresh(follow)
    return follow


@router.delete(
    "/{user_id}/follow/",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_follow(
        user_id: int,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    user = await db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    result = await db.execute(
        select(Follow).where(Follow.follower_id == current_user.id,
                             Follow.following_id == user_id)
    )
    follow = result.scalar_one_or_none()
    if follow is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You are not follow at this user"
        )
    await db.delete(follow)
    await db.commit()


@router.get(
    "/{user_id}/followers/",
    response_model=list[PublicUserResponse]
)
async def search_followers(
        user_id: int,
        db: AsyncSession = Depends(get_db)
):
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not user"
        )
    result = await db.execute(
        select(User)
        .join(Follow, Follow.follower_id == User.id)
        .where(Follow.following_id == user_id)
    )
    user_followers = result.scalars().all()
    return user_followers


@router.get(
    "/{user_id}/following/",
    response_model=list[PublicUserResponse]
)
async def search_following(
        user_id: int,
        db: AsyncSession = Depends(get_db)
):
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not user"
        )
    result = await db.execute(
        select(User)
        .join(Follow, Follow.following_id == User.id)
        .where(Follow.follower_id == user_id)
    )
    user_following = result.scalars().all()
    return user_following


@router.post(
    "/{user_id}/messages/",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_messages(
        user_id: int,
        message_data: MessageCreate,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You can't send a message to yourself",
        )
    message = Message(
        sender_id=current_user.id,
        receiver_id=user_id,
        text=message_data.text,
    )
    notification = Notification(
        user_id=user_id,
        type="new_message",
        message=f"User {current_user.username} sent you a message",
        is_read=False,
    )
    db.add(notification)
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message


@router.get(
    "/{user_id}/messages/",
    response_model=list[MessageResponse]
)
async def check_all_messages(
        user_id: int,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    result = await db.execute(
        select(Message).where(
            or_(
                (Message.sender_id == current_user.id) & (Message.receiver_id == user_id),
                (Message.sender_id == user_id) & (Message.receiver_id == current_user.id)
            )
        ).order_by(Message.created_at)
    )
    messages = result.scalars().all()
    return messages


@router.get(
    "/me/conversations/",
    response_model=list[ChatResponse]
)
async def check_all_chat(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    result_1 = await db.execute(
        select(Message, User)
        .join(User, Message.receiver_id == User.id)
        .where(Message.sender_id == current_user.id)
    )
    result_2 = await db.execute(
        select(Message, User)
        .join(User, Message.sender_id == User.id)
        .where(Message.receiver_id == current_user.id)
    )
    sent_rows = result_1.all()
    received_rows = result_2.all()

    all_rows = sent_rows + received_rows
    all_rows.sort(
        key=lambda row: row[0].created_at,
        reverse=True
    )
    conversations = {}
    for message, user in all_rows:
        if user.id not in conversations:
            conversations[user.id] = {
                "user_id": user.id,
                "username": user.username,
                "last_message": message.text,
                "last_message_created_at": message.created_at,
            }
    return list(conversations.values())


@router.get(
    "/me/notifications/",
    response_model=list[NotificationResponseSchema]
)
async def get_my_notification(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Notification)
        .where(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
    )
    notification = result.scalars().all()
    return notification


@router.patch(
    "/me/notifications/{notification_id}/read/",
    response_model=NotificationResponseSchema
)
async def change_notification(
        notification_id: int,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    notification = await db.get(Notification, notification_id)
    if notification is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )
    if notification.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found"
        )

    notification.is_read = True
    await db.commit()
    await db.refresh(notification)
    return notification