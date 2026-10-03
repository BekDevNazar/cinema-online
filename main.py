from fastapi import FastAPI

from database import lifespan
from routers.auth import router as auth_router


app = FastAPI(
    title="Cinema Online API",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(auth_router)
