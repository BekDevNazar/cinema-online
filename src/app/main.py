from fastapi import FastAPI

from app.database import lifespan
from app.routers.auth import router as auth_router
from app.routers.movies import router as movie_router
from app.routers.users import router as user_router
from app.routers.websocket import router as websocket_router
from app.models.base import Base

import app.models.user
import app.models.movie

target_metadata = Base.metadata


app = FastAPI(
    title="Cinema Online API",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(auth_router)
app.include_router(movie_router)
app.include_router(user_router)
app.include_router(websocket_router)
