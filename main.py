from fastapi import FastAPI

from database import lifespan
from routers.auth import router as auth_router
from routers.movies import router as movie_router
from routers.users import router as user_router
from routers.websocket import router as websocket_router
from models.base import Base

import models.user
import models.movie

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